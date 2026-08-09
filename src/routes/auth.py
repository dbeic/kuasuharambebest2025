from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from src.services.auth_service import AuthService
from src.services.loan_service import LoanService
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get('user_id'):
        return redirect(url_for('game.index'))

    if request.method == "POST":
        try:
            csrf_token = request.form.get('csrf_token', '')
            if not csrf_token:
                logger.warning("CSRF token missing for login")
                return render_template("auth/login.html", error="CSRF token missing. Please try again.")
            try:
                validate_csrf(csrf_token)
            except BadRequest as e:
                logger.warning(f"CSRF validation failed for login: {e}")
                return render_template("auth/login.html", error="CSRF token validation failed. Please try again.")

            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if not username or not password:
                return render_template("auth/login.html", error="Username and password are required")

            result = AuthService.login_user(username, password)

            if result['success']:
                try:
                    session.clear()
                    session['user_id'] = result['user'].id
                    session['username'] = result['user'].username
                    session.permanent = True
                    session.modified = True
                    logger.info(f"Session created for user: {username} (ID: {result['user'].id})")
                except Exception as e:
                    logger.error(f"Session setup error for user {username}: {e}", exc_info=True)
                    session.clear()
                    return render_template("auth/login.html", error="Login failed. Please try again.")

                response = redirect(url_for('game.index'))
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response
            else:
                return render_template("auth/login.html", error=result['error'])

        except Exception as e:
            logger.error(f"Unexpected error during login: {e}", exc_info=True)
            session.clear()
            return render_template("auth/login.html", error="An unexpected error occurred. Please try again.")

    return render_template("auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            csrf_token = request.form.get('csrf_token', '')
            if not csrf_token:
                logger.warning("CSRF token missing for registration")
                return render_template("auth/register.html", error="CSRF token missing. Please try again.")
            try:
                validate_csrf(csrf_token)
            except BadRequest as e:
                logger.warning(f"CSRF validation failed for registration: {e}")
                return render_template("auth/register.html", error="CSRF token validation failed. Please try again.")

            email = request.form.get("email", "").strip()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if not all([email, username, password]):
                return render_template("auth/register.html", error="All fields are required")

            result = AuthService.register_user(email, username, password)

            if result['success']:
                user_id = result['user_id']
                
                # Automatically create loan for the new user
                loan_created = LoanService.create_loan_for_user(user_id)
                
                if loan_created:
                    # Add loan amount to user's wallet
                    from src.repositories.user_repository import UserRepository
                    UserRepository.update_wallet(user_id, 200.00)
                    logger.info(f"Loan of KES 200 automatically added to user {username}'s wallet")
                    
                    flash("Registration successful! You have received a KES 200 welcome loan to start playing!", "success")
                else:
                    flash("Registration successful but loan setup failed. Please contact support.", "warning")

                return redirect(url_for('auth.login'))
            else:
                return render_template("auth/register.html", error=result['error'])

        except Exception as e:
            logger.error(f"Unexpected error during registration: {e}", exc_info=True)
            return render_template("auth/register.html", error="An unexpected error occurred. Please try again.")

    return render_template("auth/register.html")

@auth_bp.route("/logout")
def logout():
    try:
        username = session.get('username', 'Unknown')
        logger.info(f"User logout: {username}")
        session.clear()
        flash("You have been logged out successfully.", "info")
    except Exception as e:
        logger.error(f"Error during logout: {e}", exc_info=True)
        session.clear()

    return redirect(url_for('game.index'))

@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get('admin_id') and session.get('is_admin'):
        return redirect(url_for('admin.dashboard'))

    if request.method == "POST":
        try:
            csrf_token = request.form.get('csrf_token', '')
            if not csrf_token:
                logger.warning("CSRF token missing for admin login")
                return render_template("auth/admin_login.html", error="CSRF token missing. Please try again.")

            try:
                validate_csrf(csrf_token)
            except Exception as e:
                logger.warning(f"CSRF validation failed for admin login: {e}")
                return render_template("auth/admin_login.html", error="CSRF token validation failed. Please try again.")

            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if not username or not password:
                return render_template("auth/admin_login.html", error="Username and password are required")

            result = AuthService.login_admin(username, password)

            if result['success']:
                try:
                    session.clear()
                    session['admin_id'] = result['admin'].id
                    session['admin_username'] = result['admin'].username
                    session['is_admin'] = True
                    session.permanent = True
                    session.modified = True
                    logger.info(f"Admin session created: {username} (ID: {result['admin'].id})")
                except Exception as e:
                    logger.error(f"Session setup error for admin {username}: {e}", exc_info=True)
                    session.clear()
                    return render_template("auth/admin_login.html", error="Admin login failed. Please try again.")

                response = redirect(url_for('admin.dashboard'))
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['X-Frame-Options'] = 'SAMEORIGIN'
                return response
            else:
                return render_template("auth/admin_login.html", error=result['error'])

        except Exception as e:
            logger.error(f"Unexpected error during admin login: {e}", exc_info=True)
            session.clear()
            return render_template("auth/admin_login.html", error="An unexpected error occurred. Please try again.")

    return render_template("auth/admin_login.html")

@auth_bp.route("/admin/logout")
def admin_logout():
    try:
        username = session.get('admin_username', 'Unknown')
        logger.info(f"Admin logout: {username}")
        session.clear()
    except Exception as e:
        logger.error(f"Error during admin logout: {e}", exc_info=True)
        session.clear()

    return redirect(url_for('auth.admin_login'))
