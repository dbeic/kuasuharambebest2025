from repositories.user_repository import UserRepository
from repositories.admin_repository import AdminRepository
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from flask import session, request
from datetime import datetime
from utils.validators import validate_email, validate_username, validate_password

logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    def register_user(email, username, password):
        try:
            # Input validation using existing validators
            if not all([email, username, password]):
                return {'success': False, 'error': 'All fields are required'}
            
            if not validate_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            
            if not validate_username(username):
                return {'success': False, 'error': 'Username must be 3-50 characters and contain only letters, numbers, dots, underscores, or hyphens'}
            
            if not validate_password(password):
                return {'success': False, 'error': 'Password must be at least 6 characters long'}
            
            if not UserRepository.check_allowed_username(username):
                return {'success': False, 'error': 'Username is not allowed'}
            
            hashed_password = generate_password_hash(password.strip(), method='scrypt')
            
            user_id = UserRepository.create_user(email.strip(), username.strip(), hashed_password)
            if user_id:
                UserRepository.remove_allowed_username(username.strip())
                logger.info(f"User registered successfully: {username} (ID: {user_id})")
                return {'success': True, 'user_id': user_id}
            
            return {'success': False, 'error': 'Email or username already exists'}
        
        except Exception as e:
            logger.error(f"Registration error for user {username}: {e}", exc_info=True)
            return {'success': False, 'error': 'Registration failed. Please try again later.'}
    
    @staticmethod
    def login_user(username, password):
        try:
            # Input validation
            if not username or not password:
                return {'success': False, 'error': 'Username and password are required'}
            
            if not validate_username(username):
                return {'success': False, 'error': 'Invalid username format'}
            
            # Check failed attempts
            failed_attempts = session.get('failed_login_attempts', 0)
            if failed_attempts >= 5:
                return {'success': False, 'error': 'Too many failed attempts. Please try again in 15 minutes.'}
            
            user = UserRepository.get_by_username(username.strip())
            
            # Check if user exists
            if not user:
                # Increment failed attempts
                session['failed_login_attempts'] = failed_attempts + 1
                session.permanent = True
                logger.warning(f"Failed login attempt for non-existent user: {username} from IP: {request.remote_addr}")
                return {'success': False, 'error': 'Invalid username or password'}
            
            # Check password
            if check_password_hash(user.hashed_password, password.strip()):
                # Check if user is suspended
                suspension = AuthService.check_user_suspension(user.id)
                if suspension:
                    suspension_end = suspension[0]
                    reason = suspension[1] or 'Account suspended'
                    logger.warning(f"Suspended user attempted login: {username} until {suspension_end}")
                    return {'success': False, 'error': f'Account suspended until {suspension_end.strftime("%Y-%m-%d %H:%M")}. Reason: {reason}'}
                
                # Reset failed attempts on success
                session.pop('failed_login_attempts', None)
                logger.info(f"Successful login: {username} (ID: {user.id}) from IP: {request.remote_addr}")
                return {'success': True, 'user': user}
            else:
                # Increment failed attempts
                session['failed_login_attempts'] = failed_attempts + 1
                session.permanent = True
                logger.warning(f"Failed login attempt for user: {username} (wrong password) from IP: {request.remote_addr}")
                return {'success': False, 'error': 'Invalid username or password'}
        
        except Exception as e:
            logger.error(f"Login error for user {username}: {e}", exc_info=True)
            return {'success': False, 'error': 'Login failed. Please try again later.'}
    
    @staticmethod
    def login_admin(username, password):
        try:
            # Input validation
            if not username or not password:
                return {'success': False, 'error': 'Username and password are required'}
            
            admin = AdminRepository.get_by_username(username.strip())
            if admin:
                logger.info(f"Admin login attempt: {admin.username}")
                password_valid = check_password_hash(admin.hashed_password, password.strip())
                if password_valid:
                    logger.info(f"Successful admin login: {username} from IP: {request.remote_addr}")
                    return {'success': True, 'admin': admin}
                else:
                    logger.warning(f"Failed admin login: {username} (wrong password) from IP: {request.remote_addr}")
            else:
                logger.warning(f"Admin not found: {username} from IP: {request.remote_addr}")
            
            return {'success': False, 'error': 'Invalid admin credentials'}
        
        except Exception as e:
            logger.error(f"Admin login error for {username}: {e}", exc_info=True)
            return {'success': False, 'error': 'Admin login failed. Please try again later.'}
    
    @staticmethod
    def get_user_by_id(user_id):
        try:
            if not user_id:
                return None
            return UserRepository.get_by_id(user_id)
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_admin_by_id(admin_id):
        try:
            if not admin_id:
                return None
            return AdminRepository.get_by_id(admin_id)
        except Exception as e:
            logger.error(f"Error getting admin by ID {admin_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def check_user_suspension(user_id):
        from shared import get_db_connection
        try:
            if not user_id:
                return None
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT suspension_end, reason 
                    FROM user_suspensions 
                    WHERE user_id = %s AND suspension_end > CURRENT_TIMESTAMP
                    ORDER BY suspended_at DESC LIMIT 1
                """, (user_id,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error checking user suspension for user {user_id}: {e}", exc_info=True)
            return None
