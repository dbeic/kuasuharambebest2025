import os
from datetime import timedelta

class Config:
    # SECRET_KEY must be set via environment variable in production
    # Development will use a fallback
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    CASH_DATABASE = os.getenv('CASH_DATABASE')
    CASH_USERNAME = os.getenv('CASH_USERNAME')
    CASH_PASSWORD = os.getenv('CASH_PASSWORD')

    GAME_STAKE_AMOUNT = 10.0
    PLATFORM_FEE_PERCENTAGE = 0.10
    GAME_CYCLE_SECONDS = 30

    MIN_WITHDRAWAL = 100
    MAX_WITHDRAWAL = 50000
    MIN_DEPOSIT = 50
    MAX_DEPOSIT = 50000

    OTP_EXPIRY_MINUTES = 30
    OTP_MAX_ATTEMPTS = 5

    # CSRF Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv('SECRET_KEY')
    WTF_CSRF_TIME_LIMIT = 1800  # 30 minutes

    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }

    RATE_LIMITS = {
        'default': '200 per day',
        'login': '5 per minute, 200 per hour',
        'play': '10 per minute',
        'withdraw': '3 per hour',
        'deposit': '5 per hour'
    }

    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    # In development, allow a default secret key
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    # SECRET_KEY MUST be set via environment variable
    # If not set, the application will fail to start in app.py

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
