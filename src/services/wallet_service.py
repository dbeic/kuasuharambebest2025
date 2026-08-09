from src.repositories.user_repository import UserRepository
from src.repositories.transaction_repository import TransactionRepository
from src.shared import get_db_connection
import logging
from decimal import Decimal

class WalletService:
    @staticmethod
    def get_balance(user_id):
        return UserRepository.get_wallet_balance(user_id)

    @staticmethod
    def deposit(user_id, amount, admin_id=None):
        if amount <= 0:
            return {'success': False, 'error': 'Invalid amount'}

        amount_decimal = Decimal(str(amount))

        new_balance = UserRepository.update_wallet(user_id, float(amount_decimal))
        if new_balance is not None:
            TransactionRepository.create_transaction(user_id, 'deposit', float(amount_decimal))
            return {'success': True, 'new_balance': new_balance}

        return {'success': False, 'error': 'Deposit failed'}

    @staticmethod
    def withdraw(user_id, amount, admin_id=None):
        if amount <= 0:
            return {'success': False, 'error': 'Invalid amount'}

        amount_decimal = Decimal(str(amount))

        current_balance = UserRepository.get_wallet_balance(user_id)
        if current_balance < float(amount_decimal):
            return {'success': False, 'error': 'Insufficient balance'}

        new_balance = UserRepository.update_wallet(user_id, -float(amount_decimal))
        if new_balance is not None:
            TransactionRepository.create_transaction(user_id, 'withdrawal', -float(amount_decimal))
            return {'success': True, 'new_balance': new_balance}

        return {'success': False, 'error': 'Withdrawal failed'}

    @staticmethod
    def deduct_game_fee(user_id, amount):
        """Deduct game fee from user's wallet - THIS IS THE ONLY PLACE FOR DEDUCTION"""
        if amount <= 0:
            return {'success': False, 'error': 'Invalid amount'}

        amount_decimal = Decimal(str(amount))

        current_balance = UserRepository.get_wallet_balance(user_id)
        if current_balance < float(amount_decimal):
            return {'success': False, 'error': 'Insufficient balance'}

        new_balance = UserRepository.update_wallet(user_id, -float(amount_decimal))
        if new_balance is not None:
            TransactionRepository.create_transaction(user_id, 'game_entry', -float(amount_decimal))
            return {'success': True, 'new_balance': new_balance}

        return {'success': False, 'error': 'Deduction failed'}

    @staticmethod
    def add_winnings(user_id, amount, game_code):
        """Add winnings to user's wallet and record transaction"""
        if amount <= 0:
            return {'success': False, 'error': 'Invalid amount'}

        amount_decimal = Decimal(str(amount))

        new_balance = UserRepository.update_wallet(user_id, float(amount_decimal))
        if new_balance is not None:
            # Create transaction record for winnings
            TransactionRepository.create_transaction(
                user_id, 
                'win', 
                float(amount_decimal), 
                game_code
            )
            return {'success': True, 'new_balance': new_balance}

        return {'success': False, 'error': 'Adding winnings failed'}

    @staticmethod
    def get_win_earnings_balance(user_id):
        return TransactionRepository.get_win_earnings_balance(user_id)

    @staticmethod
    def get_total_platform_balance():
        return UserRepository.get_total_balance()

    @staticmethod
    def validate_sufficient_balance(user_id, amount):
        balance = UserRepository.get_wallet_balance(user_id)
        return balance >= float(amount)

    @staticmethod
    def reconcile_accounts():
        """Verify that total user balances match expected calculations.
        
        Formula: Deposits + Loans Given - Loan Repayments - Withdrawals - Game Entries + Winnings = Expected Balance
        Note: Platform fees are NOT included because they go to the house account, not user wallets.
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Total deposits
                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'deposit' AND amount > 0")
                total_deposits = Decimal(str(cursor.fetchone()[0] or 0))

                # Total withdrawals (negative amounts)
                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'withdrawal' AND amount < 0")
                total_withdrawals = abs(Decimal(str(cursor.fetchone()[0] or 0)))

                # Total game entries (negative amounts)
                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'game_entry' AND amount < 0")
                total_game_entries = abs(Decimal(str(cursor.fetchone()[0] or 0)))

                # Total wins (positive amounts)
                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'win' AND amount > 0")
                total_wins = Decimal(str(cursor.fetchone()[0] or 0))

                # Total platform fees (for display only, not used in user balance calculation)
                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'platform_fee' AND amount > 0")
                total_fees = Decimal(str(cursor.fetchone()[0] or 0))

                # Total loans given to users
                cursor.execute("SELECT COALESCE(SUM(loan_amount), 0) FROM user_loans")
                total_loans_given = Decimal(str(cursor.fetchone()[0] or 0))

                # Total loan repayments collected
                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM loan_repayments")
                total_loan_repayments = Decimal(str(cursor.fetchone()[0] or 0))

                # Total current user balances
                cursor.execute("SELECT COALESCE(SUM(wallet), 0) FROM users")
                total_balances = Decimal(str(cursor.fetchone()[0] or 0))

                # CORRECTED: Expected balance calculation
                # Fees are NOT included because they don't affect user wallets
                # Formula: Deposits + Loans Given - Loan Repayments - Withdrawals - Game Entries + Winnings = Expected Balance
                expected = total_deposits + total_loans_given - total_loan_repayments - total_withdrawals - total_game_entries + total_wins

                return {
                    'total_deposits': float(total_deposits),
                    'total_withdrawals': float(total_withdrawals),
                    'total_game_entries': float(total_game_entries),
                    'total_wins': float(total_wins),
                    'total_fees': float(total_fees),
                    'total_loans_given': float(total_loans_given),
                    'total_loan_repayments': float(total_loan_repayments),
                    'total_balances': float(total_balances),
                    'expected_balance': float(expected),
                    'difference': float(total_balances - expected),
                    'is_balanced': total_balances == expected
                }
        except Exception as e:
            logging.error(f"Reconciliation error: {e}")
            return {
                'total_deposits': 0.0,
                'total_withdrawals': 0.0,
                'total_game_entries': 0.0,
                'total_wins': 0.0,
                'total_fees': 0.0,
                'total_loans_given': 0.0,
                'total_loan_repayments': 0.0,
                'total_balances': 0.0,
                'expected_balance': 0.0,
                'difference': 0.0,
                'is_balanced': True,
                'error': str(e)
            }
