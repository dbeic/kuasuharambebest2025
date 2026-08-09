from src.models.admin import Admin
from src.shared import get_db_connection
import logging

logger = logging.getLogger(__name__)

class AdminRepository:
    @staticmethod
    def get_by_username(username):
        try:
            if not username:
                return None
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, hashed_password, role FROM admins WHERE username = %s", (username,))
                result = cursor.fetchone()
                if result:
                    logger.debug(f"Found admin: {result[1]}")
                    return Admin.from_row(result)
                else:
                    logger.debug(f"No admin found with username: {username}")
                    return None
        except Exception as e:
            logger.error(f"Error getting admin by username {username}: {e}", exc_info=True)
            return None

    @staticmethod
    def get_by_id(admin_id):
        try:
            if not admin_id:
                return None
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, hashed_password, role FROM admins WHERE id = %s", (admin_id,))
                result = cursor.fetchone()
                if result:
                    return Admin.from_row(result)
                return None
        except Exception as e:
            logger.error(f"Error getting admin by id {admin_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def create_admin(username, password):
        try:
            if not username or not password:
                return None
            with get_db_connection() as conn:
                cursor = conn.cursor()
                admin = Admin(username=username)
                admin.set_password(password)
                cursor.execute(
                    "INSERT INTO admins (username, hashed_password, role) VALUES (%s, %s, 'admin') RETURNING id",
                    (username, admin.hashed_password)
                )
                admin_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Created admin: {username} with ID: {admin_id}")
                return admin_id
        except Exception as e:
            logger.error(f"Error creating admin {username}: {e}", exc_info=True)
            return None
