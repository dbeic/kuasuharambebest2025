from flask import Blueprint, Response, stream_with_context, jsonify, session, request
from src.shared import get_db_connection
from src.services.game_service import GameService
from src.services.loan_service import LoanService
from src.utils.validators import validate_email, validate_username, validate_password, validate_amount
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
import time
import logging
import os
from datetime import datetime

api_bp = Blueprint('api', __name__)
limiter = Limiter(key_func=get_remote_address)

@api_bp.before_request
def check_production():
    if os.getenv('FLASK_ENV') == 'production' and request.path.startswith('/sim/'):
        return jsonify({'error': 'Simulation endpoints disabled in production'}), 404

@api_bp.route("/stream")
def stream():
    def event_stream():
        last_game_code = None
        last_status = None

        while True:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT game_code, status, timestamp, num_users, winner, winner_amount, outcome_message
                        FROM results
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """)
                    game = cursor.fetchone()

                    # Get queue count
                    queue_count = len(GameService.get_queue_players())

                    # Calculate time remaining for upcoming game
                    time_remaining = 0
                    try:
                        cursor.execute("""
                            SELECT timestamp FROM results
                            WHERE status = 'upcoming'
                            ORDER BY timestamp ASC LIMIT 1
                        """)
                        upcoming = cursor.fetchone()
                        if upcoming:
                            now = datetime.now()
                            diff = (upcoming[0] - now).total_seconds()
                            time_remaining = max(0, int(diff))
                    except Exception as e:
                        logging.error(f"Error calculating time remaining: {e}")

                    if game:
                        game_code = game[0]
                        status = game[1] if game[1] else "unknown"

                        # Detect status changes for sound triggers
                        if last_game_code != game_code or last_status != status:
                            event_type = "game_update"

                            if status == "in progress" and last_status != "in progress":
                                event_type = "game_start"
                            elif status == "completed" and last_status != "completed":
                                event_type = "game_end"

                                winner = game[4] if game[4] else None
                                if winner:
                                    event_type = "game_win"
                                else:
                                    event_type = "game_loss"

                            last_game_code = game_code
                            last_status = status

                            winner_amount = float(game[5]) if game[5] is not None else 0.0

                            data = {
                                "event_type": event_type,
                                "game_code": game_code,
                                "status": status,
                                "timestamp": game[2].strftime("%Y-%m-%d %H:%M:%S") if game[2] else "N/A",
                                "num_users": game[3] if isinstance(game[3], int) else 0,
                                "winner": game[4] if game[4] else "N/A",
                                "winner_amount": winner_amount,
                                "outcome_message": game[6] if isinstance(game[6], str) else "",
                                "queue_count": queue_count,
                                "time_remaining": time_remaining
                            }
                            yield f"data: {json.dumps(data)}\n\n"
                        else:
                            heartbeat_data = {
                                "event_type": "heartbeat",
                                "queue_count": queue_count,
                                "time_remaining": time_remaining
                            }
                            yield f"data: {json.dumps(heartbeat_data)}\n\n"
                time.sleep(1)

            except Exception as e:
                logging.error(f"Error in event stream: {e}")
                time.sleep(5)
                break

    return Response(stream_with_context(event_stream()), content_type="text/event-stream")

@api_bp.route("/api/queue_status")
def queue_status():
    """Get current queue status"""
    try:
        queued_players = GameService.get_queue_players()
        player_list = [player[1] for player in queued_players]
        return jsonify({
            'queue_count': len(queued_players),
            'queued_players': player_list,
            'min_players': 2,
            'players_needed': max(0, 2 - len(queued_players))
        })
    except Exception as e:
        logging.error(f"Error getting queue status: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route("/api/withdrawal_queue_status")
def withdrawal_queue_status():
    """Get withdrawal queue status for logged in user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        user_id = session['user_id']
        status = LoanService.get_withdrawal_availability(user_id)
        return jsonify(status)
    except Exception as e:
        logging.error(f"Error getting withdrawal queue status: {e}")
        return jsonify({'error': str(e)}), 500

# Simulation endpoints
@api_bp.route('/sim/register', methods=['POST'])
@limiter.limit("10 per minute, 100 per hour")
def sim_register():
    """Register a simulated user"""
    try:
        data = request.get_json()
        admin_key = os.getenv('ADMIN_API_KEY')
        if not admin_key or data.get('admin_key') != admin_key:
            return jsonify({'success': False, 'error': 'Invalid admin key'}), 401

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        initial_balance = data.get('initial_balance', 500.00)

        if not all([username, email, password]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        from src.repositories.user_repository import UserRepository
        from src.repositories.transaction_repository import TransactionRepository
        from werkzeug.security import generate_password_hash
        from src.services.loan_service import LoanService

        existing_user = UserRepository.get_by_username(username)
        if existing_user:
            return jsonify({
                'success': True,
                'exists': True,
                'user_id': existing_user.id,
                'message': 'User already exists'
            })

        existing_email = UserRepository.get_by_email(email)
        if existing_email:
            return jsonify({'success': False, 'error': 'Email already exists'}), 400

        hashed_password = generate_password_hash(password)
        user_id = UserRepository.create_user(email, username, hashed_password)

        if user_id:
            # Set initial balance if provided
            if initial_balance > 0:
                UserRepository.update_wallet(user_id, initial_balance)

            # Create loan for simulated user
            LoanService.create_loan_for_user(user_id)
            UserRepository.update_wallet(user_id, 200.00)

            # ============================================================
            # FIX: Record the loan as a deposit transaction
            # This ensures the loan is treated like real money
            # ============================================================
            TransactionRepository.create_transaction(user_id, 'deposit', 200.00)

            # Also record in real_money_deposits table
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO real_money_deposits (user_id, amount, is_used_for_withdrawal)
                    VALUES (%s, %s, FALSE)
                """, (user_id, 200.00))
                conn.commit()

            logging.info(f"Sim registration: Loan recorded as deposit for user {user_id}")

            return jsonify({
                'success': True,
                'user_id': user_id,
                'username': username,
                'initial_balance': initial_balance + 200.00,
                'loan_given': 200.00
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create user'}), 500

    except Exception as e:
        logging.error(f"Sim registration error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/sim/deposit', methods=['POST'])
@limiter.limit("20 per minute, 200 per hour")
def sim_deposit():
    try:
        data = request.get_json()
        admin_key = os.getenv('ADMIN_API_KEY')
        if not admin_key or data.get('admin_key') != admin_key:
            return jsonify({'success': False, 'error': 'Invalid admin key'}), 401

        username = data.get('username')
        amount = float(data.get('amount', 0))

        if not username or amount <= 0:
            return jsonify({'success': False, 'error': 'Invalid username or amount'}), 400

        from src.repositories.user_repository import UserRepository
        from src.models.transaction import Transaction
        from src.repositories.transaction_repository import TransactionRepository
        from datetime import datetime

        user = UserRepository.get_by_username(username)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        new_balance = UserRepository.update_wallet(user.id, amount)

        if new_balance is not None:
            transaction = Transaction(
                user_id=user.id,
                type='deposit',
                amount=amount,
                timestamp=datetime.now()
            )
            TransactionRepository.create(transaction)

            return jsonify({
                'success': True,
                'user_id': user.id,
                'username': username,
                'amount': amount,
                'new_balance': new_balance
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update wallet'}), 500

    except Exception as e:
        logging.error(f"Sim deposit error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/sim/withdraw', methods=['POST'])
@limiter.limit("10 per minute, 50 per hour")
def sim_withdraw():
    try:
        data = request.get_json()
        admin_key = os.getenv('ADMIN_API_KEY')
        if not admin_key or data.get('admin_key') != admin_key:
            return jsonify({'success': False, 'error': 'Invalid admin key'}), 401

        username = data.get('username')
        amount = float(data.get('amount', 0))

        if not username or amount <= 0:
            return jsonify({'success': False, 'error': 'Invalid username or amount'}), 400

        from src.repositories.user_repository import UserRepository
        from src.models.transaction import Transaction
        from src.repositories.transaction_repository import TransactionRepository
        from datetime import datetime

        user = UserRepository.get_by_username(username)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        current_balance = UserRepository.get_wallet_balance(user.id)
        if current_balance < amount:
            return jsonify({
                'success': False,
                'error': 'Insufficient balance',
                'current_balance': current_balance
            }), 400

        new_balance = UserRepository.update_wallet(user.id, -amount)

        if new_balance is not None:
            transaction = Transaction(
                user_id=user.id,
                type='withdrawal',
                amount=-amount,
                timestamp=datetime.now()
            )
            TransactionRepository.create(transaction)

            return jsonify({
                'success': True,
                'user_id': user.id,
                'username': username,
                'amount': amount,
                'new_balance': new_balance
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update wallet'}), 500

    except Exception as e:
        logging.error(f"Sim withdrawal error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/sim/play', methods=['POST'])
@limiter.limit("30 per minute, 300 per hour")
def sim_play():
    try:
        data = request.get_json()
        admin_key = os.getenv('ADMIN_API_KEY')
        if not admin_key or data.get('admin_key') != admin_key:
            return jsonify({'success': False, 'error': 'Invalid admin key'}), 401

        username = data.get('username')
        stake = float(data.get('stake', 0))

        if not username or stake <= 0:
            return jsonify({'success': False, 'error': 'Invalid username or stake'}), 400

        from src.repositories.user_repository import UserRepository
        from src.models.transaction import Transaction
        from src.repositories.transaction_repository import TransactionRepository
        from datetime import datetime
        import random

        user = UserRepository.get_by_username(username)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        current_balance = UserRepository.get_wallet_balance(user.id)
        if current_balance < stake:
            return jsonify({
                'success': False,
                'error': 'Insufficient balance',
                'current_balance': current_balance
            }), 400

        is_win = random.random() < 0.4
        win_multiplier = random.uniform(1.5, 3.0) if is_win else 0

        if is_win:
            win_amount = stake * win_multiplier
            net_change = win_amount - stake
        else:
            win_amount = 0
            net_change = -stake

        new_balance = UserRepository.update_wallet(user.id, net_change)

        if new_balance is not None:
            transaction = Transaction(
                user_id=user.id,
                type='game_play',
                amount=net_change,
                timestamp=datetime.now()
            )
            TransactionRepository.create(transaction)

            return jsonify({
                'success': True,
                'user_id': user.id,
                'username': username,
                'stake': stake,
                'outcome': 'win' if is_win else 'loss',
                'win_amount': win_amount,
                'net_change': net_change,
                'new_balance': new_balance
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update wallet'}), 500

    except Exception as e:
        logging.error(f"Sim play error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/sim/users/<username>', methods=['GET'])
@limiter.limit("30 per minute, 300 per hour")
def sim_get_user(username):
    try:
        admin_key = request.headers.get('X-API-Key')
        valid_admin_key = os.getenv('ADMIN_API_KEY')
        if not valid_admin_key or admin_key != valid_admin_key:
            return jsonify({'success': False, 'error': 'Invalid admin key'}), 401

        from src.repositories.user_repository import UserRepository

        user = UserRepository.get_by_username(username)

        if user:
            return jsonify({
                'success': True,
                'exists': True,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'wallet': user.wallet
            })
        else:
            return jsonify({
                'success': True,
                'exists': False,
                'message': 'User not found'
            })

    except Exception as e:
        logging.error(f"Sim get user error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
