from models.withdrawal import WithdrawalRequest, WithdrawalLimit
from shared import get_db_connection
from datetime import datetime
import logging

class WithdrawalRepository:
    @staticmethod
    def create_request(user_id, username, requested_amount, fee, net_amount, receipt_code):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO withdrawal_requests
                    (user_id, username, requested_amount, withdrawal_fee, net_amount, status, receipt_code)
                    VALUES (%s, %s, %s, %s, %s, 'pending', %s)
                    """,
                    (user_id, username, requested_amount, fee, net_amount, receipt_code)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error creating withdrawal request: {e}")
            return False

    @staticmethod
    def get_pending_requests():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT wr.*, u.email
                    FROM withdrawal_requests wr
                    JOIN users u ON wr.user_id = u.id
                    WHERE wr.status = 'pending'
                    ORDER BY wr.request_time ASC
                """)
                rows = cursor.fetchall()
                return [WithdrawalRequest.from_row(row) for row in rows]
        except Exception as e:
            logging.error(f"Error getting pending requests: {e}")
            return []

    @staticmethod
    def get_all_requests(limit=100):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT wr.*, u.email
                    FROM withdrawal_requests wr
                    JOIN users u ON wr.user_id = u.id
                    ORDER BY wr.request_time DESC
                    LIMIT %s
                """, (limit,))
                rows = cursor.fetchall()
                return [WithdrawalRequest.from_row(row) for row in rows]
        except Exception as e:
            logging.error(f"Error getting all requests: {e}")
            return []

    @staticmethod
    def get_request_by_id(request_id):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM withdrawal_requests WHERE id = %s", (request_id,))
                row = cursor.fetchone()
                if row:
                    return WithdrawalRequest.from_row(row)
                return None
        except Exception as e:
            logging.error(f"Error getting request by id: {e}")
            return None

    @staticmethod
    def get_request_by_receipt(receipt_code):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM withdrawal_requests WHERE receipt_code = %s", (receipt_code,))
                return WithdrawalRequest.from_row(cursor.fetchone())
        except Exception as e:
            logging.error(f"Error getting request by receipt: {e}")
            return None

    @staticmethod
    def update_request_status(request_id, status, processed_by, admin_notes=None):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE withdrawal_requests
                    SET status = %s, processed_time = %s, processed_by = %s, admin_notes = %s
                    WHERE id = %s
                    """,
                    (status, datetime.now(), processed_by, admin_notes, request_id)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error updating request status: {e}")
            return False

    @staticmethod
    def get_daily_withdrawal_count(user_id, date):
        """
        Get count of successful (pending, approved, completed) withdrawals for a user today.
        Rejected withdrawals are NOT counted towards the daily limit.
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                start_of_day = datetime.combine(date, datetime.min.time())
                end_of_day = datetime.combine(date, datetime.max.time())
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM withdrawal_requests
                    WHERE user_id = %s
                    AND request_time BETWEEN %s AND %s
                    AND status != 'rejected'
                    """,
                    (user_id, start_of_day, end_of_day)
                )
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logging.error(f"Error getting daily withdrawal count: {e}")
            return 0

    @staticmethod
    def get_user_withdrawals(user_id, limit=10):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, user_id, username, requested_amount, withdrawal_fee, net_amount,
                           status, request_time, processed_time, processed_by, admin_notes, receipt_code
                    FROM withdrawal_requests
                    WHERE user_id = %s
                    ORDER BY request_time DESC
                    LIMIT %s
                    """,
                    (user_id, limit)
                )
                rows = cursor.fetchall()
                return [WithdrawalRequest.from_row(row) for row in rows]
        except Exception as e:
            logging.error(f"Error getting user withdrawals: {e}")
            return []

    @staticmethod
    def calculate_fee(amount):
        """Calculate withdrawal fee based on amount"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT fee_amount, fee_percentage
                    FROM withdrawal_fees
                    WHERE min_amount <= %s AND (max_amount >= %s OR max_amount IS NULL)
                    AND is_active = TRUE
                    ORDER BY min_amount DESC
                    LIMIT 1
                    """,
                    (amount, amount)
                )
                result = cursor.fetchone()
                if result:
                    fee_amount, fee_percentage = result
                    if fee_amount and fee_amount > 0:
                        return float(fee_amount)
                    if fee_percentage and fee_percentage > 0:
                        return amount * (fee_percentage / 100)
                return 0.0
        except Exception as e:
            logging.error(f"Error calculating fee: {e}")
            return 0.0
