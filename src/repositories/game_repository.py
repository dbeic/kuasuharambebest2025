from models.game import Game
from shared import get_db_connection
from datetime import datetime
import logging
import secrets

class GameRepository:
    @staticmethod
    def generate_game_code():
        return ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(6))
    
    @staticmethod
    def create_upcoming_game(game_code, game_time):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO results (game_code, timestamp, status) VALUES (%s, %s, 'upcoming')",
                    (game_code, game_time)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error creating upcoming game: {e}")
            return False
    
    @staticmethod
    def get_upcoming_game():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, game_code, timestamp, num_users, total_amount, deduction, winner, winner_amount, outcome_message, status "
                    "FROM results WHERE status = 'upcoming' ORDER BY timestamp ASC LIMIT 1"
                )
                row = cursor.fetchone()
                if row:
                    return Game.from_row(row)
                return None
        except Exception as e:
            logging.error(f"Error getting upcoming game: {e}")
            return None
    
    @staticmethod
    def get_in_progress_game():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, game_code, timestamp, num_users, total_amount, deduction, winner, winner_amount, outcome_message, status "
                    "FROM results WHERE status = 'in progress' ORDER BY timestamp ASC LIMIT 1"
                )
                row = cursor.fetchone()
                if row:
                    return Game.from_row(row)
                return None
        except Exception as e:
            logging.error(f"Error getting in-progress game: {e}")
            return None
    
    @staticmethod
    def update_game_status(game_code, status):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE results SET status = %s WHERE game_code = %s", (status, game_code))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error updating game status: {e}")
            return False
    
    @staticmethod
    def complete_game(game_code, winner_username, winner_amount, num_players, total_pool, platform_fee, outcome_message):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE results SET 
                        status = 'completed', 
                        winner = %s, 
                        winner_amount = %s,
                        num_users = %s, 
                        total_amount = %s, 
                        deduction = %s,
                        outcome_message = %s,
                        timestamp = %s
                    WHERE game_code = %s
                    """,
                    (winner_username, winner_amount, num_players, total_pool, platform_fee, outcome_message, datetime.now(), game_code)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error completing game: {e}")
            return False
    
    @staticmethod
    def cancel_game(game_code, reason):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE results SET status = 'canceled', outcome_message = %s WHERE game_code = %s",
                    (reason, game_code)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error canceling game: {e}")
            return False
    
    @staticmethod
    def get_completed_games(limit=50):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, game_code, timestamp, num_users, total_amount, deduction, winner, winner_amount, outcome_message, status
                    FROM results
                    WHERE status = 'completed'
                    ORDER BY timestamp DESC
                    LIMIT %s
                    """,
                    (limit,)
                )
                rows = cursor.fetchall()
                return [Game.from_row(row) for row in rows]
        except Exception as e:
            logging.error(f"Error getting completed games: {e}")
            return []
    
    @staticmethod
    def add_to_queue(user_id):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO game_queue (user_id, timestamp) VALUES (%s, %s)",
                    (user_id, datetime.now())
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding to queue: {e}")
            return False
    
    @staticmethod
    def remove_from_queue(user_id):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM game_queue WHERE user_id = %s", (user_id,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error removing from queue: {e}")
            return False
    
    @staticmethod
    def is_in_queue(user_id):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM game_queue WHERE user_id = %s", (user_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking queue: {e}")
            return False
    
    @staticmethod
    def get_queued_players():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT u.id, u.username, u.wallet 
                    FROM users u
                    INNER JOIN game_queue gq ON u.id = gq.user_id
                    WHERE u.wallet >= 0  -- FIXED: Changed from 1.0 to 0
                """)
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting queued players: {e}")
            return []
    
    @staticmethod
    def clear_queue(user_ids):
        try:
            if not user_ids:
                return True
            with get_db_connection() as conn:
                cursor = conn.cursor()
                placeholders = ','.join(['%s'] * len(user_ids))
                cursor.execute(f"DELETE FROM game_queue WHERE user_id IN ({placeholders})", user_ids)
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error clearing queue: {e}")
            return False
    
    @staticmethod
    def get_active_games_count():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM results WHERE status = 'in progress'")
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logging.error(f"Error getting active games count: {e}")
            return 0
    
    @staticmethod
    def get_completed_games_count():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM results WHERE status = 'completed'")
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logging.error(f"Error getting completed games count: {e}")
            return 0
    
    @staticmethod
    def get_total_profit():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COALESCE(SUM(deduction), 0) FROM results WHERE status = 'completed' AND deduction > 0")
                result = cursor.fetchone()
                return float(result[0]) if result else 0.0
        except Exception as e:
            logging.error(f"Error getting total profit: {e}")
            return 0.0

    @staticmethod
    def reschedule_game(game_code, new_time):
        """Reschedule an existing game"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE results SET timestamp = %s WHERE game_code = %s",
                    (new_time, game_code)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error rescheduling game: {e}")
            return False
