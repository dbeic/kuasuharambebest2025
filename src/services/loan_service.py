import logging
from datetime import datetime
from decimal import Decimal
from src.shared import get_db_connection
from src.repositories.user_repository import UserRepository
from src.repositories.transaction_repository import TransactionRepository

logger = logging.getLogger(__name__)

class LoanService:
    LOAN_AMOUNT = 200.00
    MIN_WITHDRAWAL = 100.00
    REPAYMENT_THRESHOLD = 100.00

    @staticmethod
    def create_loan_for_user(user_id):
        """Create a loan for a new user automatically"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Check if user already has a loan
                cursor.execute(
                    "SELECT id FROM user_loans WHERE user_id = %s",
                    (user_id,)
                )
                existing = cursor.fetchone()
                if existing:
                    logger.info(f"User {user_id} already has a loan")
                    return True

                # Create loan
                cursor.execute("""
                    INSERT INTO user_loans (user_id, loan_amount, repaid_amount, remaining_balance)
                    VALUES (%s, %s, 0.00, %s)
                """, (user_id, LoanService.LOAN_AMOUNT, LoanService.LOAN_AMOUNT))

                conn.commit()
                logger.info(f"Loan created for user {user_id}: KES {LoanService.LOAN_AMOUNT}")
                return True
        except Exception as e:
            logger.error(f"Error creating loan for user {user_id}: {e}")
            return False

    @staticmethod
    def get_loan_status(user_id):
        """Get current loan status for a user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, user_id, loan_amount, repaid_amount, remaining_balance,
                           is_fully_repaid, created_at, updated_at
                    FROM user_loans
                    WHERE user_id = %s
                """, (user_id,))
                row = cursor.fetchone()

                if not row:
                    # No loan found - create one automatically
                    LoanService.create_loan_for_user(user_id)
                    cursor.execute("""
                        SELECT id, user_id, loan_amount, repaid_amount, remaining_balance,
                               is_fully_repaid, created_at, updated_at
                        FROM user_loans
                        WHERE user_id = %s
                    """, (user_id,))
                    row = cursor.fetchone()

                if row:
                    return {
                        'loan_id': row[0],
                        'user_id': row[1],
                        'loan_amount': float(row[2]),
                        'repaid_amount': float(row[3]),
                        'remaining_balance': float(row[4]),
                        'is_fully_repaid': row[5],
                        'created_at': row[6],
                        'updated_at': row[7]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting loan status for user {user_id}: {e}")
            return None

    @staticmethod
    def check_and_process_automatic_repayment(user_id, game_code=None):
        """
        Check if user has reached repayment threshold and process automatic repayment
        Called during game completion
        """
        try:
            # Get user's win_earnings
            win_earnings = TransactionRepository.get_win_earnings_balance(user_id)
            loan_status = LoanService.get_loan_status(user_id)

            if not loan_status:
                logger.warning(f"No loan found for user {user_id}, attempting to create")
                LoanService.create_loan_for_user(user_id)
                loan_status = LoanService.get_loan_status(user_id)
                if not loan_status:
                    return {'success': False, 'error': 'Loan not found and could not be created'}

            if loan_status['is_fully_repaid']:
                return {'success': True, 'message': 'Loan already fully repaid'}

            # Check if win_earnings reached threshold
            if win_earnings >= LoanService.REPAYMENT_THRESHOLD:
                remaining = loan_status['remaining_balance']
                repayment_amount = min(100.00, remaining, win_earnings)

                if repayment_amount <= 0:
                    return {'success': False, 'error': 'No repayment amount available'}

                # Process repayment
                return LoanService.process_loan_repayment(
                    user_id,
                    repayment_amount,
                    game_code,
                    win_earnings
                )

            return {
                'success': True,
                'message': f'Win earnings below threshold: {win_earnings:.2f}/{LoanService.REPAYMENT_THRESHOLD}',
                'win_earnings': win_earnings
            }

        except Exception as e:
            logger.error(f"Error processing automatic repayment for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def process_loan_repayment(user_id, amount, game_code=None, win_earnings_before=None):
        """Process a loan repayment from user's win earnings"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("BEGIN")

                # Get current loan
                cursor.execute("""
                    SELECT id, remaining_balance, repaid_amount, is_fully_repaid
                    FROM user_loans
                    WHERE user_id = %s FOR UPDATE
                """, (user_id,))
                loan = cursor.fetchone()

                if not loan:
                    cursor.execute("ROLLBACK")
                    return {'success': False, 'error': 'Loan not found'}

                loan_id, remaining, repaid, is_fully_repaid = loan

                if is_fully_repaid:
                    cursor.execute("ROLLBACK")
                    return {'success': True, 'message': 'Loan already repaid'}

                # Calculate new values
                new_remaining = max(0, remaining - amount)
                new_repaid = repaid + amount
                is_fully_repaid_now = new_remaining <= 0

                # Update loan
                cursor.execute("""
                    UPDATE user_loans
                    SET remaining_balance = %s,
                        repaid_amount = %s,
                        is_fully_repaid = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (new_remaining, new_repaid, is_fully_repaid_now, loan_id))

                # Mark win_earnings as withdrawn (used for repayment)
                cursor.execute("""
                    UPDATE win_earnings
                    SET is_withdrawn = TRUE,
                        withdrawn_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND is_withdrawn = FALSE
                    ORDER BY earned_at ASC
                    LIMIT %s
                """, (user_id, amount))

                # Record repayment in loan_repayments table
                win_earnings_after = win_earnings_before - amount if win_earnings_before else 0
                cursor.execute("""
                    INSERT INTO loan_repayments
                    (user_id, game_code, amount, repayment_type, win_earnings_before, win_earnings_after)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, game_code, amount, 'automatic', win_earnings_before, win_earnings_after))

                # Update house account
                cursor.execute("""
                    UPDATE house_account
                    SET total_loan_repayments = total_loan_repayments + %s,
                        available_balance = available_balance + %s,
                        total_balance = total_balance + %s,
                        updated_at = CURRENT_TIMESTAMP
                """, (amount, amount, amount))

                conn.commit()

                logger.info(f"Loan repayment processed: User {user_id}, Amount {amount}, "
                           f"Remaining {new_remaining}, Fully repaid: {is_fully_repaid_now}")

                return {
                    'success': True,
                    'repayment_amount': amount,
                    'new_remaining': new_remaining,
                    'is_fully_repaid': is_fully_repaid_now,
                    'win_earnings_used': amount,
                    'win_earnings_remaining': win_earnings_after
                }

        except Exception as e:
            logger.error(f"Error processing loan repayment for user {user_id}: {e}")
            try:
                cursor.execute("ROLLBACK")
            except:
                pass
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_withdrawal_availability(user_id):
        """
        Get comprehensive withdrawal availability for a user
        """
        try:
            loan_status = LoanService.get_loan_status(user_id)
            win_earnings = TransactionRepository.get_win_earnings_balance(user_id)
            wallet_balance = UserRepository.get_wallet_balance(user_id)

            # Check if fully repaid
            is_loan_cleared = loan_status and loan_status['is_fully_repaid']

            # Calculate withdrawable amount (only from win_earnings)
            withdrawable_amount = win_earnings

            # Check if withdrawal threshold met
            threshold_met = withdrawable_amount >= LoanService.MIN_WITHDRAWAL

            # Check if user has any pending withdrawal requests
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM withdrawal_queue
                    WHERE user_id = %s AND status = 'pending'
                """, (user_id,))
                pending_count = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT COUNT(*) FROM withdrawal_requests
                    WHERE user_id = %s AND status IN ('pending', 'approved')
                """, (user_id,))
                pending_requests = cursor.fetchone()[0]

            # Get queue position if applicable
            queue_position = None
            if pending_count > 0:
                cursor.execute("""
                    SELECT queue_position FROM withdrawal_queue
                    WHERE user_id = %s AND status = 'pending'
                    ORDER BY queue_position ASC LIMIT 1
                """, (user_id,))
                queue_position = cursor.fetchone()
                queue_position = queue_position[0] if queue_position else None

            # Determine if user can withdraw
            # NOTE: House account balance check is removed for users
            # Users should only see loan status and win_earnings
            can_withdraw = (
                is_loan_cleared and
                threshold_met and
                pending_count == 0 and
                pending_requests == 0
            )

            # Build reasons if blocked
            reasons = []
            if not is_loan_cleared:
                remaining = loan_status['remaining_balance'] if loan_status else 200.00
                reasons.append(f"Outstanding loan: KES {remaining:.2f}")

            if not threshold_met:
                reasons.append(f"Minimum withdrawal: KES {LoanService.MIN_WITHDRAWAL} (Available: KES {withdrawable_amount:.2f})")

            if pending_count > 0:
                reasons.append(f"Pending withdrawal request in queue (Position: {queue_position})")

            if pending_requests > 0:
                reasons.append("Pending withdrawal request being processed")

            return {
                'can_withdraw': can_withdraw,
                'withdrawable_amount': withdrawable_amount if can_withdraw else 0,
                'loan_cleared': is_loan_cleared,
                'threshold_met': threshold_met,
                'wallet_balance': wallet_balance,
                'win_earnings': win_earnings,
                'pending_withdrawal_count': pending_count,
                'pending_requests': pending_requests,
                'queue_position': queue_position,
                'reasons': reasons,
                'loan_status': loan_status,
                'status': 'available' if can_withdraw else 'blocked'
            }

        except Exception as e:
            logger.error(f"Error getting withdrawal availability for user {user_id}: {e}")
            return {
                'can_withdraw': False,
                'withdrawable_amount': 0,
                'loan_cleared': False,
                'threshold_met': False,
                'status': 'error',
                'reasons': ['System error. Please try again later.']
            }

    @staticmethod
    def add_to_withdrawal_queue(user_id, amount):
        """
        Add a user to the withdrawal queue
        """
        try:
            availability = LoanService.get_withdrawal_availability(user_id)

            if not availability['can_withdraw']:
                return {
                    'success': False,
                    'error': 'Withdrawal not available',
                    'reasons': availability['reasons']
                }

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("BEGIN")

                # Get current queue position
                cursor.execute("SELECT COALESCE(MAX(queue_position), 0) + 1 FROM withdrawal_queue")
                new_position = cursor.fetchone()[0]

                # Add to queue
                cursor.execute("""
                    INSERT INTO withdrawal_queue
                    (user_id, amount, queue_position, status, priority, created_at)
                    VALUES (%s, %s, %s, 'pending', 0, CURRENT_TIMESTAMP)
                """, (user_id, amount, new_position))

                # Update house account pending withdrawals
                cursor.execute("""
                    UPDATE house_account
                    SET pending_withdrawals = pending_withdrawals + %s,
                        available_balance = available_balance - %s,
                        updated_at = CURRENT_TIMESTAMP
                """, (amount, amount))

                conn.commit()

                logger.info(f"User {user_id} added to withdrawal queue at position {new_position}")

                return {
                    'success': True,
                    'queue_position': new_position,
                    'amount': amount,
                    'estimated_payment': 'Pending house account availability'
                }

        except Exception as e:
            logger.error(f"Error adding user to withdrawal queue: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def process_withdrawal_queue():
        """
        Process the withdrawal queue based on house account availability
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Get house account balance
                cursor.execute("""
                    SELECT available_balance FROM house_account
                    ORDER BY id DESC LIMIT 1
                """)
                house = cursor.fetchone()
                if not house:
                    return {'success': False, 'error': 'House account not found'}

                available = float(house[0])

                # Get pending withdrawals ordered by priority and position
                cursor.execute("""
                    SELECT id, user_id, amount, queue_position
                    FROM withdrawal_queue
                    WHERE status = 'pending'
                    ORDER BY priority DESC, queue_position ASC
                    LIMIT 10
                """)
                pending = cursor.fetchall()

                processed = 0
                for withdrawal in pending:
                    withdrawal_id, user_id, amount, position = withdrawal

                    if available < amount:
                        break

                    # Process this withdrawal
                    # 1. Deduct from house account
                    cursor.execute("""
                        UPDATE house_account
                        SET available_balance = available_balance - %s,
                            pending_withdrawals = pending_withdrawals - %s,
                            updated_at = CURRENT_TIMESTAMP
                    """, (amount, amount))

                    # 2. Mark as processed
                    cursor.execute("""
                        UPDATE withdrawal_queue
                        SET status = 'processing',
                            processed_at = CURRENT_TIMESTAMP,
                            estimated_payment_date = CURRENT_TIMESTAMP + INTERVAL '1 day'
                        WHERE id = %s
                    """, (withdrawal_id,))

                    # 3. Create actual withdrawal request
                    from src.services.withdrawal_service import WithdrawalService
                    user = UserRepository.get_by_id(user_id)
                    if user:
                        result = WithdrawalService.create_withdrawal_request(
                            user_id,
                            user.username,
                            amount
                        )

                        if result['success']:
                            processed += 1
                            available -= amount
                            logger.info(f"Processed withdrawal for user {user_id}: {amount}")

                    # Update available balance for next iteration
                    cursor.execute("""
                        SELECT available_balance FROM house_account
                        ORDER BY id DESC LIMIT 1
                    """)
                    available = float(cursor.fetchone()[0])

                conn.commit()

                return {
                    'success': True,
                    'processed': processed,
                    'remaining_available': available
                }

        except Exception as e:
            logger.error(f"Error processing withdrawal queue: {e}")
            return {'success': False, 'error': str(e)}
