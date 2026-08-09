from models.transaction import Transaction
from shared import get_db_connection
from datetime import datetime
import logging

class TransactionRepository:
    @staticmethod
    def create_transaction(user_id, transaction_type, amount, game_code=None):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, timestamp, game_code) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, transaction_type, amount, datetime.now(), game_code)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error creating transaction: {e}")
            return False

    @staticmethod
    def create(transaction):
        return TransactionRepository.create_transaction(
            transaction.user_id,
            transaction.type,
            transaction.amount,
            transaction.game_code
        )

    @staticmethod
    def get_user_transactions(user_id, limit=50):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, user_id, type, amount, timestamp, game_code FROM transactions WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s",
                    (user_id, limit)
                )
                rows = cursor.fetchall()
                return [Transaction.from_row(row) for row in rows]
        except Exception as e:
            logging.error(f"Error getting user transactions: {e}")
            return []

    @staticmethod
    def get_win_earnings_balance(user_id):
        """
        Calculate withdrawable balance for a user.
        = Total un-withdrawn win_earnings - Total approved/completed withdrawals
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # 1. Get total un-withdrawn winnings from win_earnings table
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM win_earnings
                    WHERE user_id = %s AND is_withdrawn = FALSE
                """, (user_id,))
                total_wins = float(cursor.fetchone()[0] or 0)

                # 2. Get total approved/completed withdrawals
                cursor.execute("""
                    SELECT COALESCE(SUM(requested_amount), 0)
                    FROM withdrawal_requests
                    WHERE user_id = %s AND status IN ('approved', 'completed')
                """, (user_id,))
                total_withdrawals = float(cursor.fetchone()[0] or 0)

                # 3. Calculate available balance
                available_balance = total_wins - total_withdrawals

                # Ensure balance doesn't go negative
                if available_balance < 0:
                    logging.warning(f"Negative withdrawable balance for user {user_id}: {available_balance}. Setting to 0.")
                    available_balance = 0.0

                logging.debug(f"User {user_id} withdrawable balance: {available_balance} (wins: {total_wins}, withdrawals: {total_withdrawals})")
                return available_balance

        except Exception as e:
            logging.error(f"Error getting win earnings balance for user {user_id}: {e}", exc_info=True)
            return 0.0

    @staticmethod
    def mark_earnings_withdrawn(user_id):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE win_earnings SET is_withdrawn = TRUE, withdrawn_at = %s WHERE user_id = %s AND is_withdrawn = FALSE",
                    (datetime.now(), user_id)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error marking earnings as withdrawn: {e}")
            return False
