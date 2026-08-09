from models.activity import UserActivity, VisitLog
from shared import get_db_connection
from datetime import datetime
import logging

class ActivityRepository:
    @staticmethod
    def log_user_activity(username, ip_address, path, method, user_agent, referrer):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO user_activity (username, ip_address, path, method, user_agent, referrer)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (username, ip_address, path, method, user_agent, referrer)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.debug(f"Failed to log user activity: {e}")
            return False
    
    @staticmethod
    def log_visit(ip_address, user_agent, referrer, path, timestamp=None):
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO visit_logs (ip_address, user_agent, referrer, path, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (ip_address, user_agent, referrer, path, timestamp)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.debug(f"Failed to log visit: {e}")
            return False
    
    @staticmethod
    def get_user_activity(limit=100):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, timestamp, username, ip_address, path, method, user_agent, referrer FROM user_activity ORDER BY timestamp DESC LIMIT %s",
                    (limit,)
                )
                rows = cursor.fetchall()
                return [UserActivity.from_row(row) for row in rows]
        except Exception as e:
            logging.error(f"Error getting user activity: {e}")
            return []
    
    @staticmethod
    def get_visit_logs(limit=100):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, ip_address, user_agent, referrer, path, timestamp FROM visit_logs ORDER BY timestamp DESC LIMIT %s",
                    (limit,)
                )
                rows = cursor.fetchall()
                return [VisitLog.from_row(row) for row in rows]
        except Exception as e:
            logging.error(f"Error getting visit logs: {e}")
            return []
    
    @staticmethod
    def clear_old_activity(days=30):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM user_activity WHERE timestamp < NOW() - INTERVAL '%s days'",
                    (days,)
                )
                cursor.execute(
                    "DELETE FROM visit_logs WHERE timestamp < NOW() - INTERVAL '%s days'",
                    (days,)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error clearing old activity: {e}")
            return False
