import os
import sys
import logging
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt, decode_token
from flask_migrate import Migrate
from datetime import datetime, timezone

from src.config import config
from src.models.user import db, User
from src.models.job import Job, JobApplication, ApplicationQueue, JobSearchHistory

# Import blueprints
from src.routes.auth import auth_bp
from src.routes.profile import profile_bp
from src.routes.jobs import jobs_bp
from src.routes.applications import applications_bp
from src.routes.resume import resume_bp
from src.routes.matching import matching_bp
from src.routes.queue import queue_bp
from src.routes.analytics import analytics_bp

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app(config_object='src.config.Config'):
    """Application factory pattern"""
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))
    
    # Load configuration
    app.config.from_object(config_object)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5002"],
            "supports_credentials": True,
            "allow_headers": ["Content-Type", "Authorization", "X-CSRF-TOKEN"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "expose_headers": ["Authorization"],
            "max_age": 120
        }
    })
    jwt = JWTManager(app)
    migrate = Migrate(app, db)
    
    # Debug endpoint to check JWT configuration
    @app.route('/api/debug/token', methods=['GET'])
    def debug_token():
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No Authorization header'}), 401
        
        try:
            token = auth_header.split(' ')[1]
            logger.debug(f"Received token: {token}")
            
            # Try to decode the token
            decoded = decode_token(token)
            logger.debug(f"Decoded token: {decoded}")
            
            return jsonify({
                'message': 'Token is valid',
                'decoded': decoded
            })
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return jsonify({
                'error': 'Token validation failed',
                'details': str(e)
            }), 401

    # JWT configuration
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        try:
            identity = jwt_data["sub"]
            logger.debug(f"Looking up user with ID: {identity}")
            user = User.query.filter_by(id=int(identity)).one_or_none()
            logger.debug(f"Found user: {user}")
            return user
        except Exception as e:
            logger.error(f"User lookup error: {str(e)}")
            return None

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        try:
            jti = jwt_payload["jti"]
            logger.debug(f"Checking token JTI: {jti}")
            # For now, no tokens are blocked
            return False
        except Exception as e:
            logger.error(f"Token blocklist check error: {str(e)}")
            return True

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'code': 'token_expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logger.error(f"Invalid token error: {str(error)}")
        return jsonify({
            'error': 'Invalid token',
            'code': 'invalid_token',
            'details': str(error)
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Authorization token is missing',
            'code': 'missing_token'
        }), 401

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Fresh token required',
            'code': 'fresh_token_required'
        }), 401

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(jobs_bp, url_prefix='/api/jobs')
    app.register_blueprint(applications_bp, url_prefix='/api/applications')
    app.register_blueprint(resume_bp, url_prefix='/api/resume')
    app.register_blueprint(matching_bp, url_prefix='/api/matching')
    app.register_blueprint(queue_bp, url_prefix='/api/queue')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'environment': app.config['FLASK_ENV']
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'code': 'not_found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'code': 'internal_error'}), 500
    
    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        if request.method == 'OPTIONS':
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    # Serve React app
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return jsonify({'message': 'AutoJobApply API is running'}), 200
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)

