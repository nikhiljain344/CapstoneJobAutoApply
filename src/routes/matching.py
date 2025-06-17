from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.job_matching import JobMatchingEngine
from src.models.user import User, UserProfile, Education, WorkExperience
from src.models.job import Job, JobApplication
import logging
from datetime import datetime

matching_bp = Blueprint('matching', __name__)

@matching_bp.route('/find-matches', methods=['POST'])
@jwt_required()
def find_job_matches():
    """
    Find job matches for the current user
    
    Expected JSON (optional):
    - limit: Number of matches to return (default: 20)
    - weights: Custom weights for matching factors
    - filters: Additional filters (salary_min, location_radius, etc.)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Get user profile
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not user_profile:
            return jsonify({
                'success': False,
                'error': 'User profile not found. Please complete your profile first.'
            }), 400
        
        # Build user profile for matching
        profile_data = build_user_profile_for_matching(user, user_profile)
        
        # Get available jobs (mock data for now - in production this would come from job board APIs)
        jobs = get_mock_jobs()
        
        # Apply filters if provided
        filters = data.get('filters', {})
        if filters:
            jobs = apply_job_filters(jobs, filters)
        
        # Initialize matching engine
        matching_engine = JobMatchingEngine()
        
        # Get custom weights if provided
        weights = data.get('weights')
        limit = data.get('limit', 20)
        
        # Find matches
        if weights:
            matches = []
            for job in jobs:
                match_result = matching_engine.calculate_overall_match_score(
                    profile_data, job, weights
                )
                job_with_score = job.copy()
                job_with_score['match_score'] = match_result['overall_score']
                job_with_score['match_breakdown'] = match_result['breakdown']
                job_with_score['match_quality'] = match_result['match_quality']
                matches.append(job_with_score)
            
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            matches = matches[:limit]
        else:
            matches = matching_engine.find_best_matches(profile_data, jobs, limit)
        
        return jsonify({
            'success': True,
            'matches': matches,
            'total_jobs_analyzed': len(jobs),
            'user_profile_summary': {
                'skills_count': len(profile_data.get('skills', [])),
                'experience_years': profile_data.get('experience', {}).get('years', 0),
                'experience_level': profile_data.get('experience', {}).get('level', 'entry')
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error finding job matches: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@matching_bp.route('/explain-match', methods=['POST'])
@jwt_required()
def explain_job_match():
    """
    Get detailed explanation of why a specific job matches or doesn't match
    
    Expected JSON:
    - job_id: ID of the job to explain
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'job_id' not in data:
            return jsonify({
                'success': False,
                'error': 'job_id is required'
            }), 400
        
        job_id = data['job_id']
        
        # Get user profile
        user = User.query.get(user_id)
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not user or not user_profile:
            return jsonify({
                'success': False,
                'error': 'User profile not found'
            }), 404
        
        # Build user profile for matching
        profile_data = build_user_profile_for_matching(user, user_profile)
        
        # Get the specific job (mock data for now)
        jobs = get_mock_jobs()
        job = next((j for j in jobs if j['id'] == job_id), None)
        
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        # Get explanation
        matching_engine = JobMatchingEngine()
        explanation = matching_engine.explain_match(profile_data, job)
        
        # Add match score
        match_result = matching_engine.calculate_overall_match_score(profile_data, job)
        explanation['match_score'] = match_result['overall_score']
        explanation['match_breakdown'] = match_result['breakdown']
        
        return jsonify({
            'success': True,
            'explanation': explanation,
            'job': job
        }), 200
        
    except Exception as e:
        logging.error(f"Error explaining job match: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@matching_bp.route('/update-preferences', methods=['POST'])
@jwt_required()
def update_matching_preferences():
    """
    Update user's job matching preferences
    
    Expected JSON:
    - salary_preferences: {min_salary: int, max_salary: int}
    - location_preferences: {remote_ok: bool, hybrid_ok: bool, max_commute_miles: int}
    - company_preferences: {preferred_companies: List[str], company_size: str, industry: str}
    - job_type_preferences: {full_time: bool, part_time: bool, contract: bool, internship: bool}
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Preferences data is required'
            }), 400
        
        # Get or create user profile
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not user_profile:
            user_profile = UserProfile(user_id=user_id)
            from src.main import db
            db.session.add(user_profile)
        
        # Update preferences
        if 'salary_preferences' in data:
            user_profile.salary_preferences = data['salary_preferences']
        
        if 'location_preferences' in data:
            user_profile.location_preferences = data['location_preferences']
        
        if 'company_preferences' in data:
            user_profile.company_preferences = data['company_preferences']
        
        if 'job_type_preferences' in data:
            user_profile.job_type_preferences = data['job_type_preferences']
        
        from src.main import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated successfully'
        }), 200
        
    except Exception as e:
        logging.error(f"Error updating preferences: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@matching_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_matching_preferences():
    """Get user's current job matching preferences"""
    try:
        user_id = get_jwt_identity()
        
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not user_profile:
            # Return default preferences
            return jsonify({
                'success': True,
                'preferences': {
                    'salary_preferences': {'min_salary': 0, 'max_salary': 1000000},
                    'location_preferences': {'remote_ok': True, 'hybrid_ok': True, 'max_commute_miles': 30},
                    'company_preferences': {'preferred_companies': [], 'company_size': '', 'industry': ''},
                    'job_type_preferences': {'full_time': True, 'part_time': False, 'contract': False, 'internship': False}
                }
            }), 200
        
        return jsonify({
            'success': True,
            'preferences': {
                'salary_preferences': user_profile.salary_preferences or {'min_salary': 0, 'max_salary': 1000000},
                'location_preferences': user_profile.location_preferences or {'remote_ok': True, 'hybrid_ok': True, 'max_commute_miles': 30},
                'company_preferences': user_profile.company_preferences or {'preferred_companies': [], 'company_size': '', 'industry': ''},
                'job_type_preferences': user_profile.job_type_preferences or {'full_time': True, 'part_time': False, 'contract': False, 'internship': False}
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting preferences: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

def build_user_profile_for_matching(user: User, user_profile: UserProfile) -> dict:
    """Build user profile data structure for job matching"""
    
    # Get user's education
    education = Education.query.filter_by(user_id=user.id).all()
    
    # Get user's work experience
    work_experience = WorkExperience.query.filter_by(user_id=user.id).all()
    
    # Build experience data
    experience_data = {
        'years': user_profile.total_experience_years or 0,
        'level': user_profile.experience_level or 'entry',
        'titles': [exp.job_title for exp in work_experience if exp.job_title]
    }
    
    # Build location data
    location_data = {
        'zip_code': user.zip_code,
        'remote_ok': user_profile.location_preferences.get('remote_ok', True) if user_profile.location_preferences else True,
        'hybrid_ok': user_profile.location_preferences.get('hybrid_ok', True) if user_profile.location_preferences else True,
        'max_commute_miles': user_profile.location_preferences.get('max_commute_miles', 30) if user_profile.location_preferences else 30
    }
    
    # Add coordinates if available (would need geocoding service in production)
    if user.zip_code:
        # Mock coordinates for common ZIP codes (in production, use geocoding API)
        mock_coordinates = get_mock_coordinates(user.zip_code)
        if mock_coordinates:
            location_data.update(mock_coordinates)
    
    return {
        'skills': user_profile.skills or [],
        'experience': experience_data,
        'location': location_data,
        'salary_preferences': user_profile.salary_preferences or {'min_salary': 0, 'max_salary': 1000000},
        'company_preferences': user_profile.company_preferences or {},
        'job_type_preferences': user_profile.job_type_preferences or {'full_time': True}
    }

def get_mock_coordinates(zip_code: str) -> dict:
    """Get mock coordinates for ZIP codes (in production, use geocoding API)"""
    mock_coords = {
        '10001': {'lat': 40.7505, 'lng': -73.9934},  # NYC
        '90210': {'lat': 34.0901, 'lng': -118.4065},  # Beverly Hills
        '94102': {'lat': 37.7849, 'lng': -122.4094},  # San Francisco
        '02101': {'lat': 42.3584, 'lng': -71.0598},   # Boston
        '60601': {'lat': 41.8781, 'lng': -87.6298},   # Chicago
        '98101': {'lat': 47.6062, 'lng': -122.3321},  # Seattle
        '78701': {'lat': 30.2672, 'lng': -97.7431},   # Austin
        '30301': {'lat': 33.7490, 'lng': -84.3880},   # Atlanta
    }
    return mock_coords.get(zip_code[:5])

def apply_job_filters(jobs: list, filters: dict) -> list:
    """Apply additional filters to job list"""
    filtered_jobs = jobs.copy()
    
    # Salary filter
    if 'salary_min' in filters:
        min_salary = filters['salary_min']
        filtered_jobs = [job for job in filtered_jobs 
                        if job.get('salary', {}).get('max', 0) >= min_salary]
    
    # Location filter
    if 'location_radius' in filters and 'user_location' in filters:
        # Would implement geospatial filtering here
        pass
    
    # Remote work filter
    if filters.get('remote_only'):
        filtered_jobs = [job for job in filtered_jobs 
                        if job.get('location', {}).get('remote', False)]
    
    # Company size filter
    if 'company_size' in filters:
        company_size = filters['company_size']
        filtered_jobs = [job for job in filtered_jobs 
                        if job.get('company', {}).get('size', '') == company_size]
    
    return filtered_jobs

def get_mock_jobs() -> list:
    """Generate mock job data for testing (in production, this would come from job board APIs)"""
    return [
        {
            'id': 'job_1',
            'title': 'Senior Software Engineer',
            'company': {
                'name': 'TechCorp Inc',
                'size': 'large',
                'industry': 'technology',
                'rating': 4.5
            },
            'location': {
                'city': 'San Francisco',
                'state': 'CA',
                'zip_code': '94102',
                'lat': 37.7849,
                'lng': -122.4094,
                'remote': False,
                'hybrid': True
            },
            'salary': {
                'min': 120000,
                'max': 180000,
                'currency': 'USD'
            },
            'required_skills': ['python', 'javascript', 'react', 'aws', 'docker'],
            'experience_requirements': {
                'min_years': 5,
                'max_years': 10,
                'level': 'senior',
                'title': 'software engineer'
            },
            'description': 'We are looking for a senior software engineer to join our team...',
            'posted_date': '2024-01-15',
            'job_type': 'full_time'
        },
        {
            'id': 'job_2',
            'title': 'Frontend Developer',
            'company': {
                'name': 'StartupXYZ',
                'size': 'small',
                'industry': 'fintech',
                'rating': 4.2
            },
            'location': {
                'city': 'Remote',
                'state': '',
                'zip_code': '',
                'remote': True,
                'hybrid': False
            },
            'salary': {
                'min': 80000,
                'max': 120000,
                'currency': 'USD'
            },
            'required_skills': ['javascript', 'react', 'typescript', 'css', 'html'],
            'experience_requirements': {
                'min_years': 2,
                'max_years': 5,
                'level': 'mid',
                'title': 'frontend developer'
            },
            'description': 'Join our remote team as a frontend developer...',
            'posted_date': '2024-01-14',
            'job_type': 'full_time'
        },
        {
            'id': 'job_3',
            'title': 'Data Scientist',
            'company': {
                'name': 'DataCorp',
                'size': 'medium',
                'industry': 'data analytics',
                'rating': 4.0
            },
            'location': {
                'city': 'New York',
                'state': 'NY',
                'zip_code': '10001',
                'lat': 40.7505,
                'lng': -73.9934,
                'remote': False,
                'hybrid': True
            },
            'salary': {
                'min': 100000,
                'max': 150000,
                'currency': 'USD'
            },
            'required_skills': ['python', 'machine learning', 'sql', 'pandas', 'tensorflow'],
            'experience_requirements': {
                'min_years': 3,
                'max_years': 7,
                'level': 'mid',
                'title': 'data scientist'
            },
            'description': 'We are seeking a data scientist to analyze complex datasets...',
            'posted_date': '2024-01-13',
            'job_type': 'full_time'
        },
        {
            'id': 'job_4',
            'title': 'Junior Web Developer',
            'company': {
                'name': 'WebAgency',
                'size': 'small',
                'industry': 'marketing',
                'rating': 3.8
            },
            'location': {
                'city': 'Austin',
                'state': 'TX',
                'zip_code': '78701',
                'lat': 30.2672,
                'lng': -97.7431,
                'remote': False,
                'hybrid': False
            },
            'salary': {
                'min': 50000,
                'max': 70000,
                'currency': 'USD'
            },
            'required_skills': ['html', 'css', 'javascript', 'php', 'wordpress'],
            'experience_requirements': {
                'min_years': 0,
                'max_years': 2,
                'level': 'entry',
                'title': 'web developer'
            },
            'description': 'Entry-level position for a web developer...',
            'posted_date': '2024-01-12',
            'job_type': 'full_time'
        },
        {
            'id': 'job_5',
            'title': 'DevOps Engineer',
            'company': {
                'name': 'CloudTech',
                'size': 'large',
                'industry': 'cloud services',
                'rating': 4.7
            },
            'location': {
                'city': 'Seattle',
                'state': 'WA',
                'zip_code': '98101',
                'lat': 47.6062,
                'lng': -122.3321,
                'remote': True,
                'hybrid': True
            },
            'salary': {
                'min': 110000,
                'max': 160000,
                'currency': 'USD'
            },
            'required_skills': ['aws', 'docker', 'kubernetes', 'terraform', 'jenkins'],
            'experience_requirements': {
                'min_years': 4,
                'max_years': 8,
                'level': 'senior',
                'title': 'devops engineer'
            },
            'description': 'Looking for an experienced DevOps engineer...',
            'posted_date': '2024-01-11',
            'job_type': 'full_time'
        }
    ]

