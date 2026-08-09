from datetime import datetime

class Transaction:
    TRANSACTION_TYPES = ['deposit', 'withdrawal', 'game_entry', 'win', 'platform_fee', 'game_play']

    def __init__(self, id=None, user_id=None, type=None, amount=None,
                 timestamp=None, game_code=None):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.amount = float(amount) if amount else 0.0
        self.timestamp = timestamp
        self.game_code = game_code

    @staticmethod
    def from_row(row):
        if not row:
            return None
        return Transaction(
            id=row[0],
            user_id=row[1],
            type=row[2],
            amount=row[3],
            timestamp=row[4],
            game_code=row[5] if len(row) > 5 else None
        )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'amount': self.amount,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
            'game_code': self.game_code
        }
