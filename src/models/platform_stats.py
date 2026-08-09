from datetime import datetime
from src.shared import get_db_connection
import logging

logger = logging.getLogger(__name__)

class PlatformStats:
    """Platform statistics manager using raw SQL"""
    
    @staticmethod
    def get_value(key, default=0.0):
        """Get a stat value from the database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT stat_value FROM platform_stats WHERE stat_key = %s",
                    (key,)
                )
                result = cursor.fetchone()
                if result:
                    return float(result[0])
                return default
        except Exception as e:
            logger.error(f"Error getting stat {key}: {e}")
            return default

    @staticmethod
    def set_value(key, value, description=None):
        """Set a stat value in the database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO platform_stats (stat_key, stat_value, description, updated_at) 
                       VALUES (%s, %s, %s, %s) 
                       ON CONFLICT (stat_key) 
                       DO UPDATE SET stat_value = EXCLUDED.stat_value, 
                                     description = EXCLUDED.description,
                                     updated_at = EXCLUDED.updated_at""",
                    (key, float(value), description, datetime.now())
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting stat {key}: {e}")
            return False

    @staticmethod
    def increment(key, amount, description=None):
        """Increment a stat value"""
        try:
            current = PlatformStats.get_value(key, 0.0)
            new_value = current + float(amount)
            return PlatformStats.set_value(key, new_value, description)
        except Exception as e:
            logger.error(f"Error incrementing stat {key}: {e}")
            return False

    @staticmethod
    def get_all_stats():
        """Get all platform statistics"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT stat_key, stat_value, description, updated_at FROM platform_stats ORDER BY stat_key"
                )
                results = cursor.fetchall()
                stats = {}
                for row in results:
                    stats[row[0]] = {
                        'value': float(row[1]),
                        'description': row[2],
                        'updated_at': row[3]
                    }
                return stats
        except Exception as e:
            logger.error(f"Error getting all stats: {e}")
            return {}
