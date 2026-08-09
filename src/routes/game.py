from flask import Blueprint, render_template, session, jsonify, request
from services.game_service import GameService
from services.wallet_service import WalletService
import logging

game_bp = Blueprint('game', __name__)

def mask_username(username):
    """Mask the last character of a username with 'X'"""
    if not username or username == 'N/A':
        return username
    if len(username) <= 1:
        return username
    return username[:-1] + 'X'

@game_bp.route("/")
def index():
    wallet_balance = 0.0
    if session.get('user_id'):
        wallet_balance = WalletService.get_balance(session['user_id'])

    # Welcome message stays with full username - NO CHANGE
    return render_template("user/index.html", wallet_balance=wallet_balance, session=session)

@game_bp.route("/play", methods=["POST"])
def play():
    user_id = session.get("user_id")
    username = session.get("username")

    if not user_id:
        return jsonify({"success": False, "error": "You must be logged in to play."})

    result = GameService.enqueue_player(user_id)

    if result['success']:
        logging.info(f"User {username} enrolled. New balance: Ksh. {result['new_balance']:.2f}")
        return jsonify({
            "success": True,
            "message": "Successfully enrolled in the next game!",
            "new_balance": result['new_balance']
        })
    else:
        return jsonify({"success": False, "error": result['error']})

@game_bp.route("/game_data")
def game_data():
    try:
        game_data = GameService.get_game_data()

        upcoming_data = None
        if game_data['upcoming']:
            upcoming_data = {
                "game_code": game_data['upcoming'].game_code,
                "timestamp": game_data['upcoming'].timestamp.strftime('%Y-%m-%d %H:%M:%S') if game_data['upcoming'].timestamp else "N/A",
                "status": game_data['upcoming'].status,
                "time_remaining": game_data.get('time_remaining', 0)
            }

        completed_data = []
        for game in game_data['completed']:
            completed_data.append({
                "game_code": game.game_code,
                "timestamp": game.timestamp.strftime('%Y-%m-%d %H:%M:%S') if game.timestamp else "N/A",
                "num_users": game.num_users,
                "total_amount": f"Ksh. {game.total_amount:.2f}",
                "winner": mask_username(game.winner or "N/A"),  # ← MASKED HERE
                "winner_amount": f"Ksh. {game.winner_amount:.2f}",
                "outcome_message": f"Winner: {mask_username(game.winner)}" if game.winner else "No winner"  # ← MASKED HERE
            })

        current_user_queued = False
        if session.get('user_id'):
            current_user_queued = GameService.is_user_queued(session['user_id'])

        return jsonify({
            "upcoming_game": upcoming_data or {"game_code": "N/A", "timestamp": "N/A", "status": "upcoming", "time_remaining": 0},
            "completed_games": completed_data,
            "current_user_queued": current_user_queued,
            "queue_count": game_data.get('queue_count', 0),
            "time_remaining": game_data.get('time_remaining', 0),
            "min_players": game_data.get('min_players', 10),
            "players_needed": game_data.get('players_needed', 10)
        })
    except Exception as e:
        logging.error(f"Error in game_data: {e}")
        return jsonify({
            "upcoming_game": {"game_code": "N/A", "timestamp": "N/A", "status": "upcoming", "time_remaining": 0},
            "completed_games": [],
            "current_user_queued": False,
            "queue_count": 0,
            "time_remaining": 0,
            "min_players": 10,
            "players_needed": 10
        }), 500

@game_bp.route("/api/game/status")
def game_status():
    return jsonify({'status': 'pending'})
