from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
import json

from src.models.user import db, User, Education, WorkExperience, UserProfile, UserPreferences

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user's complete profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get related data
        education = [edu.to_dict() for edu in user.education]
        work_experience = [work.to_dict() for work in user.work_experience]
        profile = user.profile.to_dict() if user.profile else None
        preferences = user.preferences.to_dict() if user.preferences else None
        
        return jsonify({
            'user': user.to_dict(),
            'education': education,
            'work_experience': work_experience,
            'profile': profile,
            'preferences': preferences
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get profile', 'details': str(e)}), 500

@profile_bp.route('/basic', methods=['PUT'])
@jwt_required()
def update_basic_info():
    """Update basic user information"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name'].strip()
        if 'phone' in data:
            user.phone = data['phone'].strip()
        if 'address' in data:
            user.address = data['address'].strip()
        if 'zip_code' in data:
            user.zip_code = data['zip_code'].strip()
        
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@profile_bp.route('/education', methods=['POST'])
@jwt_required()
def add_education():
    """Add education record"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['institution', 'degree_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate degree type
        valid_degrees = ['high_school', 'associate', 'bachelor', 'master', 'phd']
        if data['degree_type'] not in valid_degrees:
            return jsonify({'error': 'Invalid degree type'}), 400
        
        education = Education(
            user_id=user_id,
            institution=data['institution'].strip(),
            degree_type=data['degree_type'],
            field_of_study=data.get('field_of_study', '').strip(),
            graduation_year=data.get('graduation_year'),
            gpa=data.get('gpa')
        )
        
        db.session.add(education)
        db.session.commit()
        
        # Update user's calculated experience
        user = User.query.get(user_id)
        if user.profile:
            user.profile.total_experience = user.calculate_total_experience()
            user.profile.experience_level = user.get_experience_level()
            db.session.commit()
        
        return jsonify({
            'message': 'Education added successfully',
            'education': education.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add education', 'details': str(e)}), 500

@profile_bp.route('/education/<int:education_id>', methods=['PUT'])
@jwt_required()
def update_education(education_id):
    """Update education record"""
    try:
        user_id = get_jwt_identity()
        education = Education.query.filter_by(id=education_id, user_id=user_id).first()
        
        if not education:
            return jsonify({'error': 'Education record not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'institution' in data:
            education.institution = data['institution'].strip()
        if 'degree_type' in data:
            valid_degrees = ['high_school', 'associate', 'bachelor', 'master', 'phd']
            if data['degree_type'] not in valid_degrees:
                return jsonify({'error': 'Invalid degree type'}), 400
            education.degree_type = data['degree_type']
        if 'field_of_study' in data:
            education.field_of_study = data['field_of_study'].strip()
        if 'graduation_year' in data:
            education.graduation_year = data['graduation_year']
        if 'gpa' in data:
            education.gpa = data['gpa']
        
        education.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'message': 'Education updated successfully',
            'education': education.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update education', 'details': str(e)}), 500

@profile_bp.route('/education/<int:education_id>', methods=['DELETE'])
@jwt_required()
def delete_education(education_id):
    """Delete education record"""
    try:
        user_id = get_jwt_identity()
        education = Education.query.filter_by(id=education_id, user_id=user_id).first()
        
        if not education:
            return jsonify({'error': 'Education record not found'}), 404
        
        db.session.delete(education)
        db.session.commit()
        
        return jsonify({'message': 'Education deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete education', 'details': str(e)}), 500

@profile_bp.route('/work-experience', methods=['POST'])
@jwt_required()
def add_work_experience():
    """Add work experience record"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['job_title', 'company', 'start_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Parse dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = None
        if data.get('end_date') and not data.get('is_current', False):
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        work_experience = WorkExperience(
            user_id=user_id,
            job_title=data['job_title'].strip(),
            company=data['company'].strip(),
            start_date=start_date,
            end_date=end_date,
            is_current=data.get('is_current', False),
            is_direct=data.get('is_direct', True),
            description=data.get('description', '').strip(),
            skills=data.get('skills', '')
        )
        
        db.session.add(work_experience)
        db.session.commit()
        
        # Update user's calculated experience
        user = User.query.get(user_id)
        if user.profile:
            user.profile.total_experience = user.calculate_total_experience()
            user.profile.experience_level = user.get_experience_level()
            db.session.commit()
        
        return jsonify({
            'message': 'Work experience added successfully',
            'work_experience': work_experience.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add work experience', 'details': str(e)}), 500

@profile_bp.route('/work-experience/<int:work_id>', methods=['PUT'])
@jwt_required()
def update_work_experience(work_id):
    """Update work experience record"""
    try:
        user_id = get_jwt_identity()
        work = WorkExperience.query.filter_by(id=work_id, user_id=user_id).first()
        
        if not work:
            return jsonify({'error': 'Work experience not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'job_title' in data:
            work.job_title = data['job_title'].strip()
        if 'company' in data:
            work.company = data['company'].strip()
        if 'start_date' in data:
            work.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data and not data.get('is_current', work.is_current):
            work.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if 'is_current' in data:
            work.is_current = data['is_current']
            if work.is_current:
                work.end_date = None
        if 'is_direct' in data:
            work.is_direct = data['is_direct']
        if 'description' in data:
            work.description = data['description'].strip()
        if 'skills' in data:
            work.skills = data['skills']
        
        work.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'message': 'Work experience updated successfully',
            'work_experience': work.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update work experience', 'details': str(e)}), 500

@profile_bp.route('/work-experience/<int:work_id>', methods=['DELETE'])
@jwt_required()
def delete_work_experience(work_id):
    """Delete work experience record"""
    try:
        user_id = get_jwt_identity()
        work = WorkExperience.query.filter_by(id=work_id, user_id=user_id).first()
        
        if not work:
            return jsonify({'error': 'Work experience not found'}), 404
        
        db.session.delete(work)
        db.session.commit()
        
        return jsonify({'message': 'Work experience deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete work experience', 'details': str(e)}), 500

@profile_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """Get user preferences"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.preferences:
            # Create default preferences
            preferences = UserPreferences(user_id=user_id)
            db.session.add(preferences)
            db.session.commit()
            user.preferences = preferences
        
        return jsonify({'preferences': user.preferences.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get preferences', 'details': str(e)}), 500

@profile_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """Update user preferences"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.preferences:
            user.preferences = UserPreferences(user_id=user_id)
            db.session.add(user.preferences)
        
        data = request.get_json()
        preferences = user.preferences
        
        # Update preference fields
        if 'min_salary' in data:
            preferences.min_salary = data['min_salary']
        if 'max_salary' in data:
            preferences.max_salary = data['max_salary']
        if 'salary_type' in data:
            preferences.salary_type = data['salary_type']
        if 'max_commute_miles' in data:
            preferences.max_commute_miles = data['max_commute_miles']
        if 'remote_ok' in data:
            preferences.remote_ok = data['remote_ok']
        if 'hybrid_ok' in data:
            preferences.hybrid_ok = data['hybrid_ok']
        if 'onsite_ok' in data:
            preferences.onsite_ok = data['onsite_ok']
        if 'job_types' in data:
            preferences.job_types = json.dumps(data['job_types'])
        if 'industries' in data:
            preferences.industries = json.dumps(data['industries'])
        if 'company_sizes' in data:
            preferences.company_sizes = json.dumps(data['company_sizes'])
        if 'auto_respond_yes' in data:
            preferences.auto_respond_yes = data['auto_respond_yes']
        if 'daily_application_limit' in data:
            preferences.daily_application_limit = data['daily_application_limit']
        
        preferences.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': preferences.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update preferences', 'details': str(e)}), 500

