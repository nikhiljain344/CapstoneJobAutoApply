import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

# Flask configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
DEBUG = os.environ.get('FLASK_ENV') == 'development'

# Database configuration
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///instance/dev.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# JWT configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-jwt-secret-key-here')
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # Token expires in 24 hours
JWT_TOKEN_LOCATION = ['headers']
JWT_HEADER_NAME = 'Authorization'
JWT_HEADER_TYPE = 'Bearer'
JWT_ERROR_MESSAGE_KEY = 'error'

# CORS configuration
CORS_ORIGINS = [
    'http://localhost:5173',  # Vite dev server
    'http://localhost:3000',  # Alternative frontend port
    'http://127.0.0.1:5173',
    'http://127.0.0.1:3000',
]

# API configuration
API_TITLE = 'Job Auto Apply API'
API_VERSION = 'v1'

class Config:
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = SQLALCHEMY_TRACK_MODIFICATIONS
    JWT_SECRET_KEY = JWT_SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = JWT_ACCESS_TOKEN_EXPIRES
    JWT_TOKEN_LOCATION = JWT_TOKEN_LOCATION
    JWT_HEADER_NAME = JWT_HEADER_NAME
    JWT_HEADER_TYPE = JWT_HEADER_TYPE
    JWT_ERROR_MESSAGE_KEY = JWT_ERROR_MESSAGE_KEY
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access']
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET') or 'autojobapply-resumes'
    AWS_S3_REGION = os.environ.get('AWS_S3_REGION') or 'us-east-1'
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Email Configuration
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    MAIL_FROM_EMAIL = os.environ.get('MAIL_FROM_EMAIL') or 'noreply@autojobapply.com'
    STAFFING_EMAIL = 'staffing@cswpbc.org'
    
    # Job Board APIs
    INDEED_API_KEY = os.environ.get('INDEED_API_KEY')
    MONSTER_API_KEY = os.environ.get('MONSTER_API_KEY')
    GOOGLE_GEOCODING_API_KEY = os.environ.get('GOOGLE_GEOCODING_API_KEY')
    
    # Security
    BCRYPT_LOG_ROUNDS = 12
    
    # API configuration
    API_TITLE = API_TITLE
    API_VERSION = API_VERSION

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

