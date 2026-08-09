from datetime import datetime

class UserActivity:
    def __init__(self, id=None, timestamp=None, username=None, ip_address=None,
                 path=None, method=None, user_agent=None, referrer=None):
        self.id = id
        self.timestamp = timestamp
        self.username = username
        self.ip_address = ip_address
        self.path = path
        self.method = method
        self.user_agent = user_agent
        self.referrer = referrer
    
    @staticmethod
    def from_row(row):
        if not row:
            return None
        return UserActivity(
            id=row[0],
            timestamp=row[1],
            username=row[2],
            ip_address=row[3],
            path=row[4],
            method=row[5],
            user_agent=row[6],
            referrer=row[7]
        )

class VisitLog:
    def __init__(self, id=None, ip_address=None, user_agent=None, 
                 referrer=None, path=None, timestamp=None):
        self.id = id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.referrer = referrer
        self.path = path
        self.timestamp = timestamp
    
    @staticmethod
    def from_row(row):
        if not row:
            return None
        return VisitLog(
            id=row[0],
            ip_address=row[1],
            user_agent=row[2],
            referrer=row[3],
            path=row[4],
            timestamp=row[5]
        )
