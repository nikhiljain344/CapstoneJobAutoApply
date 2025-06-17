from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.automation_tasks import apply_to_job, scrape_job_details
from src.models.user import User, UserProfile
from src.models.job import Job, JobApplication, ApplicationQueue
from datetime import datetime
import logging

queue_bp = Blueprint('queue', __name__)

@queue_bp.route('/add-to-queue', methods=['POST'])
@jwt_required()
def add_job_to_queue():
    """
    Add a job to the application queue
    
    Expected JSON:
    - job_url: URL of the job posting
    - job_id: Optional job ID (for tracked jobs)
    - priority: Optional priority (1-5, default: 3)
    - apply_immediately: Boolean to apply immediately or queue for later
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'job_url' not in data:
            return jsonify({
                'success': False,
                'error': 'job_url is required'
            }), 400
        
        job_url = data['job_url']
        job_id = data.get('job_id', f"external_{hash(job_url)}")
        priority = data.get('priority', 3)
        apply_immediately = data.get('apply_immediately', False)
        
        # Check if user has already applied to this job
        existing_application = JobApplication.query.filter_by(
            user_id=user_id,
            job_url=job_url
        ).first()
        
        if existing_application:
            return jsonify({
                'success': False,
                'error': 'You have already applied to this job'
            }), 400
        
        # Check if job is already in queue
        existing_queue_item = ApplicationQueue.query.filter_by(
            user_id=user_id,
            job_url=job_url,
            status='pending'
        ).first()
        
        if existing_queue_item:
            return jsonify({
                'success': False,
                'error': 'Job is already in your application queue'
            }), 400
        
        # Check user's daily application limit
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        daily_limit = 10  # Default limit
        
        if user_profile and hasattr(user_profile, 'daily_application_limit'):
            daily_limit = user_profile.daily_application_limit or 10
        
        # Count today's applications
        today = datetime.utcnow().date()
        today_applications = JobApplication.query.filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= today
        ).count()
        
        if today_applications >= daily_limit:
            return jsonify({
                'success': False,
                'error': f'Daily application limit of {daily_limit} reached'
            }), 400
        
        if apply_immediately:
            # Start application task immediately
            task = apply_to_job.delay(user_id, job_id, job_url)
            
            return jsonify({
                'success': True,
                'message': 'Application started immediately',
                'task_id': task.id,
                'status': 'processing'
            }), 200
        else:
            # Add to queue
            queue_item = ApplicationQueue(
                user_id=user_id,
                job_id=job_id,
                job_url=job_url,
                priority=priority,
                status='pending',
                created_at=datetime.utcnow()
            )
            
            from src.main import db
            db.session.add(queue_item)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Job added to application queue',
                'queue_item_id': queue_item.id,
                'position_in_queue': get_queue_position(user_id, queue_item.id)
            }), 200
        
    except Exception as e:
        logging.error(f"Error adding job to queue: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@queue_bp.route('/queue-status', methods=['GET'])
@jwt_required()
def get_queue_status():
    """Get user's application queue status"""
    try:
        user_id = get_jwt_identity()
        
        # Get pending queue items
        pending_items = ApplicationQueue.query.filter_by(
            user_id=user_id,
            status='pending'
        ).order_by(ApplicationQueue.priority.desc(), ApplicationQueue.created_at).all()
        
        # Get processing items
        processing_items = ApplicationQueue.query.filter_by(
            user_id=user_id,
            status='processing'
        ).all()
        
        # Get recent applications
        recent_applications = JobApplication.query.filter_by(
            user_id=user_id
        ).order_by(JobApplication.applied_at.desc()).limit(10).all()
        
        queue_data = []
        for item in pending_items:
            queue_data.append({
                'id': item.id,
                'job_id': item.job_id,
                'job_url': item.job_url,
                'priority': item.priority,
                'status': item.status,
                'created_at': item.created_at.isoformat(),
                'position': get_queue_position(user_id, item.id)
            })
        
        processing_data = []
        for item in processing_items:
            processing_data.append({
                'id': item.id,
                'job_id': item.job_id,
                'job_url': item.job_url,
                'status': item.status,
                'started_at': item.started_at.isoformat() if item.started_at else None
            })
        
        applications_data = []
        for app in recent_applications:
            applications_data.append({
                'id': app.id,
                'job_id': app.job_id,
                'job_url': app.job_url,
                'status': app.status,
                'applied_at': app.applied_at.isoformat(),
                'application_method': app.application_method,
                'notes': app.notes
            })
        
        return jsonify({
            'success': True,
            'queue': {
                'pending': queue_data,
                'processing': processing_data,
                'total_pending': len(pending_items),
                'total_processing': len(processing_items)
            },
            'recent_applications': applications_data,
            'daily_stats': get_daily_application_stats(user_id)
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting queue status: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@queue_bp.route('/remove-from-queue/<int:queue_item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_queue(queue_item_id):
    """Remove a job from the application queue"""
    try:
        user_id = get_jwt_identity()
        
        queue_item = ApplicationQueue.query.filter_by(
            id=queue_item_id,
            user_id=user_id
        ).first()
        
        if not queue_item:
            return jsonify({
                'success': False,
                'error': 'Queue item not found'
            }), 404
        
        if queue_item.status == 'processing':
            return jsonify({
                'success': False,
                'error': 'Cannot remove job that is currently being processed'
            }), 400
        
        from src.main import db
        db.session.delete(queue_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job removed from queue'
        }), 200
        
    except Exception as e:
        logging.error(f"Error removing from queue: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@queue_bp.route('/task-status/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    """Get status of a specific application task"""
    try:
        from src.services.celery_config import celery_app
        
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': 'Task is waiting to be processed'
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'status': task.info.get('status', ''),
                'progress': task.info.get('progress', 0)
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'status': task.info.get('status', 'Task completed successfully'),
                'result': task.info
            }
        else:  # FAILURE
            response = {
                'state': task.state,
                'status': task.info.get('status', 'Task failed'),
                'error': task.info.get('error', str(task.info))
            }
        
        return jsonify({
            'success': True,
            'task_status': response
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting task status: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@queue_bp.route('/bulk-apply', methods=['POST'])
@jwt_required()
def bulk_apply_jobs():
    """
    Add multiple jobs to the application queue
    
    Expected JSON:
    - job_urls: List of job URLs
    - priority: Optional priority for all jobs
    - stagger_applications: Boolean to stagger applications over time
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'job_urls' not in data:
            return jsonify({
                'success': False,
                'error': 'job_urls list is required'
            }), 400
        
        job_urls = data['job_urls']
        priority = data.get('priority', 3)
        stagger_applications = data.get('stagger_applications', True)
        
        if not isinstance(job_urls, list) or len(job_urls) == 0:
            return jsonify({
                'success': False,
                'error': 'job_urls must be a non-empty list'
            }), 400
        
        if len(job_urls) > 50:
            return jsonify({
                'success': False,
                'error': 'Maximum 50 jobs can be added at once'
            }), 400
        
        # Check daily limit
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        daily_limit = user_profile.daily_application_limit if user_profile else 10
        
        today = datetime.utcnow().date()
        today_applications = JobApplication.query.filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= today
        ).count()
        
        remaining_limit = daily_limit - today_applications
        
        if len(job_urls) > remaining_limit:
            return jsonify({
                'success': False,
                'error': f'Adding {len(job_urls)} jobs would exceed daily limit. Remaining: {remaining_limit}'
            }), 400
        
        added_jobs = []
        skipped_jobs = []
        
        from src.main import db
        
        for i, job_url in enumerate(job_urls):
            job_id = f"bulk_{hash(job_url)}"
            
            # Check if already applied or queued
            existing_application = JobApplication.query.filter_by(
                user_id=user_id,
                job_url=job_url
            ).first()
            
            existing_queue_item = ApplicationQueue.query.filter_by(
                user_id=user_id,
                job_url=job_url,
                status='pending'
            ).first()
            
            if existing_application or existing_queue_item:
                skipped_jobs.append({
                    'job_url': job_url,
                    'reason': 'Already applied or queued'
                })
                continue
            
            # Calculate delay for staggered applications
            delay_minutes = i * 5 if stagger_applications else 0
            
            queue_item = ApplicationQueue(
                user_id=user_id,
                job_id=job_id,
                job_url=job_url,
                priority=priority,
                status='pending',
                created_at=datetime.utcnow(),
                scheduled_for=datetime.utcnow() if delay_minutes == 0 else None
            )
            
            db.session.add(queue_item)
            added_jobs.append({
                'job_url': job_url,
                'queue_item_id': queue_item.id,
                'delay_minutes': delay_minutes
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Added {len(added_jobs)} jobs to queue',
            'added_jobs': added_jobs,
            'skipped_jobs': skipped_jobs,
            'total_added': len(added_jobs),
            'total_skipped': len(skipped_jobs)
        }), 200
        
    except Exception as e:
        logging.error(f"Error in bulk apply: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@queue_bp.route('/application-stats', methods=['GET'])
@jwt_required()
def get_application_stats():
    """Get detailed application statistics for the user"""
    try:
        user_id = get_jwt_identity()
        
        # Get all applications
        all_applications = JobApplication.query.filter_by(user_id=user_id).all()
        
        # Calculate statistics
        total_applications = len(all_applications)
        successful_applications = len([app for app in all_applications if app.status == 'submitted'])
        failed_applications = len([app for app in all_applications if app.status == 'failed'])
        pending_applications = len([app for app in all_applications if app.status == 'pending'])
        
        # Success rate
        success_rate = (successful_applications / total_applications * 100) if total_applications > 0 else 0
        
        # Applications by date (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_applications = [app for app in all_applications if app.applied_at >= thirty_days_ago]
        
        # Group by date
        applications_by_date = {}
        for app in recent_applications:
            date_key = app.applied_at.date().isoformat()
            if date_key not in applications_by_date:
                applications_by_date[date_key] = {'total': 0, 'successful': 0, 'failed': 0}
            
            applications_by_date[date_key]['total'] += 1
            if app.status == 'submitted':
                applications_by_date[date_key]['successful'] += 1
            elif app.status == 'failed':
                applications_by_date[date_key]['failed'] += 1
        
        # Queue statistics
        pending_queue = ApplicationQueue.query.filter_by(user_id=user_id, status='pending').count()
        processing_queue = ApplicationQueue.query.filter_by(user_id=user_id, status='processing').count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_applications': total_applications,
                'successful_applications': successful_applications,
                'failed_applications': failed_applications,
                'pending_applications': pending_applications,
                'success_rate': round(success_rate, 2),
                'queue_stats': {
                    'pending': pending_queue,
                    'processing': processing_queue
                },
                'applications_by_date': applications_by_date,
                'recent_activity': {
                    'last_30_days': len(recent_applications),
                    'this_week': len([app for app in recent_applications 
                                    if app.applied_at >= datetime.utcnow() - timedelta(days=7)]),
                    'today': len([app for app in recent_applications 
                                if app.applied_at.date() == datetime.utcnow().date()])
                }
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting application stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

def get_queue_position(user_id: int, queue_item_id: int) -> int:
    """Get position of a queue item in the user's queue"""
    try:
        queue_items = ApplicationQueue.query.filter_by(
            user_id=user_id,
            status='pending'
        ).order_by(ApplicationQueue.priority.desc(), ApplicationQueue.created_at).all()
        
        for i, item in enumerate(queue_items):
            if item.id == queue_item_id:
                return i + 1
        
        return -1
    except:
        return -1

def get_daily_application_stats(user_id: int) -> dict:
    """Get daily application statistics"""
    try:
        today = datetime.utcnow().date()
        
        today_applications = JobApplication.query.filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= today
        ).count()
        
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        daily_limit = user_profile.daily_application_limit if user_profile else 10
        
        return {
            'applications_today': today_applications,
            'daily_limit': daily_limit,
            'remaining': max(0, daily_limit - today_applications),
            'percentage_used': round((today_applications / daily_limit * 100), 2) if daily_limit > 0 else 0
        }
    except:
        return {
            'applications_today': 0,
            'daily_limit': 10,
            'remaining': 10,
            'percentage_used': 0
        }

