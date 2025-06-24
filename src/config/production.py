import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class ProductionConfig:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/prod.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Security settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') 