from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone

from src.models.job import db, JobApplication, ApplicationQueue

applications_bp = Blueprint('applications', __name__)

@applications_bp.route('/', methods=['GET'])
@jwt_required()
def get_applications():
    """Get user's job applications"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        
        # Build query
        query = JobApplication.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Paginate results
        applications = query.order_by(JobApplication.applied_at.desc())\
                           .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'applications': [app.to_dict() for app in applications.items],
            'total': applications.total,
            'pages': applications.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get applications', 'details': str(e)}), 500

@applications_bp.route('/<int:application_id>', methods=['GET'])
@jwt_required()
def get_application_details(application_id):
    """Get detailed information about a specific application"""
    try:
        user_id = get_jwt_identity()
        
        application = JobApplication.query.filter_by(
            id=application_id, 
            user_id=user_id
        ).first()
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        return jsonify({'application': application.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get application details', 'details': str(e)}), 500

@applications_bp.route('/<int:application_id>/status', methods=['PUT'])
@jwt_required()
def update_application_status(application_id):
    """Update application status (for manual tracking)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('status'):
            return jsonify({'error': 'Status is required'}), 400
        
        valid_statuses = ['pending', 'submitted', 'failed', 'rejected', 'interview', 'hired']
        if data['status'] not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        application = JobApplication.query.filter_by(
            id=application_id, 
            user_id=user_id
        ).first()
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        application.status = data['status']
        application.last_status_update = datetime.now(timezone.utc)
        
        if data['status'] in ['rejected', 'interview', 'hired']:
            application.response_received_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Application status updated successfully',
            'application': application.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update application status', 'details': str(e)}), 500

@applications_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_application_stats():
    """Get application statistics for the user"""
    try:
        user_id = get_jwt_identity()
        
        # Get basic counts
        total_applications = JobApplication.query.filter_by(user_id=user_id).count()
        
        # Get status breakdown
        status_counts = db.session.query(
            JobApplication.status,
            db.func.count(JobApplication.id)
        ).filter_by(user_id=user_id).group_by(JobApplication.status).all()
        
        # Get method breakdown
        method_counts = db.session.query(
            JobApplication.application_method,
            db.func.count(JobApplication.id)
        ).filter_by(user_id=user_id).group_by(JobApplication.application_method).all()
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc).replace(day=1)  # Simplified for demo
        recent_applications = JobApplication.query.filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= thirty_days_ago
        ).count()
        
        return jsonify({
            'total_applications': total_applications,
            'recent_applications': recent_applications,
            'status_breakdown': dict(status_counts),
            'method_breakdown': dict(method_counts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get application stats', 'details': str(e)}), 500

@applications_bp.route('/queue', methods=['GET'])
@jwt_required()
def get_application_queue():
    """Get user's application queue status"""
    try:
        user_id = get_jwt_identity()
        
        # Get queued applications
        queued = ApplicationQueue.query.filter_by(
            user_id=user_id,
            status='queued'
        ).order_by(ApplicationQueue.priority.desc(), ApplicationQueue.created_at).all()
        
        # Get processing applications
        processing = ApplicationQueue.query.filter_by(
            user_id=user_id,
            status='processing'
        ).all()
        
        return jsonify({
            'queued': [q.to_dict() for q in queued],
            'processing': [p.to_dict() for p in processing],
            'total_queued': len(queued),
            'total_processing': len(processing)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get application queue', 'details': str(e)}), 500

