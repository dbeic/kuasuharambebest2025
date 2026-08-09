from datetime import datetime

class UserLoan:
    """Represents a user's loan status"""
    def __init__(self, id=None, user_id=None, loan_amount=200.0, repaid_amount=0.0,
                 remaining_balance=200.0, is_fully_repaid=False, created_at=None,
                 updated_at=None):
        self.id = id
        self.user_id = user_id
        self.loan_amount = float(loan_amount) if loan_amount else 200.0
        self.repaid_amount = float(repaid_amount) if repaid_amount else 0.0
        self.remaining_balance = float(remaining_balance) if remaining_balance else 200.0
        self.is_fully_repaid = is_fully_repaid
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def from_row(row):
        if not row:
            return None
        return UserLoan(
            id=row[0],
            user_id=row[1],
            loan_amount=row[2],
            repaid_amount=row[3],
            remaining_balance=row[4],
            is_fully_repaid=row[5],
            created_at=row[6],
            updated_at=row[7]
        )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'loan_amount': self.loan_amount,
            'repaid_amount': self.repaid_amount,
            'remaining_balance': self.remaining_balance,
            'is_fully_repaid': self.is_fully_repaid,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class WithdrawalQueue:
    """Represents a user's position in the withdrawal queue"""
    def __init__(self, id=None, user_id=None, amount=None, queue_position=None,
                 status='pending', priority=0, created_at=None, processed_at=None,
                 estimated_payment_date=None):
        self.id = id
        self.user_id = user_id
        self.amount = float(amount) if amount else 0.0
        self.queue_position = queue_position
        self.status = status  # 'pending', 'processing', 'completed', 'cancelled'
        self.priority = priority  # Higher = higher priority
        self.created_at = created_at
        self.processed_at = processed_at
        self.estimated_payment_date = estimated_payment_date

    @staticmethod
    def from_row(row):
        if not row:
            return None
        return WithdrawalQueue(
            id=row[0],
            user_id=row[1],
            amount=row[2],
            queue_position=row[3],
            status=row[4],
            priority=row[5],
            created_at=row[6],
            processed_at=row[7],
            estimated_payment_date=row[8]
        )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'queue_position': self.queue_position,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'processed_at': self.processed_at.strftime('%Y-%m-%d %H:%M:%S') if self.processed_at else None,
            'estimated_payment_date': self.estimated_payment_date.strftime('%Y-%m-%d %H:%M:%S') if self.estimated_payment_date else None
        }

class LoanRepayment:
    """Tracks individual loan repayments"""
    def __init__(self, id=None, user_id=None, game_code=None, amount=None,
                 repayment_type='automatic', win_earnings_before=None,
                 win_earnings_after=None, created_at=None):
        self.id = id
        self.user_id = user_id
        self.game_code = game_code
        self.amount = float(amount) if amount else 0.0
        self.repayment_type = repayment_type
        self.win_earnings_before = float(win_earnings_before) if win_earnings_before else 0.0
        self.win_earnings_after = float(win_earnings_after) if win_earnings_after else 0.0
        self.created_at = created_at

    @staticmethod
    def from_row(row):
        if not row:
            return None
        return LoanRepayment(
            id=row[0],
            user_id=row[1],
            game_code=row[2],
            amount=row[3],
            repayment_type=row[4],
            win_earnings_before=row[5],
            win_earnings_after=row[6],
            created_at=row[7]
        )

class HouseAccount:
    """Tracks platform house account"""
    def __init__(self, id=None, total_balance=0.0, available_balance=0.0,
                 pending_withdrawals=0.0, total_deposits=0.0, total_fees=0.0,
                 total_loan_repayments=0.0, updated_at=None):
        self.id = id
        self.total_balance = float(total_balance) if total_balance else 0.0
        self.available_balance = float(available_balance) if available_balance else 0.0
        self.pending_withdrawals = float(pending_withdrawals) if pending_withdrawals else 0.0
        self.total_deposits = float(total_deposits) if total_deposits else 0.0
        self.total_fees = float(total_fees) if total_fees else 0.0
        self.total_loan_repayments = float(total_loan_repayments) if total_loan_repayments else 0.0
        self.updated_at = updated_at

    @staticmethod
    def from_row(row):
        if not row:
            return None
        return HouseAccount(
            id=row[0],
            total_balance=row[1],
            available_balance=row[2],
            pending_withdrawals=row[3],
            total_deposits=row[4],
            total_fees=row[5],
            total_loan_repayments=row[6],
            updated_at=row[7]
        )
