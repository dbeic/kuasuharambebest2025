import os
import logging
from flask import Flask, session, request, render_template, jsonify
from flask_limiter import Limiter
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from datetime import datetime, timedelta
import threading
import time

load_dotenv()

# Local imports
from config import config
from middleware.rate_limit import rate_limit_key
from middleware.logging import log_user_activity, log_visitor
from routes.auth import auth_bp
from routes.game import game_bp
from routes.wallet import wallet_bp
from routes.admin import admin_bp
from routes.api import api_bp
from routes.static_pages import pages_bp
from workers.game_worker import start_game_loop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag to prevent multiple worker starts
_worker_started = False
_worker_lock = threading.Lock()

def create_app(config_name='default'):
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Load configuration
    app.config.from_object(config.get(config_name))

    # CRITICAL FIX: Secret key must be set - no default fallback in production
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        if os.getenv('FLASK_ENV') == 'production':
            raise ValueError("SECRET_KEY environment variable must be set in production")
        else:
            secret_key = 'dev-key-change-in-production'
            logger.warning("Using development secret key - DO NOT USE IN PRODUCTION")
    
    app.secret_key = secret_key

    # Session configuration - CRITICAL for production
    app.config.update(
        SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_SECRET_KEY=secret_key,
        WTF_CSRF_TIME_LIMIT=3600
    )

    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)
    logger.info("CSRF protection initialized")

    # Initialize rate limiter
    limiter = Limiter(key_func=rate_limit_key, default_limits=[], app=app, storage_uri="memory://")
    logger.info("Rate limiter initialized")

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(pages_bp)

    @app.before_request
    def before_request_func():
        if request.path.startswith("/static"):
            return
        log_user_activity()
        log_visitor()
        if session.get('admin_id') or session.get('user_id'):
            if not request.path.startswith('/admin/process_') and not request.path.startswith('/admin/update_'):
                session.modified = True

    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "upgrade-insecure-requests"
        )
        response.headers['Content-Security-Policy'] = csp_policy
        
        if os.getenv('FLASK_ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    @app.route('/health')
    def health_check():
        from shared import get_db_connection, _db_pool
        
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'unknown',
            'pool': 'available' if _db_pool is not None else 'unavailable'
        }
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                status['database'] = 'connected'
        except Exception as e:
            status['status'] = 'unhealthy'
            status['database'] = f'error: {str(e)}'
            return jsonify(status), 503
        
        return jsonify(status), 200
    
    @app.route('/ready')
    def ready_check():
        status = {
            'ready': True,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            from shared import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
        except Exception as e:
            status['ready'] = False
            status['error'] = str(e)
            return jsonify(status), 503
        
        return jsonify(status), 200

    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', 
                              error_code=404, 
                              error_message='Page not found',
                              wallet_balance=0.0), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return render_template('error.html',
                              error_code=500,
                              error_message='Internal server error. Please try again later.',
                              wallet_balance=0.0), 500

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('error.html',
                              error_code=403,
                              error_message='Access forbidden',
                              wallet_balance=0.0), 403

    @app.errorhandler(405)
    def method_not_allowed(error):
        return render_template('error.html',
                              error_code=405,
                              error_message='Method not allowed',
                              wallet_balance=0.0), 405

    @app.errorhandler(429)
    def too_many_requests(error):
        return render_template('error.html',
                              error_code=429,
                              error_message='Too many requests. Please try again later.',
                              wallet_balance=0.0), 429

    app.game_loop_started = False

    @app.before_request
    def start_background_tasks():
        global _worker_started
        if not app.game_loop_started and not request.path.startswith("/static"):
            if not _worker_started:
                with _worker_lock:
                    if not _worker_started:
                        _worker_started = True
                        app.game_loop_started = True
                        thread = threading.Thread(target=start_game_loop, daemon=True)
                        thread.start()
                        logger.info("Game worker thread started (single instance)")

    return app

app = create_app(os.getenv('FLASK_ENV', 'default'))
