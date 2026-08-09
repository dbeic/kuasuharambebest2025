class Admin:
    def __init__(self, id=None, username=None, hashed_password=None, role='admin', created_at=None):
        self.id = id
        self.username = username
        self.hashed_password = hashed_password
        self.role = role
        self.created_at = created_at
    
    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row[0],
            username=row[1],
            hashed_password=row[2],
            role=row[3] if len(row) > 3 else 'admin'
        )
    
    def set_password(self, password):
        """Set password using scrypt hashing"""
        from werkzeug.security import generate_password_hash
        self.hashed_password = generate_password_hash(password.strip(), method='scrypt')
    
    def check_password(self, password):
        """Verify password against stored hash"""
        from werkzeug.security import check_password_hash
        if not self.hashed_password or not password:
            return False
        return check_password_hash(self.hashed_password, password.strip())
