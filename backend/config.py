"""
Herbalife Distributor SaaS Platform - Configuration Module
Manages application settings from environment variables.

Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.
Migration Path: Config will be decentralized via user-controlled vaults and DID-based identity.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env file from same directory as this file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # --- Database ---
    MYSQL_HOST = os.getenv('MYSQL_HOST', '')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', '')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'enpi_ai')

    # Default SQLite path for easy local development
    _default_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'enpi_ai.db')

    # Database Connection Logic:
    # 1. Explicit DATABASE_URL takes precedence
    # 2. MySQL env vars if all are set
    # 3. SQLite fallback for local dev
    if os.getenv('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    elif os.getenv('MYSQL_HOST') and os.getenv('MYSQL_USER') and os.getenv('MYSQL_PASSWORD'):
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
            f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', '3306')}"
            f"/{os.getenv('MYSQL_DATABASE', 'enpi_ai')}"
        )
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{_default_db}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,      # Recycle connections before MySQL default timeout (28800s) or shorter cloud timeouts
        'pool_pre_ping': True,    # Self-healing connection check
        'pool_timeout': 30,
        'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),      # Configurable: 5 for 1GB RAM, 20+ for high scale
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 5)), # Burst capacity
    }

    # --- Pinecone (Vector DB) ---
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY', '')
    PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', '')
    PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'enpi-ai-rag')

    # --- LLM Providers ---
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY', '')
    DEFAULT_LLM_PROVIDER = os.getenv('DEFAULT_LLM_PROVIDER', 'openai')
    DEFAULT_LLM_MODEL = os.getenv('DEFAULT_LLM_MODEL', 'gpt-4')

    # --- Google APIs ---
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/auth/google/callback')

    # --- SMTP (Email) ---
    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', '')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

    # --- WhatsApp Service ---
    WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL', 'http://localhost:3001').rstrip('/')
    WHATSAPP_API_SECRET = os.getenv('WHATSAPP_API_SECRET', '')

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

    # --- File Uploads ---
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'xlsx', 'csv'}

    # --- Celery / Redis (Task Queue - Phase 11) ---
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV environment variable"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
