from datetime import datetime

class DepositRequest:
    STATUSES = ['pending', 'completed', 'rejected']
    
    def __init__(self, id=None, user_id=None, username=None, amount=None,
                 voucher_code=None, status='pending', request_time=None,
                 processed_time=None, processed_by=None, admin_notes=None):
        self.id = id
        self.user_id = user_id
        self.username = username
        self.amount = float(amount) if amount else 0.0
        self.voucher_code = voucher_code
        self.status = status
        self.request_time = request_time
        self.processed_time = processed_time
        self.processed_by = processed_by
        self.admin_notes = admin_notes
    
    @staticmethod
    def from_row(row):
        if not row:
            return None
        return DepositRequest(
            id=row[0],
            user_id=row[1],
            username=row[2],
            amount=row[3],
            voucher_code=row[4],
            status=row[5],
            request_time=row[6],
            processed_time=row[7],
            processed_by=row[8],
            admin_notes=row[9] if len(row) > 9 else None
        )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'amount': self.amount,
            'voucher_code': self.voucher_code,
            'status': self.status,
            'request_time': self.request_time.strftime('%Y-%m-%d %H:%M:%S') if self.request_time else None
        }
