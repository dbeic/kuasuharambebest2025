from models.deposit import DepositRequest
from shared import get_db_connection
from datetime import datetime
import logging

class DepositRepository:
    @staticmethod
    def create_request(user_id, username, amount, voucher_code):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO deposit_requests 
                    (user_id, username, amount, voucher_code, status)
                    VALUES (%s, %s, %s, %s, 'pending')
                    """,
                    (user_id, username, amount, voucher_code)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error creating deposit request: {e}")
            return False
    
    @staticmethod
    def get_pending_requests():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dr.*, u.email
                    FROM deposit_requests dr
                    JOIN users u ON dr.user_id = u.id
                    WHERE dr.status = 'pending'
                    ORDER BY dr.request_time ASC
                """)
                rows = cursor.fetchall()
                return [DepositRequest.from_row(row) for row in rows]
        except Exception as e:
            logging.error(f"Error getting pending requests: {e}")
            return []
    
    @staticmethod
    def get_all_requests(limit=100):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dr.*, u.email
                    FROM deposit_requests dr
                    JOIN users u ON dr.user_id = u.id
                    ORDER BY dr.request_time DESC
                    LIMIT %s
                """, (limit,))
                rows = cursor.fetchall()
                return [DepositRequest.from_row(row) for row in rows]
        except Exception as e:
            logging.error(f"Error getting all requests: {e}")
            return []
    
    @staticmethod
    def get_request_by_id(request_id):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM deposit_requests WHERE id = %s", (request_id,))
                return DepositRequest.from_row(cursor.fetchone())
        except Exception as e:
            logging.error(f"Error getting request by id: {e}")
            return None
    
    @staticmethod
    def get_request_by_voucher_code(voucher_code):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM deposit_requests WHERE voucher_code = %s", (voucher_code,))
                return DepositRequest.from_row(cursor.fetchone())
        except Exception as e:
            logging.error(f"Error getting request by voucher code: {e}")
            return None
    
    @staticmethod
    def update_request_status(request_id, status, processed_by, admin_notes=None):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE deposit_requests 
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
