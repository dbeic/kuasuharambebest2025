from repositories.game_repository import GameRepository
from repositories.user_repository import UserRepository
from repositories.transaction_repository import TransactionRepository
from services.wallet_service import WalletService
from services.notification_service import NotificationService
from services.loan_service import LoanService
from datetime import datetime, timedelta
import secrets
import logging
from decimal import Decimal, ROUND_HALF_UP

class GameService:
    GAME_STAKE = Decimal('10.00')
    PLATFORM_FEE_PERCENTAGE = Decimal('0.10')
    GAME_INTERVAL_SECONDS = 30
    MIN_PLAYERS = 2

    @staticmethod
    def schedule_next_game():
        upcoming = GameRepository.get_upcoming_game()
        in_progress = GameRepository.get_in_progress_game()

        if not upcoming and not in_progress:
            game_code = GameRepository.generate_game_code()
            game_time = datetime.now() + timedelta(seconds=GameService.GAME_INTERVAL_SECONDS)
            GameRepository.create_upcoming_game(game_code, game_time)
            NotificationService.notify_game_scheduled(game_code, game_time)
            logging.info(f"New game scheduled: {game_code} at {game_time}")
            return True
        return False

    @staticmethod
    def start_pending_game():
        next_game = GameRepository.get_upcoming_game()

        if next_game and next_game.timestamp:
            now = datetime.now()
            time_remaining = (next_game.timestamp - now).total_seconds()

            if now >= next_game.timestamp:
                players = GameRepository.get_queued_players()
                if len(players) >= GameService.MIN_PLAYERS:
                    GameRepository.update_game_status(next_game.game_code, 'in progress')
                    NotificationService.notify_game_started(next_game.game_code)
                    logging.info(f"Game started: {next_game.game_code} with {len(players)} players")
                    return next_game.game_code
                else:
                    new_time = datetime.now() + timedelta(seconds=GameService.GAME_INTERVAL_SECONDS)
                    GameRepository.reschedule_game(next_game.game_code, new_time)
                    logging.info(f"Game {next_game.game_code} rescheduled due to insufficient players ({len(players)}/{GameService.MIN_PLAYERS})")
                    return None
        return None

    @staticmethod
    def process_active_game():
        game = GameRepository.get_in_progress_game()

        if not game:
            return None

        logging.info(f"Processing game: {game.game_code}")

        players = GameRepository.get_queued_players()
        logging.info(f"Found {len(players)} players in queue")

        if len(players) >= GameService.MIN_PLAYERS:
            success = GameService._process_game_round(players, game.game_code)
            if not success:
                GameRepository.cancel_game(game.game_code, 'Game processing failed')
                logging.error(f"Game {game.game_code} processing failed")
        else:
            new_time = datetime.now() + timedelta(seconds=GameService.GAME_INTERVAL_SECONDS)
            GameRepository.reschedule_game(game.game_code, new_time)
            GameRepository.update_game_status(game.game_code, 'upcoming')
            logging.info(f"Game {game.game_code} rescheduled: not enough players ({len(players)}/{GameService.MIN_PLAYERS})")

        return game.game_code

    @staticmethod
    def _process_game_round(players, game_code):
        if not players or len(players) < GameService.MIN_PLAYERS:
            logging.error(f"Game {game_code}: Insufficient players")
            return False

        from shared import get_db_connection

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("BEGIN")

                valid_players = []
                for player in players:
                    user_id, username, wallet = player
                    cursor.execute("SELECT wallet FROM users WHERE id = %s FOR UPDATE", (user_id,))
                    current_wallet = cursor.fetchone()

                    if current_wallet and Decimal(str(current_wallet[0])) >= GameService.GAME_STAKE:
                        valid_players.append((user_id, username, Decimal(str(current_wallet[0]))))
                    else:
                        logging.warning(f"User {username} no longer has sufficient balance")

                if len(valid_players) < GameService.MIN_PLAYERS:
                    logging.error(f"Game {game_code}: Not enough valid players ({len(valid_players)})")
                    cursor.execute("ROLLBACK")
                    return False

                stake_amount = GameService.GAME_STAKE
                num_players = len(valid_players)
                total_pool = Decimal(str(num_players)) * stake_amount
                platform_fee = (total_pool * GameService.PLATFORM_FEE_PERCENTAGE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                winner_amount = (total_pool - platform_fee).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                logging.info(f"Game {game_code}: {num_players} players, pool={total_pool}, fee={platform_fee}, winner={winner_amount}")

                winner = secrets.choice(valid_players)
                winner_id, winner_username = winner[0], winner[1]

                logging.info(f"Game {game_code}: Winner selected - {winner_username}")

                cursor.execute(
                    "UPDATE users SET wallet = wallet + %s WHERE id = %s",
                    (float(winner_amount), winner_id)
                )

                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, timestamp, game_code) VALUES (%s, %s, %s, %s, %s)",
                    (winner_id, "win", float(winner_amount), datetime.now(), game_code)
                )

                cursor.execute(
                    "INSERT INTO win_earnings (user_id, game_code, amount, earned_at, is_withdrawn) VALUES (%s, %s, %s, %s, %s)",
                    (winner_id, game_code, float(winner_amount), datetime.now(), False)
                )
                logging.info(f"Added win_earning for user {winner_id}: {winner_amount}")

                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, timestamp, game_code) VALUES (%s, %s, %s, %s, %s)",
                    (1, "platform_fee", float(platform_fee), datetime.now(), game_code)
                )

                outcome_message = f"Game {game_code}: {num_players} players. Winner: {winner_username} won KES {winner_amount:.2f}"
                cursor.execute(
                    """
                    UPDATE results SET
                        status = 'completed',
                        winner = %s,
                        winner_amount = %s,
                        num_users = %s,
                        total_amount = %s,
                        deduction = %s,
                        outcome_message = %s,
                        timestamp = %s
                    WHERE game_code = %s
                    """,
                    (winner_username, float(winner_amount), num_players, float(total_pool), float(platform_fee),
                     outcome_message, datetime.now(), game_code)
                )

                user_ids = [player[0] for player in valid_players]
                if user_ids:
                    placeholders = ','.join(['%s'] * len(user_ids))
                    cursor.execute(f"DELETE FROM game_queue WHERE user_id IN ({placeholders})", user_ids)

                conn.commit()

                # ============================================================
                # CRITICAL: Check for automatic loan repayment for winner
                # ============================================================
                LoanService.check_and_process_automatic_repayment(winner_id, game_code)

                # Also check all other players who had money deducted
                for player in valid_players:
                    if player[0] != winner_id:
                        # Check if their win_earnings might have crossed threshold
                        LoanService.check_and_process_automatic_repayment(player[0], game_code)

                NotificationService.notify_game_completed(game_code, winner_username, float(winner_amount), num_players, float(total_pool))

                logging.info(f"Game {game_code} completed successfully with loan checks")
                return True

        except Exception as e:
            logging.error(f"Error processing game {game_code}: {str(e)}")
            try:
                if 'conn' in locals():
                    conn.rollback()
            except:
                pass
            return False

    @staticmethod
    def enqueue_player(user_id):
        if GameRepository.is_in_queue(user_id):
            return {'success': False, 'error': 'Already enrolled in current game!'}

        if not WalletService.validate_sufficient_balance(user_id, GameService.GAME_STAKE):
            balance = WalletService.get_balance(user_id)
            return {'success': False, 'error': f"Insufficient funds! Your balance: Ksh. {balance:.2f}"}

        deduction_result = WalletService.deduct_game_fee(user_id, GameService.GAME_STAKE)
        if not deduction_result['success']:
            return {'success': False, 'error': 'Transaction failed. Please try again.'}

        GameRepository.add_to_queue(user_id)

        return {'success': True, 'message': 'Successfully enrolled in the next game!', 'new_balance': deduction_result['new_balance']}

    @staticmethod
    def get_game_data():
        upcoming = GameRepository.get_upcoming_game()
        in_progress = GameRepository.get_in_progress_game()
        completed = GameRepository.get_completed_games(100)

        queued_players = GameRepository.get_queued_players()
        queue_count = len(queued_players)
        player_list = [player[1] for player in queued_players]

        time_remaining = 0
        if upcoming and upcoming.timestamp:
            time_remaining = max(0, int((upcoming.timestamp - datetime.now()).total_seconds()))

        return {
            'upcoming': upcoming,
            'in_progress': in_progress,
            'completed': completed,
            'queue_count': queue_count,
            'queued_players': player_list,
            'time_remaining': time_remaining,
            'min_players': GameService.MIN_PLAYERS,
            'players_needed': max(0, GameService.MIN_PLAYERS - queue_count)
        }

    @staticmethod
    def get_game_stats():
        return {
            'active_games': GameRepository.get_active_games_count(),
            'completed_games': GameRepository.get_completed_games_count(),
            'total_profit': GameRepository.get_total_profit()
        }

    @staticmethod
    def is_user_queued(user_id):
        return GameRepository.is_in_queue(user_id)

    @staticmethod
    def get_queue_players():
        return GameRepository.get_queued_players()
