import logging

class NotificationService:
    @staticmethod
    def notify_game_scheduled(game_code, game_time):
        logging.info(f"Game Event: game_scheduled - game_code='{game_code}', timestamp='{game_time.strftime('%Y-%m-%d %H:%M:%S')}'")
    
    @staticmethod
    def notify_game_started(game_code):
        logging.info(f"Game Event: game_started - game_code='{game_code}'")
    
    @staticmethod
    def notify_game_completed(game_code, winner, winner_amount, total_players, total_pool):
        logging.info(f"Game Event: game_completed - game_code='{game_code}', winner='{winner}', winner_amount={winner_amount}, total_players={total_players}, total_pool={total_pool}")
    
    @staticmethod
    def notify_game_canceled(game_code):
        logging.info(f"Game Event: game_canceled - game_code='{game_code}'")
    
    @staticmethod
    def notify_clients(event_type, data):
        logging.info(f"Game Event: {event_type} - {data}")
