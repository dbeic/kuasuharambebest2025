from datetime import datetime

class Game:
    def __init__(self, id=None, game_code=None, timestamp=None, num_users=0, 
                 total_amount=0.0, deduction=0.0, winner=None, winner_amount=0.0,
                 outcome_message=None, status='upcoming'):
        self.id = id
        self.game_code = game_code
        self.timestamp = timestamp
        self.num_users = num_users if num_users else 0
        self.total_amount = float(total_amount) if total_amount else 0.0
        self.deduction = float(deduction) if deduction else 0.0
        self.winner = winner
        self.winner_amount = float(winner_amount) if winner_amount else 0.0
        self.outcome_message = outcome_message
        self.status = status
    
    @staticmethod
    def from_row(row):
        if not row:
            return None
        return Game(
            id=row[0],
            game_code=row[1],
            timestamp=row[2],
            num_users=row[3],
            total_amount=row[4],
            deduction=row[5],
            winner=row[6],
            winner_amount=row[7],
            outcome_message=row[8],
            status=row[9]
        )
    
    def to_dict(self):
        return {
            'id': self.id,
            'game_code': self.game_code,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
            'num_users': self.num_users,
            'total_amount': self.total_amount,
            'deduction': self.deduction,
            'winner': self.winner,
            'winner_amount': self.winner_amount,
            'outcome_message': self.outcome_message,
            'status': self.status
        }

class GameQueue:
    def __init__(self, id=None, user_id=None, timestamp=None):
        self.id = id
        self.user_id = user_id
        self.timestamp = timestamp
    
    @staticmethod
    def from_row(row):
        if not row:
            return None
        return GameQueue(
            id=row[0],
            user_id=row[1],
            timestamp=row[2]
        )
