from models.user import User
from shared import get_db_connection
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    @staticmethod
    def get_by_id(user_id):
        try:
            if not user_id:
                return None
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, username, hashed_password, wallet FROM users WHERE id = %s", (user_id,))
                row = cursor.fetchone()
                if row:
                    return User(id=row[0], email=row[1], username=row[2], hashed_password=row[3], wallet=row[4])
                return None
        except Exception as e:
            logger.error(f"Error getting user by id {user_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_by_username(username):
        try:
            if not username:
                return None
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, username, hashed_password, wallet FROM users WHERE username = %s", (username,))
                row = cursor.fetchone()
                if row:
                    return User(id=row[0], email=row[1], username=row[2], hashed_password=row[3], wallet=row[4])
                return None
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_by_email(email):
        try:
            if not email:
                return None
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, username, hashed_password, wallet FROM users WHERE email = %s", (email,))
                row = cursor.fetchone()
                if row:
                    return User(id=row[0], email=row[1], username=row[2], hashed_password=row[3], wallet=row[4])
                return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def create_user(email, username, hashed_password):
        try:
            if not all([email, username, hashed_password]):
                return None
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (email, username, hashed_password, wallet) VALUES (%s, %s, %s, 0.0) RETURNING id",
                    (email, username, hashed_password)
                )
                user_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"User created: {username} (ID: {user_id})")
                return user_id
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def update_wallet(user_id, amount):
        try:
            if not user_id or amount is None:
                return None
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET wallet = wallet + %s WHERE id = %s RETURNING wallet", (amount, user_id))
                result = cursor.fetchone()
                conn.commit()
                if result:
                    logger.info(f"Wallet updated for user {user_id}: {amount}")
                    return float(result[0])
                return None
        except Exception as e:
            logger.error(f"Error updating wallet for user {user_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_wallet_balance(user_id):
        try:
            if not user_id:
                return 0.0
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT wallet FROM users WHERE id = %s", (user_id,))
                result = cursor.fetchone()
                return float(result[0]) if result else 0.0
        except Exception as e:
            logger.error(f"Error getting wallet balance for user {user_id}: {e}", exc_info=True)
            return 0.0
    
    @staticmethod
    def get_all_users():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, username, hashed_password, wallet FROM users ORDER BY id ASC")
                rows = cursor.fetchall()
                return [User(id=row[0], email=row[1], username=row[2], hashed_password=row[3], wallet=row[4]) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all users: {e}", exc_info=True)
            return []
    
    @staticmethod
    def get_total_balance():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COALESCE(SUM(wallet), 0) FROM users")
                result = cursor.fetchone()
                return float(result[0]) if result else 0.0
        except Exception as e:
            logger.error(f"Error getting total balance: {e}", exc_info=True)
            return 0.0
    
    @staticmethod
    def check_allowed_username(username):
        try:
            if not username:
                return False
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM allowed_users WHERE username = %s", (username,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking allowed username {username}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def add_allowed_username(username):
        try:
            if not username:
                return False
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO allowed_users (username) VALUES (%s) ON CONFLICT DO NOTHING", (username,))
                conn.commit()
                logger.info(f"Added allowed username: {username}")
                return True
        except Exception as e:
            logger.error(f"Error adding allowed username {username}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def remove_allowed_username(username):
        try:
            if not username:
                return False
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM allowed_users WHERE username = %s", (username,))
                conn.commit()
                logger.info(f"Removed allowed username: {username}")
                return True
        except Exception as e:
            logger.error(f"Error removing allowed username {username}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def get_allowed_users():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM allowed_users")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting allowed users: {e}", exc_info=True)
            return []
