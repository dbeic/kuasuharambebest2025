from datetime import datetime

class WithdrawalRequest:
    STATUSES = ['pending', 'approved', 'rejected', 'completed']
    
    def __init__(self, id=None, user_id=None, username=None, requested_amount=None,
                 withdrawal_fee=None, net_amount=None, status='pending', 
                 request_time=None, processed_time=None, processed_by=None,
                 admin_notes=None, receipt_code=None, email=None):
        self.id = id
        self.user_id = user_id
        self.username = username
        self.requested_amount = float(requested_amount) if requested_amount else 0.0
        self.withdrawal_fee = float(withdrawal_fee) if withdrawal_fee else 0.0
        self.net_amount = float(net_amount) if net_amount else 0.0
        self.status = status
        self.request_time = request_time
        self.processed_time = processed_time
        self.processed_by = processed_by
        self.admin_notes = admin_notes
        self.receipt_code = receipt_code
        self.email = email
    
    @staticmethod
    def from_row(row):
        if not row:
            return None
        # Handle variable row length (with or without email)
        if len(row) > 12:
            return WithdrawalRequest(
                id=row[0],
                user_id=row[1],
                username=row[2],
                requested_amount=row[3],
                withdrawal_fee=row[4],
                net_amount=row[5],
                status=row[6],
                request_time=row[7],
                processed_time=row[8],
                processed_by=row[9],
                admin_notes=row[10],
                receipt_code=row[11],
                email=row[12] if len(row) > 12 else None
            )
        else:
            return WithdrawalRequest(
                id=row[0],
                user_id=row[1],
                username=row[2],
                requested_amount=row[3],
                withdrawal_fee=row[4],
                net_amount=row[5],
                status=row[6],
                request_time=row[7],
                processed_time=row[8],
                processed_by=row[9],
                admin_notes=row[10],
                receipt_code=row[11] if len(row) > 11 else None
            )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'requested_amount': self.requested_amount,
            'withdrawal_fee': self.withdrawal_fee,
            'net_amount': self.net_amount,
            'status': self.status,
            'request_time': self.request_time.strftime('%Y-%m-%d %H:%M:%S') if self.request_time else None,
            'receipt_code': self.receipt_code
        }

class WithdrawalLimit:
    def __init__(self, user_id=None, last_withdrawal_time=None, 
                 daily_attempts=0, last_attempt_time=None):
        self.user_id = user_id
        self.last_withdrawal_time = last_withdrawal_time
        self.daily_attempts = daily_attempts
        self.last_attempt_time = last_attempt_time

class WithdrawalFee:
    def __init__(self, id=None, min_amount=None, max_amount=None, 
                 fee_amount=0, fee_percentage=0, is_active=True):
        self.id = id
        self.min_amount = float(min_amount) if min_amount else 0.0
        self.max_amount = float(max_amount) if max_amount else float('inf')
        self.fee_amount = float(fee_amount) if fee_amount else 0.0
        self.fee_percentage = float(fee_percentage) if fee_percentage else 0.0
        self.is_active = is_active
    
    def calculate_fee(self, amount):
        if self.fee_amount > 0:
            return self.fee_amount
        if self.fee_percentage > 0:
            return amount * (self.fee_percentage / 100)
        return 0
