from datetime import datetime, timedelta

class ReceiptOTP:
    def __init__(self, id=None, order_id=None, order_type=None, otp_code=None,
                 expires_at=None, verified_at=None, verification_attempts=0,
                 created_at=None):
        self.id = id
        self.order_id = order_id
        self.order_type = order_type  # 'game' or 'withdrawal'
        self.otp_code = otp_code
        self.expires_at = expires_at
        self.verified_at = verified_at
        self.verification_attempts = verification_attempts
        self.created_at = created_at or datetime.now()
    
    @staticmethod
    def from_row(row):
        if not row:
            return None
        return ReceiptOTP(
            id=row[0],
            order_id=row[1],
            order_type=row[2],
            otp_code=row[3],
            expires_at=row[4],
            verified_at=row[5],
            verification_attempts=row[6],
            created_at=row[7]
        )
    
    def is_expired(self):
        return datetime.now() > self.expires_at
    
    def is_verified(self):
        return self.verified_at is not None
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_type': self.order_type,
            'otp_code': self.otp_code,
            'expires_at': self.expires_at.strftime('%Y-%m-%d %H:%M:%S') if self.expires_at else None,
            'verified_at': self.verified_at.strftime('%Y-%m-%d %H:%M:%S') if self.verified_at else None,
            'verification_attempts': self.verification_attempts,
            'is_expired': self.is_expired(),
            'is_verified': self.is_verified()
        }
