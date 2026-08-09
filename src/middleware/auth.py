from functools import wraps
from flask import session, redirect, url_for, flash, request
import logging

logger = logging.getLogger(__name__)

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if role == "admin":
                    # Check if admin session exists and is valid
                    admin_id = session.get('admin_id')
                    is_admin = session.get('is_admin')
                    
                    if not admin_id or not is_admin:
                        logger.warning(f"Admin access denied: admin_id={admin_id}, is_admin={is_admin}")
                        flash("Please log in as admin to access this page.", "error")
                        return redirect(url_for("auth.admin_login"))
                    
                    logger.info(f"Admin access granted: {session.get('admin_username', 'Unknown')}")
                    return f(*args, **kwargs)

                if "user_id" not in session:
                    flash("Please log in to access this page.", "error")
                    return redirect(url_for("auth.login"))

                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Authentication check error: {e}", exc_info=True)
                flash("Authentication error. Please log in again.", "error")
                if role == "admin":
                    return redirect(url_for("auth.admin_login"))
                return redirect(url_for("auth.login"))
        return decorated_function
    return decorator
