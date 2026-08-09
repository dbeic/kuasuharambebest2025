from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, id=None, email=None, username=None, hashed_password=None, wallet=0.0):
        self.id = id
        self.email = email
        self.username = username
        self.hashed_password = hashed_password
        self.wallet = float(wallet) if wallet else 0.0

    @staticmethod
    def from_row(row):
        if not row:
            return None
        return User(
            id=row[0],
            email=row[1],
            username=row[2],
            hashed_password=row[3],
            wallet=row[4]
        )

    def set_password(self, password):
        """Set password using scrypt hashing"""
        self.hashed_password = generate_password_hash(password.strip(), method='scrypt')

    def check_password(self, password):
        """Verify password against stored hash"""
        if not self.hashed_password or not password:
            return False
        return check_password_hash(self.hashed_password, password.strip())

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'wallet': self.wallet
        }
