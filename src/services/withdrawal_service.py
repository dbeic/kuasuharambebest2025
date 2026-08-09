import psycopg2
from repositories.withdrawal_repository import WithdrawalRepository
from repositories.transaction_repository import TransactionRepository
from src.shared import get_db_connection
from datetime import datetime
import logging

class WithdrawalService:
    MIN_WITHDRAWAL = 100
    MAX_WITHDRAWAL = 50000
    DAILY_LIMIT = 3

    @staticmethod
    def create_withdrawal_request(user_id, username, requested_amount):
        """Create a withdrawal request"""
        from services.wallet_service import WalletService

        # Validate amount
        if requested_amount < WithdrawalService.MIN_WITHDRAWAL:
            return {'success': False, 'error': f'Minimum withdrawal amount is KES {WithdrawalService.MIN_WITHDRAWAL}'}

        if requested_amount > WithdrawalService.MAX_WITHDRAWAL:
            return {'success': False, 'error': f'Maximum withdrawal amount is KES {WithdrawalService.MAX_WITHDRAWAL}'}

        # Check available win earnings balance
        available_balance = WalletService.get_win_earnings_balance(user_id)
        if available_balance < requested_amount:
            return {'success': False, 'error': f'Insufficient balance. Available: KES {available_balance:.2f}'}

        # Check daily withdrawal limit
        today = datetime.now().date()
        daily_count = WithdrawalRepository.get_daily_withdrawal_count(user_id, today)
        if daily_count >= WithdrawalService.DAILY_LIMIT:
            return {'success': False, 'error': f'Daily withdrawal limit reached. You have made {daily_count} withdrawals today. Maximum is {WithdrawalService.DAILY_LIMIT} per day.'}

        # Calculate fees
        fee = WithdrawalRepository.calculate_fee(requested_amount)
        net_amount = requested_amount - fee

        # Generate receipt code
        receipt_code = f"WDR{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id}"

        # Create request
        success = WithdrawalRepository.create_request(
            user_id, username, requested_amount, fee, net_amount, receipt_code
        )

        if success:
            logging.info(f"Withdrawal request created for user {username} (ID: {user_id}). "
                        f"Amount: {requested_amount}, Fee: {fee}, Net: {net_amount}, "
                        f"Daily count: {daily_count + 1}/{WithdrawalService.DAILY_LIMIT}")
            return {'success': True, 'receipt_code': receipt_code}

        return {'success': False, 'error': 'Failed to create withdrawal request'}

    @staticmethod
    def approve_withdrawal(request_id, admin_id, admin_notes=None):
        """Approve a withdrawal request with transaction safety"""
        # Get the withdrawal request first (outside transaction)
        request = WithdrawalRepository.get_request_by_id(request_id)
        if not request:
            return {'success': False, 'error': 'Withdrawal request not found'}

        if request.status != 'pending':
            return {'success': False, 'error': f'Withdrawal already {request.status}'}

        with get_db_connection() as conn:
            try:
                cursor = conn.cursor()
                
                # Start transaction
                cursor.execute("BEGIN")
                
                # 1. Check current balance with row lock
                cursor.execute(
                    "SELECT wallet FROM users WHERE id = %s FOR UPDATE",
                    (request.user_id,)
                )
                result = cursor.fetchone()
                if not result:
                    cursor.execute("ROLLBACK")
                    return {'success': False, 'error': 'User not found'}

                current_balance = float(result[0])

                # 2. Verify sufficient balance
                if current_balance < request.requested_amount:
                    cursor.execute("ROLLBACK")
                    return {'success': False, 'error': f'Insufficient balance. Available: KES {current_balance:.2f}, Required: KES {request.requested_amount:.2f}'}

                # 3. Deduct amount from user wallet
                cursor.execute(
                    "UPDATE users SET wallet = wallet - %s WHERE id = %s",
                    (request.requested_amount, request.user_id)
                )

                # 4. Create withdrawal transaction
                cursor.execute(
                    """INSERT INTO transactions (user_id, type, amount, timestamp)
                       VALUES (%s, 'withdrawal', %s, %s)""",
                    (request.user_id, -request.requested_amount, datetime.now())
                )

                # 5. Update withdrawal request status
                cursor.execute(
                    """UPDATE withdrawal_requests
                       SET status = 'approved',
                           processed_time = %s,
                           processed_by = %s,
                           admin_notes = %s
                       WHERE id = %s""",
                    (datetime.now(), admin_id, admin_notes, request_id)
                )

                # 6. Commit
                cursor.execute("COMMIT")

                logging.info(f"Withdrawal {request.id} approved for user {request.username}, "
                           f"Amount: {request.requested_amount}, Fee: {request.withdrawal_fee}")
                return {'success': True, 'message': 'Withdrawal approved successfully'}

            except Exception as e:
                try:
                    cursor.execute("ROLLBACK")
                except Exception as rollback_error:
                    logging.error(f"Rollback failed: {rollback_error}")
                logging.error(f"Withdrawal approval failed: {e}", exc_info=True)
                return {'success': False, 'error': f'Failed to approve withdrawal: {str(e)}'}

    @staticmethod
    def reject_withdrawal(request_id, admin_id, admin_notes=None):
        """Reject a withdrawal request"""
        request = WithdrawalRepository.get_request_by_id(request_id)
        if not request:
            return {'success': False, 'error': 'Withdrawal request not found'}

        if request.status != 'pending':
            return {'success': False, 'error': f'Withdrawal already {request.status}'}

        success = WithdrawalRepository.update_request_status(request_id, 'rejected', admin_id, admin_notes)
        if success:
            logging.info(f"Withdrawal {request.id} rejected for user {request.username}")
            return {'success': True, 'message': 'Withdrawal rejected successfully'}

        return {'success': False, 'error': 'Failed to reject withdrawal'}

    @staticmethod
    def mark_withdrawal_completed(request_id, admin_id, admin_notes=None):
        """Mark a withdrawal as completed"""
        request = WithdrawalRepository.get_request_by_id(request_id)
        if not request or request.status != 'approved':
            return {'success': False, 'error': 'Withdrawal not found or not approved'}

        success = WithdrawalRepository.update_request_status(request_id, 'completed', admin_id, admin_notes)
        if success:
            logging.info(f"Withdrawal {request.id} marked as completed for user {request.username}")
            return {'success': True, 'message': 'Withdrawal marked as completed'}

        return {'success': False, 'error': 'Failed to mark withdrawal as completed'}

    @staticmethod
    def get_pending_count():
        """Get count of pending withdrawal requests"""
        return len(WithdrawalRepository.get_pending_requests())

    @staticmethod
    def get_request_by_receipt(receipt_code):
        """Get withdrawal request by receipt code"""
        return WithdrawalRepository.get_request_by_receipt(receipt_code)

    @staticmethod
    def get_withdrawal_history(user_id, limit=10):
        """Get withdrawal history for a user"""
        return WithdrawalRepository.get_user_withdrawals(user_id, limit)

    @staticmethod
    def get_daily_withdrawal_count(user_id):
        """Get today's withdrawal count for a user"""
        today = datetime.now().date()
        return WithdrawalRepository.get_daily_withdrawal_count(user_id, today)

    @staticmethod
    def get_all_withdrawals(limit=100):
        """Get all withdrawal requests"""
        return WithdrawalRepository.get_all_requests(limit)
