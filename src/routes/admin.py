from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from src.services.auth_service import AuthService
from src.services.wallet_service import WalletService
from src.services.game_service import GameService
from src.services.withdrawal_service import WithdrawalService
from src.services.deposit_service import DepositService
from src.repositories.user_repository import UserRepository
from src.repositories.activity_repository import ActivityRepository
from src.repositories.game_repository import GameRepository
from src.repositories.withdrawal_repository import WithdrawalRepository
from src.repositories.deposit_repository import DepositRepository
from src.repositories.transaction_repository import TransactionRepository
from src.middleware.auth import login_required
from src.shared import get_db_connection
from datetime import datetime
import logging

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin/dashboard")
@login_required(role='admin')
def dashboard():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users ORDER BY id ASC")
        users = cursor.fetchall()

        cursor.execute("SELECT * FROM user_activity ORDER BY timestamp DESC LIMIT 100")
        logs = cursor.fetchall()

        user_suspensions = {}
        cursor.execute("SELECT user_id FROM user_suspensions WHERE suspension_end > CURRENT_TIMESTAMP")
        for row in cursor.fetchall():
            user_suspensions[row[0]] = True

        total_balance = UserRepository.get_total_balance()
        active_games = GameRepository.get_active_games_count()
        completed_games = GameRepository.get_completed_games_count()

        # Calculate total platform profit
        cursor.execute("SELECT COALESCE(SUM(deduction), 0) FROM results WHERE status = 'completed'")
        result = cursor.fetchone()
        total_profit = float(result[0]) if result else 0.0

        cursor.execute("SELECT username FROM allowed_users")
        allowed_users = cursor.fetchall()

        # Get game queue count
        cursor.execute("SELECT COUNT(*) FROM game_queue")
        game_queue_count = cursor.fetchone()[0] or 0

    return render_template(
        "admin/dashboard.html",
        users=users,
        logs=logs,
        total_balance=total_balance,
        total_profit=total_profit,
        active_games=active_games,
        completed_games=completed_games,
        allowed_users=allowed_users,
        user_suspensions=user_suspensions,
        game_queue_count=game_queue_count,
        error=request.args.get("error"),
        message=request.args.get("message")
    )

@admin_bp.route("/admin/update_wallet", methods=["POST"])
@login_required(role='admin')
def update_wallet():
    user_id = request.form.get("user_id")
    amount = request.form.get("amount")
    action = request.form.get("action")

    try:
        amount = float(amount)
        if action not in ["deposit", "withdraw"]:
            return redirect(url_for("admin.dashboard", error="Invalid action."))

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return redirect(url_for("admin.dashboard", error="User not found."))

            if action == "deposit":
                WalletService.deposit(int(user_id), amount, session.get('admin_id'))
            elif action == "withdraw":
                wallet_balance = WalletService.get_balance(int(user_id))
                if wallet_balance < amount:
                    return redirect(url_for("admin.dashboard", error="Insufficient balance for withdrawal."))
                WalletService.withdraw(int(user_id), amount, session.get('admin_id'))

        return redirect(url_for("admin.dashboard", message="Wallet updated successfully."))

    except ValueError:
        return redirect(url_for("admin.dashboard", error="Invalid amount. Please enter a valid number."))

@admin_bp.route("/admin/add_allowed_user", methods=["POST"])
@login_required(role='admin')
def add_allowed_user():
    username = request.form.get("allowed_username")

    if not username:
        return redirect(url_for("admin.dashboard", error="Username is required."))

    success = UserRepository.add_allowed_username(username)

    if success:
        return redirect(url_for("admin.dashboard", message="Allowed username added successfully."))
    else:
        return redirect(url_for("admin.dashboard", error="Failed to add allowed username."))

@admin_bp.route("/admin/visitor_log")
@login_required(role='admin')
def visitor_log():
    logs = ActivityRepository.get_visit_logs(100)
    return render_template("admin/visitor_log.html", logs=logs)

@admin_bp.route("/admin/withdrawals")
@login_required(role='admin')
def withdrawals():
    withdrawals = WithdrawalRepository.get_all_requests(100)
    pending_count = len(WithdrawalRepository.get_pending_requests())
    return render_template("admin/withdrawals.html", withdrawals=withdrawals, pending_count=pending_count)

@admin_bp.route("/admin/process_withdrawal", methods=["POST"])
@login_required(role='admin')
def process_withdrawal():
    withdrawal_id = request.form.get("withdrawal_id")
    action = request.form.get("action")
    admin_notes = request.form.get("admin_notes", "")

    if not withdrawal_id or not action:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        # Get admin_id from session
        admin_id = session.get('admin_id')
        if not admin_id:
            return jsonify({"error": "Admin not authenticated"}), 401

        if action == 'approve':
            result = WithdrawalService.approve_withdrawal(int(withdrawal_id), admin_id, admin_notes)
        elif action == 'reject':
            result = WithdrawalService.reject_withdrawal(int(withdrawal_id), admin_id, admin_notes)
        else:
            return jsonify({"error": "Invalid action"}), 400

        if result['success']:
            return jsonify({"success": True, "message": f"Withdrawal {action}ed"})
        else:
            return jsonify({"error": result['error']}), 400

    except Exception as e:
        logging.error(f"Process withdrawal error: {e}", exc_info=True)
        return jsonify({"error": f"System error: {str(e)}"}), 500

@admin_bp.route("/admin/process_deposit", methods=["POST"])
@login_required(role='admin')
def process_deposit():
    deposit_id = request.form.get("deposit_id")
    action = request.form.get("action")
    admin_notes = request.form.get("admin_notes", "")

    if not deposit_id or not action:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        admin_id = session.get('admin_id')
        if not admin_id:
            return jsonify({"error": "Admin not authenticated"}), 401

        if action == 'approve':
            result = DepositService.approve_deposit(int(deposit_id), admin_id, admin_notes)
        elif action == 'reject':
            result = DepositService.reject_deposit(int(deposit_id), admin_id, admin_notes)
        else:
            return jsonify({"error": "Invalid action"}), 400

        if result['success']:
            return jsonify({"success": True, "message": f"Deposit {action}ed"})
        else:
            return jsonify({"error": result['error']}), 400

    except Exception as e:
        logging.error(f"Process deposit error: {e}")
        return jsonify({"error": "System error"}), 500

@admin_bp.route("/cashbook")
@login_required(role='admin')
def cashbook():
    try:
        total_gross_profit = GameRepository.get_total_profit()
        total_user_balance = UserRepository.get_total_balance()
        total_profitable_games = GameRepository.get_completed_games_count()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT game_code, timestamp, num_users, total_amount, deduction
                FROM results
                WHERE status = 'completed' AND deduction > 0
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            recent_profits = cursor.fetchall()

        cashbook_data = {
            "total_gross_profit": total_gross_profit,
            "total_user_balance": total_user_balance,
            "total_profitable_games": total_profitable_games,
            "recent_profits": recent_profits
        }

        return render_template("admin/cashbook.html", data=cashbook_data)

    except Exception as e:
        logging.error(f"Cashbook error: {e}")
        cashbook_data = {
            "total_gross_profit": 0.0,
            "total_user_balance": 0.0,
            "total_profitable_games": 0,
            "recent_profits": []
        }
        return render_template("admin/cashbook.html", data=cashbook_data)

@admin_bp.route("/admin/reconcile")
@login_required(role='admin')
def reconcile():
    """Admin endpoint to check financial reconciliation"""
    try:
        result = WalletService.reconcile_accounts()
        return render_template("admin/reconcile.html", result=result)
    except Exception as e:
        logging.error(f"Reconciliation error: {e}")
        return render_template("admin/reconcile.html",
            result={
                'total_deposits': 0.0,
                'total_withdrawals': 0.0,
                'total_game_entries': 0.0,
                'total_wins': 0.0,
                'total_fees': 0.0,
                'total_balances': 0.0,
                'expected_balance': 0.0,
                'difference': 0.0,
                'is_balanced': True,
                'error': str(e)
            }
        )

@admin_bp.route("/admin/user_details/<int:user_id>")
@login_required(role='admin')
def user_details(user_id):
    # Verify admin has access (already handled by login_required)
    user = UserRepository.get_by_id(user_id)
    if user:
        return jsonify({
            'username': user.username,
            'balance': user.wallet
        })
    return jsonify({'error': 'User not found'}), 404

@admin_bp.route("/admin/remove_allowed_user", methods=["POST"])
@login_required(role='admin')
def remove_allowed_user():
    username = request.form.get("username")
    if username:
        success = UserRepository.remove_allowed_username(username)
        if success:
            return jsonify({"success": True})
    return jsonify({"success": False}), 400
