from flask import request, session
from src.shared import get_db_connection
import logging
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

def anonymize_ip(ip):
    if not ip:
        return '0.0.0.0'
    parts = ip.split('.')
    if len(parts) >= 4:
        return f"{parts[0]}.{parts[1]}.0.0"
    return ip

def log_user_activity():
    try:
        if request.path.startswith("/static"):
            return
        
        username = session.get('username') or session.get('admin_username') or 'anonymous'
        ip = anonymize_ip(request.remote_addr)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_activity (timestamp, username, ip_address, path, method, user_agent, referrer)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.now(),
                username,
                ip,
                request.path,
                request.method,
                request.user_agent.string if request.user_agent else None,
                request.referrer
            ))
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")

def log_visitor():
    try:
        if request.path.startswith("/static"):
            return
        
        ip = anonymize_ip(request.remote_addr)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO visit_logs (ip_address, user_agent, referrer, path, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                ip,
                request.user_agent.string if request.user_agent else None,
                request.referrer,
                request.path,
                datetime.now()
            ))
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging visitor: {e}")
