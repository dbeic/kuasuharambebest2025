from models.admin import Admin
from shared import get_db_connection
import logging

logger = logging.getLogger(__name__)

class AdminStatsRepository:
    """Repository for admin dashboard statistics and reporting."""
    
    @staticmethod
    def get_dashboard_stats():
        """Get all dashboard statistics in a single query"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Total users
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0] or 0

                # Active users (users with activity in last 7 days)
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM transactions
                    WHERE timestamp >= datetime('now', '-7 days')
                """)
                active_users = cursor.fetchone()[0] or 0

                # New users today
                cursor.execute("""
                    SELECT COUNT(*) FROM users
                    WHERE date(created_at) = date('now')
                """)
                new_users_today = cursor.fetchone()[0] or 0

                # Total deposits from transactions
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM transactions
                    WHERE type = 'deposit'
                """)
                total_deposits = float(cursor.fetchone()[0] or 0)

                # Total withdrawals from transactions
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM transactions
                    WHERE type = 'withdrawal'
                """)
                total_withdrawals = float(cursor.fetchone()[0] or 0)

                # Pending withdrawals count and amount
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(net_amount), 0)
                    FROM withdrawal_requests
                    WHERE status = 'pending'
                """)
                pending_result = cursor.fetchone()
                pending_count = pending_result[0] or 0
                pending_amount = float(pending_result[1] or 0)

                # Approved withdrawals
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(net_amount), 0)
                    FROM withdrawal_requests
                    WHERE status IN ('approved', 'completed')
                """)
                approved_result = cursor.fetchone()
                approved_count = approved_result[0] or 0
                approved_amount = float(approved_result[1] or 0)

                # Rejected withdrawals
                cursor.execute("""
                    SELECT COUNT(*) FROM withdrawal_requests
                    WHERE status = 'rejected'
                """)
                rejected_count = cursor.fetchone()[0] or 0

                # Total platform balance (sum of all user wallets)
                cursor.execute("SELECT COALESCE(SUM(wallet), 0) FROM users")
                total_balance = float(cursor.fetchone()[0] or 0)

                # Total platform profit from game deductions
                cursor.execute("""
                    SELECT COALESCE(SUM(deduction), 0) FROM results
                    WHERE status = 'completed'
                """)
                platform_profit = float(cursor.fetchone()[0] or 0)

                # Platform fees from transactions
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM transactions
                    WHERE type = 'platform_fee'
                """)
                platform_fees = float(cursor.fetchone()[0] or 0)

                # Games statistics
                cursor.execute("SELECT COUNT(*) FROM results WHERE status = 'completed'")
                completed_games = cursor.fetchone()[0] or 0

                cursor.execute("SELECT COUNT(*) FROM results WHERE status IN ('active', 'running', 'in progress')")
                active_games = cursor.fetchone()[0] or 0

                # Winners and losers
                cursor.execute("""
                    SELECT COUNT(*) FROM results
                    WHERE winner IS NOT NULL AND status = 'completed'
                """)
                winners = cursor.fetchone()[0] or 0

                cursor.execute("""
                    SELECT COUNT(*) FROM results
                    WHERE winner IS NULL AND status = 'completed'
                """)
                losers = cursor.fetchone()[0] or 0

                # Total jackpot value
                cursor.execute("""
                    SELECT COALESCE(SUM(winner_amount), 0) FROM results
                    WHERE winner IS NOT NULL AND status = 'completed'
                """)
                total_jackpot = float(cursor.fetchone()[0] or 0)

                # Daily statistics
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_games,
                        COALESCE(SUM(total_amount), 0) as total_amount,
                        COALESCE(SUM(deduction), 0) as total_profit
                    FROM results
                    WHERE date(timestamp) = date('now') AND status = 'completed'
                """)
                daily_game_stats = cursor.fetchone()
                daily_games = daily_game_stats[0] or 0
                daily_amount = float(daily_game_stats[1] or 0)
                daily_profit = float(daily_game_stats[2] or 0)

                # Weekly statistics
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_games,
                        COALESCE(SUM(total_amount), 0) as total_amount,
                        COALESCE(SUM(deduction), 0) as total_profit
                    FROM results
                    WHERE timestamp >= datetime('now', '-7 days') AND status = 'completed'
                """)
                weekly_game_stats = cursor.fetchone()
                weekly_games = weekly_game_stats[0] or 0
                weekly_amount = float(weekly_game_stats[1] or 0)
                weekly_profit = float(weekly_game_stats[2] or 0)

                # Monthly statistics
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_games,
                        COALESCE(SUM(total_amount), 0) as total_amount,
                        COALESCE(SUM(deduction), 0) as total_profit
                    FROM results
                    WHERE timestamp >= datetime('now', '-30 days') AND status = 'completed'
                """)
                monthly_game_stats = cursor.fetchone()
                monthly_games = monthly_game_stats[0] or 0
                monthly_amount = float(monthly_game_stats[1] or 0)
                monthly_profit = float(monthly_game_stats[2] or 0)

                return {
                    'total_users': total_users,
                    'active_users': active_users,
                    'new_users_today': new_users_today,
                    'total_deposits': total_deposits,
                    'total_withdrawals': total_withdrawals,
                    'pending_withdrawals': pending_count,
                    'pending_withdrawal_amount': pending_amount,
                    'approved_withdrawals': approved_count,
                    'approved_withdrawal_amount': approved_amount,
                    'rejected_withdrawals': rejected_count,
                    'total_balance': total_balance,
                    'platform_profit': platform_profit,
                    'platform_fees': platform_fees,
                    'completed_games': completed_games,
                    'active_games': active_games,
                    'winners': winners,
                    'losers': losers,
                    'total_jackpot': total_jackpot,
                    'daily_games': daily_games,
                    'daily_amount': daily_amount,
                    'daily_profit': daily_profit,
                    'weekly_games': weekly_games,
                    'weekly_amount': weekly_amount,
                    'weekly_profit': weekly_profit,
                    'monthly_games': monthly_games,
                    'monthly_amount': monthly_amount,
                    'monthly_profit': monthly_profit,
                }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}", exc_info=True)
            return {}

    @staticmethod
    def get_recent_activities(limit=20):
        """Get recent user activities"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        username,
                        path as action,
                        timestamp,
                        ip_address,
                        path
                    FROM user_activity
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))
                results = cursor.fetchall()
                return [{
                    'username': row[0],
                    'action': row[1] or 'view',
                    'timestamp': row[2],
                    'ip_address': row[3],
                    'path': row[4] or '/'
                } for row in results]
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}", exc_info=True)
            return []

# Keep backward compatibility - also export as AdminRepository for existing imports
# This allows both AdminStatsRepository and AdminRepository to work
AdminRepository = AdminStatsRepository
