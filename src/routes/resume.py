import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from src.services.resume_processor import ResumeProcessor
import logging

resume_bp = Blueprint('resume', __name__)

# Configure upload settings
UPLOAD_FOLDER = 'uploads/resumes'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_upload_folder():
    """Create upload folder if it doesn't exist"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@resume_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    """
    Upload and process a resume file
    
    Expected form data:
    - file: Resume file (PDF, DOC, DOCX)
    - auto_populate: Boolean to auto-populate profile (optional, default: true)
    """
    try:
        user_id = get_jwt_identity()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Supported formats: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400
        
        # Create upload folder
        create_upload_folder()
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{user_id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Process resume
        processor = ResumeProcessor()
        result = processor.process_resume(file_path)
        
        if not result['success']:
            # Clean up file on processing error
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify(result), 400
        
        # Auto-populate profile if requested
        auto_populate = request.form.get('auto_populate', 'true').lower() == 'true'
        profile_result = None
        
        if auto_populate:
            profile_result = processor.auto_populate_profile(
                result['extracted_data'], 
                user_id
            )
        
        # Clean up file after processing (optional - you might want to keep it)
        # if os.path.exists(file_path):
        #     os.remove(file_path)
        
        response_data = {
            'success': True,
            'message': 'Resume processed successfully',
            'extracted_data': result['extracted_data'],
            'file_info': {
                'original_filename': file.filename,
                'file_size': file_size,
                'processed_at': str(datetime.utcnow())
            }
        }
        
        if profile_result:
            response_data['profile_update'] = profile_result
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Error uploading resume: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@resume_bp.route('/analyze-text', methods=['POST'])
@jwt_required()
def analyze_resume_text():
    """
    Analyze resume text directly (without file upload)
    
    Expected JSON:
    - text: Resume text content
    - auto_populate: Boolean to auto-populate profile (optional, default: false)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Resume text is required'
            }), 400
        
        resume_text = data['text']
        
        if not resume_text.strip():
            return jsonify({
                'success': False,
                'error': 'Resume text cannot be empty'
            }), 400
        
        # Create a temporary file for processing
        temp_filename = f"temp_{user_id}_{uuid.uuid4().hex}.txt"
        temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
        
        create_upload_folder()
        
        # Write text to temporary file
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(resume_text)
        
        # Process using the text directly (modify processor to handle text)
        processor = ResumeProcessor()
        
        # Extract information directly from text
        contact_info = processor.extract_contact_info(resume_text)
        skills = processor.extract_skills(resume_text)
        education = processor.extract_education(resume_text)
        work_experience = processor.extract_work_experience(resume_text)
        total_experience_years = processor.calculate_total_experience(work_experience)
        experience_level = processor.classify_experience_level(total_experience_years)
        
        # Extract name (first line heuristic)
        lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
        name = lines[0] if lines else ""
        
        extracted_data = {
            'name': name,
            'contact_info': contact_info,
            'skills': skills,
            'education': education,
            'work_experience': work_experience,
            'total_experience_years': total_experience_years,
            'experience_level': experience_level,
            'raw_text': resume_text
        }
        
        # Auto-populate profile if requested
        auto_populate = data.get('auto_populate', False)
        profile_result = None
        
        if auto_populate:
            profile_result = processor.auto_populate_profile(extracted_data, user_id)
        
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        response_data = {
            'success': True,
            'message': 'Resume text analyzed successfully',
            'extracted_data': extracted_data
        }
        
        if profile_result:
            response_data['profile_update'] = profile_result
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Error analyzing resume text: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@resume_bp.route('/skills/suggestions', methods=['GET'])
@jwt_required()
def get_skill_suggestions():
    """
    Get skill suggestions for auto-complete
    """
    try:
        processor = ResumeProcessor()
        
        # Flatten all skills for suggestions
        all_skills = []
        for category, skills_list in processor.technical_skills.items():
            all_skills.extend(skills_list)
        
        # Get query parameter for filtering
        query = request.args.get('q', '').lower()
        
        if query:
            # Filter skills based on query
            filtered_skills = [skill for skill in all_skills if query in skill.lower()]
            return jsonify({
                'success': True,
                'skills': filtered_skills[:20]  # Limit to 20 suggestions
            }), 200
        else:
            return jsonify({
                'success': True,
                'skills': all_skills[:50]  # Return first 50 skills
            }), 200
            
    except Exception as e:
        logging.error(f"Error getting skill suggestions: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@resume_bp.route('/user-files', methods=['GET'])
@jwt_required()
def get_user_resume_files():
    """
    Get list of uploaded resume files for the current user
    """
    try:
        user_id = get_jwt_identity()
        
        if not os.path.exists(UPLOAD_FOLDER):
            return jsonify({
                'success': True,
                'files': []
            }), 200
        
        # Get all files for this user
        user_files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.startswith(f"{user_id}_"):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file_stats = os.stat(file_path)
                
                user_files.append({
                    'filename': filename,
                    'size': file_stats.st_size,
                    'uploaded_at': str(datetime.fromtimestamp(file_stats.st_ctime)),
                    'file_type': filename.split('.')[-1].upper()
                })
        
        # Sort by upload date (newest first)
        user_files.sort(key=lambda x: x['uploaded_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': user_files
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting user files: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# Add missing import
from datetime import datetime

