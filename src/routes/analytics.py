from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, UserProfile
from src.models.job import Job, JobApplication, ApplicationQueue
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import logging

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard-stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get comprehensive dashboard statistics for the user"""
    try:
        user_id = get_jwt_identity()
        
        # Time periods
        today = datetime.utcnow().date()
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        # Basic application stats
        total_applications = JobApplication.query.filter_by(user_id=user_id).count()
        successful_applications = JobApplication.query.filter_by(
            user_id=user_id, status='submitted'
        ).count()
        failed_applications = JobApplication.query.filter_by(
            user_id=user_id, status='failed'
        ).count()
        
        # Time-based stats
        applications_today = JobApplication.query.filter(
            JobApplication.user_id == user_id,
            func.date(JobApplication.applied_at) == today
        ).count()
        
        applications_this_week = JobApplication.query.filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= week_ago
        ).count()
        
        applications_this_month = JobApplication.query.filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= month_ago
        ).count()
        
        # Queue stats
        pending_queue = ApplicationQueue.query.filter_by(
            user_id=user_id, status='pending'
        ).count()
        processing_queue = ApplicationQueue.query.filter_by(
            user_id=user_id, status='processing'
        ).count()
        
        # Success rate
        success_rate = (successful_applications / total_applications * 100) if total_applications > 0 else 0
        
        # Average applications per day (last 30 days)
        avg_applications_per_day = applications_this_month / 30 if applications_this_month > 0 else 0
        
        # User profile completion
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        profile_completion = calculate_profile_completion(user_id, user_profile)
        
        # Recent activity
        recent_applications = JobApplication.query.filter_by(
            user_id=user_id
        ).order_by(JobApplication.applied_at.desc()).limit(5).all()
        
        recent_activity = []
        for app in recent_applications:
            recent_activity.append({
                'id': app.id,
                'job_url': app.job_url,
                'status': app.status,
                'applied_at': app.applied_at.isoformat(),
                'application_method': app.application_method
            })
        
        return jsonify({
            'success': True,
            'stats': {
                'overview': {
                    'total_applications': total_applications,
                    'successful_applications': successful_applications,
                    'failed_applications': failed_applications,
                    'success_rate': round(success_rate, 2),
                    'profile_completion': profile_completion
                },
                'time_based': {
                    'applications_today': applications_today,
                    'applications_this_week': applications_this_week,
                    'applications_this_month': applications_this_month,
                    'avg_per_day': round(avg_applications_per_day, 2)
                },
                'queue': {
                    'pending': pending_queue,
                    'processing': processing_queue,
                    'total_queued': pending_queue + processing_queue
                },
                'recent_activity': recent_activity
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@analytics_bp.route('/application-trends', methods=['GET'])
@jwt_required()
def get_application_trends():
    """Get application trends over time"""
    try:
        user_id = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        
        # Limit to reasonable range
        days = min(max(days, 7), 365)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get applications grouped by date
        applications = JobApplication.query.filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= start_date
        ).all()
        
        # Group by date
        trends = {}
        for app in applications:
            date_key = app.applied_at.date().isoformat()
            if date_key not in trends:
                trends[date_key] = {
                    'date': date_key,
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'pending': 0
                }
            
            trends[date_key]['total'] += 1
            if app.status == 'submitted':
                trends[date_key]['successful'] += 1
            elif app.status == 'failed':
                trends[date_key]['failed'] += 1
            else:
                trends[date_key]['pending'] += 1
        
        # Fill in missing dates with zeros
        current_date = start_date.date()
        end_date = datetime.utcnow().date()
        
        while current_date <= end_date:
            date_key = current_date.isoformat()
            if date_key not in trends:
                trends[date_key] = {
                    'date': date_key,
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'pending': 0
                }
            current_date += timedelta(days=1)
        
        # Sort by date
        trend_data = sorted(trends.values(), key=lambda x: x['date'])
        
        return jsonify({
            'success': True,
            'trends': trend_data,
            'period_days': days,
            'total_data_points': len(trend_data)
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting application trends: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@analytics_bp.route('/success-metrics', methods=['GET'])
@jwt_required()
def get_success_metrics():
    """Get detailed success metrics and insights"""
    try:
        user_id = get_jwt_identity()
        
        # Get all applications
        applications = JobApplication.query.filter_by(user_id=user_id).all()
        
        if not applications:
            return jsonify({
                'success': True,
                'metrics': {
                    'overall_success_rate': 0,
                    'response_rate': 0,
                    'application_methods': {},
                    'time_to_response': {},
                    'best_performing_days': {},
                    'insights': []
                }
            }), 200
        
        # Calculate metrics
        total_apps = len(applications)
        successful_apps = len([app for app in applications if app.status == 'submitted'])
        failed_apps = len([app for app in applications if app.status == 'failed'])
        
        # Success rate by application method
        method_stats = {}
        for app in applications:
            method = app.application_method or 'unknown'
            if method not in method_stats:
                method_stats[method] = {'total': 0, 'successful': 0}
            
            method_stats[method]['total'] += 1
            if app.status == 'submitted':
                method_stats[method]['successful'] += 1
        
        # Calculate success rates
        for method in method_stats:
            total = method_stats[method]['total']
            successful = method_stats[method]['successful']
            method_stats[method]['success_rate'] = (successful / total * 100) if total > 0 else 0
        
        # Best performing days of the week
        day_stats = {}
        for app in applications:
            day_name = app.applied_at.strftime('%A')
            if day_name not in day_stats:
                day_stats[day_name] = {'total': 0, 'successful': 0}
            
            day_stats[day_name]['total'] += 1
            if app.status == 'submitted':
                day_stats[day_name]['successful'] += 1
        
        # Calculate success rates for days
        for day in day_stats:
            total = day_stats[day]['total']
            successful = day_stats[day]['successful']
            day_stats[day]['success_rate'] = (successful / total * 100) if total > 0 else 0
        
        # Generate insights
        insights = generate_insights(applications, method_stats, day_stats)
        
        return jsonify({
            'success': True,
            'metrics': {
                'overall_success_rate': round((successful_apps / total_apps * 100), 2),
                'total_applications': total_apps,
                'successful_applications': successful_apps,
                'failed_applications': failed_apps,
                'application_methods': method_stats,
                'best_performing_days': day_stats,
                'insights': insights
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting success metrics: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@analytics_bp.route('/performance-insights', methods=['GET'])
@jwt_required()
def get_performance_insights():
    """Get AI-powered performance insights and recommendations"""
    try:
        user_id = get_jwt_identity()
        
        # Get user data
        applications = JobApplication.query.filter_by(user_id=user_id).all()
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        # Generate comprehensive insights
        insights = {
            'application_patterns': analyze_application_patterns(applications),
            'optimization_suggestions': generate_optimization_suggestions(applications, user_profile),
            'skill_recommendations': generate_skill_recommendations(user_profile),
            'market_insights': generate_market_insights(applications),
            'goal_tracking': calculate_goal_progress(user_id, applications)
        }
        
        return jsonify({
            'success': True,
            'insights': insights
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting performance insights: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@analytics_bp.route('/export-data', methods=['GET'])
@jwt_required()
def export_user_data():
    """Export user's application data"""
    try:
        user_id = get_jwt_identity()
        format_type = request.args.get('format', 'json')
        
        # Get all user data
        user = User.query.get(user_id)
        applications = JobApplication.query.filter_by(user_id=user_id).all()
        queue_items = ApplicationQueue.query.filter_by(user_id=user_id).all()
        
        export_data = {
            'user_info': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'created_at': user.created_at.isoformat() if user.created_at else None
            },
            'applications': [],
            'queue_items': []
        }
        
        # Add applications
        for app in applications:
            export_data['applications'].append({
                'id': app.id,
                'job_id': app.job_id,
                'job_url': app.job_url,
                'status': app.status,
                'applied_at': app.applied_at.isoformat(),
                'application_method': app.application_method,
                'notes': app.notes
            })
        
        # Add queue items
        for item in queue_items:
            export_data['queue_items'].append({
                'id': item.id,
                'job_id': item.job_id,
                'job_url': item.job_url,
                'status': item.status,
                'priority': item.priority,
                'created_at': item.created_at.isoformat()
            })
        
        export_data['export_timestamp'] = datetime.utcnow().isoformat()
        export_data['total_applications'] = len(applications)
        export_data['total_queue_items'] = len(queue_items)
        
        return jsonify({
            'success': True,
            'data': export_data,
            'format': format_type
        }), 200
        
    except Exception as e:
        logging.error(f"Error exporting data: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# Helper functions
def calculate_profile_completion(user_id: int, user_profile: UserProfile) -> int:
    """Calculate user profile completion percentage"""
    try:
        user = User.query.get(user_id)
        if not user:
            return 0
        
        completion_score = 0
        total_fields = 10
        
        # Basic user info (4 fields)
        if user.name:
            completion_score += 1
        if user.email:
            completion_score += 1
        if user.phone:
            completion_score += 1
        if user.address:
            completion_score += 1
        
        if user_profile:
            # Profile fields (6 fields)
            if user_profile.skills:
                completion_score += 1
            if user_profile.summary:
                completion_score += 1
            if user_profile.total_experience and user_profile.total_experience > 0:
                completion_score += 1
            if user_profile.experience_level:
                completion_score += 1
            if user_profile.resume_filename:
                completion_score += 1
            if user_profile.salary_preferences:
                completion_score += 1
        
        return int((completion_score / total_fields) * 100)
        
    except Exception:
        return 0

def generate_insights(applications, method_stats, day_stats):
    """Generate actionable insights from application data"""
    insights = []
    
    try:
        # Method performance insights
        if method_stats:
            best_method = max(method_stats.items(), key=lambda x: x[1]['success_rate'])
            if best_method[1]['success_rate'] > 0:
                insights.append({
                    'type': 'success',
                    'title': 'Best Application Method',
                    'message': f"Your {best_method[0]} applications have a {best_method[1]['success_rate']:.1f}% success rate",
                    'action': f"Focus more on {best_method[0]} applications"
                })
        
        # Day performance insights
        if day_stats:
            best_day = max(day_stats.items(), key=lambda x: x[1]['success_rate'])
            if best_day[1]['success_rate'] > 0:
                insights.append({
                    'type': 'info',
                    'title': 'Best Day to Apply',
                    'message': f"You have the highest success rate on {best_day[0]}s ({best_day[1]['success_rate']:.1f}%)",
                    'action': f"Schedule more applications for {best_day[0]}s"
                })
        
        # Volume insights
        total_apps = len(applications)
        if total_apps < 10:
            insights.append({
                'type': 'warning',
                'title': 'Low Application Volume',
                'message': f"You've only submitted {total_apps} applications",
                'action': "Consider increasing your daily application target"
            })
        elif total_apps > 100:
            insights.append({
                'type': 'success',
                'title': 'High Application Volume',
                'message': f"Great job! You've submitted {total_apps} applications",
                'action': "Focus on quality and targeting for better results"
            })
        
        # Recent activity insights
        recent_apps = [app for app in applications if app.applied_at >= datetime.utcnow() - timedelta(days=7)]
        if len(recent_apps) == 0:
            insights.append({
                'type': 'warning',
                'title': 'No Recent Activity',
                'message': "You haven't applied to any jobs in the past week",
                'action': "Resume your job search to maintain momentum"
            })
        
    except Exception as e:
        logging.error(f"Error generating insights: {e}")
    
    return insights

def analyze_application_patterns(applications):
    """Analyze patterns in application behavior"""
    if not applications:
        return {}
    
    # Time patterns
    hour_distribution = {}
    day_distribution = {}
    
    for app in applications:
        hour = app.applied_at.hour
        day = app.applied_at.strftime('%A')
        
        hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
        day_distribution[day] = day_distribution.get(day, 0) + 1
    
    # Find peak hours and days
    peak_hour = max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else None
    peak_day = max(day_distribution.items(), key=lambda x: x[1])[0] if day_distribution else None
    
    return {
        'peak_application_hour': peak_hour,
        'peak_application_day': peak_day,
        'hour_distribution': hour_distribution,
        'day_distribution': day_distribution,
        'total_applications': len(applications),
        'average_per_day': len(applications) / max(1, (datetime.utcnow() - min(app.applied_at for app in applications)).days)
    }

def generate_optimization_suggestions(applications, user_profile):
    """Generate optimization suggestions based on user data"""
    suggestions = []
    
    if not applications:
        suggestions.append({
            'category': 'getting_started',
            'title': 'Start Your Job Search',
            'description': 'Begin applying to jobs to get personalized insights',
            'priority': 'high'
        })
        return suggestions
    
    # Success rate analysis
    success_rate = len([app for app in applications if app.status == 'submitted']) / len(applications) * 100
    
    if success_rate < 20:
        suggestions.append({
            'category': 'success_rate',
            'title': 'Improve Application Success Rate',
            'description': 'Your current success rate is low. Consider improving your resume and targeting more relevant positions.',
            'priority': 'high'
        })
    
    # Profile completion
    if not user_profile or not user_profile.skills:
        suggestions.append({
            'category': 'profile',
            'title': 'Complete Your Skills Profile',
            'description': 'Add your skills to get better job matches and improve application success.',
            'priority': 'medium'
        })
    
    # Application frequency
    recent_apps = [app for app in applications if app.applied_at >= datetime.utcnow() - timedelta(days=7)]
    if len(recent_apps) < 5:
        suggestions.append({
            'category': 'frequency',
            'title': 'Increase Application Frequency',
            'description': 'Apply to more jobs per week to increase your chances of success.',
            'priority': 'medium'
        })
    
    return suggestions

def generate_skill_recommendations(user_profile):
    """Generate skill recommendations based on market trends"""
    recommendations = []
    
    # Popular skills in tech (this would come from job market analysis in production)
    trending_skills = [
        'Python', 'JavaScript', 'React', 'AWS', 'Docker', 'Kubernetes',
        'Machine Learning', 'Data Analysis', 'SQL', 'Git', 'Agile'
    ]
    
    user_skills = []
    if user_profile and user_profile.skills:
        try:
            import json
            user_skills = json.loads(user_profile.skills) if isinstance(user_profile.skills, str) else user_profile.skills
        except:
            user_skills = []
    
    # Recommend skills not in user's profile
    missing_skills = [skill for skill in trending_skills if skill.lower() not in [s.lower() for s in user_skills]]
    
    for skill in missing_skills[:5]:  # Top 5 recommendations
        recommendations.append({
            'skill': skill,
            'reason': 'High demand in current job market',
            'priority': 'medium'
        })
    
    return recommendations

def generate_market_insights(applications):
    """Generate market insights based on application data"""
    insights = {
        'total_applications': len(applications),
        'success_rate': 0,
        'market_trends': [],
        'recommendations': []
    }
    
    if applications:
        successful = len([app for app in applications if app.status == 'submitted'])
        insights['success_rate'] = (successful / len(applications)) * 100
        
        # Add market trend insights (would be enhanced with real market data)
        insights['market_trends'] = [
            'Remote work opportunities are increasing',
            'Tech skills are in high demand',
            'Companies are hiring more actively in Q1'
        ]
        
        insights['recommendations'] = [
            'Focus on companies with remote-friendly policies',
            'Highlight technical skills in your applications',
            'Apply early in the week for better response rates'
        ]
    
    return insights

def calculate_goal_progress(user_id, applications):
    """Calculate progress towards user's goals"""
    # Default goals (would be customizable by user)
    monthly_goal = 50
    weekly_goal = 12
    
    # Calculate current progress
    this_month = datetime.utcnow().replace(day=1)
    this_week = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    
    monthly_progress = len([app for app in applications if app.applied_at >= this_month])
    weekly_progress = len([app for app in applications if app.applied_at >= this_week])
    
    return {
        'monthly': {
            'goal': monthly_goal,
            'progress': monthly_progress,
            'percentage': (monthly_progress / monthly_goal * 100) if monthly_goal > 0 else 0
        },
        'weekly': {
            'goal': weekly_goal,
            'progress': weekly_progress,
            'percentage': (weekly_progress / weekly_goal * 100) if weekly_goal > 0 else 0
        }
    }

