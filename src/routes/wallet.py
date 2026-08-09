from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from services.wallet_service import WalletService
from services.withdrawal_service import WithdrawalService
from services.deposit_service import DepositService
from services.auth_service import AuthService
from services.loan_service import LoanService
from repositories.withdrawal_repository import WithdrawalRepository
from middleware.auth import login_required
from datetime import datetime, timedelta
import logging

wallet_bp = Blueprint('wallet', __name__)

@wallet_bp.route('/wallet/balance')
def get_balance():
    """Get current wallet balance for the logged-in user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    balance = WalletService.get_balance(session['user_id'])
    return jsonify({'balance': balance})

@wallet_bp.route('/wallet/withdrawal_status')
def withdrawal_status():
    """Get comprehensive withdrawal availability status"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    status = LoanService.get_withdrawal_availability(session['user_id'])
    return jsonify(status)

@wallet_bp.route("/deposit", methods=["GET", "POST"])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    username = session.get('username')

    wallet_balance = WalletService.get_balance(user_id)

    if request.method == "POST":
        try:
            amount = float(request.form.get('amount', 0))

            if amount < 50:
                return render_template("user/deposit.html",
                    error="Minimum deposit amount is KES 50",
                    can_deposit=True,
                    wallet_balance=wallet_balance)

            if amount > 50000:
                return render_template("user/deposit.html",
                    error="Maximum deposit amount is KES 50,000",
                    can_deposit=True,
                    wallet_balance=wallet_balance)

            result = DepositService.create_deposit_request(user_id, username, amount)

            if result['success']:
                return redirect(url_for('wallet.deposit_voucher', voucher_code=result['voucher_code']))
            else:
                return render_template("user/deposit.html",
                    error=result['error'],
                    can_deposit=True,
                    wallet_balance=wallet_balance)

        except ValueError:
            return render_template("user/deposit.html",
                error="Invalid amount format",
                can_deposit=True,
                wallet_balance=wallet_balance)
        except Exception as e:
            logging.error(f"Deposit request error: {e}")
            return render_template("user/deposit.html",
                error="System error. Please try again.",
                can_deposit=True,
                wallet_balance=wallet_balance)

    return render_template("user/deposit.html",
        can_deposit=True,
        wallet_balance=wallet_balance)

@wallet_bp.route("/deposit_voucher/<voucher_code>")
def deposit_voucher(voucher_code):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    wallet_balance = WalletService.get_balance(user_id)

    deposit = DepositService.get_request_by_voucher(voucher_code)

    if not deposit or deposit.user_id != session['user_id']:
        return redirect(url_for('game.index', error="Voucher not found"))

    return render_template("user/deposit_voucher.html",
        deposit=deposit,
        wallet_balance=wallet_balance)

@wallet_bp.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    username = session.get('username')

    wallet_balance = WalletService.get_balance(user_id)

    # Get withdrawal availability
    withdrawal_status = LoanService.get_withdrawal_availability(user_id)
    loan_status = LoanService.get_loan_status(user_id)

    suspension = AuthService.check_user_suspension(user_id)
    if suspension:
        suspension_end = suspension[0]
        reason = suspension[1]
        return render_template("user/withdraw.html",
            error=f"Account suspended until {suspension_end}. Reason: {reason}",
            can_withdraw=False,
            wallet_balance=wallet_balance,
            withdrawal_status=withdrawal_status,
            loan_status=loan_status)

    # Get available balance for display
    available_balance = WalletService.get_win_earnings_balance(user_id)

    if request.method == "POST":
        try:
            amount = float(request.form.get('amount', 0))

            if amount < 100:
                return render_template("user/withdraw.html",
                    error="Minimum withdrawal amount is KES 100",
                    can_withdraw=True,
                    wallet_balance=wallet_balance,
                    available_balance=available_balance,
                    withdrawal_status=withdrawal_status,
                    loan_status=loan_status)

            if amount > 50000:
                return render_template("user/withdraw.html",
                    error="Maximum withdrawal amount is KES 50,000",
                    can_withdraw=True,
                    wallet_balance=wallet_balance,
                    available_balance=available_balance,
                    withdrawal_status=withdrawal_status,
                    loan_status=loan_status)

            # Check if user can withdraw
            if not withdrawal_status['can_withdraw']:
                return render_template("user/withdraw.html",
                    error="Withdrawal not available: " + ", ".join(withdrawal_status.get('reasons', ['Unknown reason'])),
                    available_balance=available_balance,
                    can_withdraw=False,
                    wallet_balance=wallet_balance,
                    withdrawal_status=withdrawal_status,
                    loan_status=loan_status)

            # Check balance
            if available_balance < amount:
                return render_template("user/withdraw.html",
                    error=f"Insufficient balance. Available: KES {available_balance:.2f}",
                    available_balance=available_balance,
                    can_withdraw=True,
                    wallet_balance=wallet_balance,
                    withdrawal_status=withdrawal_status,
                    loan_status=loan_status)

            # Check daily withdrawal limit
            today = datetime.now().date()
            daily_count = WithdrawalRepository.get_daily_withdrawal_count(user_id, today)
            if daily_count >= WithdrawalService.DAILY_LIMIT:
                return render_template("user/withdraw.html",
                    error=f"Daily withdrawal limit reached. You have made {daily_count} withdrawals today. Maximum is {WithdrawalService.DAILY_LIMIT} per day.",
                    available_balance=available_balance,
                    can_withdraw=False,
                    wallet_balance=wallet_balance,
                    daily_limit=WithdrawalService.DAILY_LIMIT,
                    daily_count=daily_count,
                    withdrawal_status=withdrawal_status,
                    loan_status=loan_status)

            # Add to withdrawal queue
            result = LoanService.add_to_withdrawal_queue(user_id, amount)

            if result['success']:
                return render_template("user/withdraw_success.html",
                    amount=amount,
                    queue_position=result['queue_position'],
                    estimated_payment=result.get('estimated_payment', 'Pending'),
                    wallet_balance=wallet_balance)
            else:
                return render_template("user/withdraw.html",
                    error=result.get('error', 'Withdrawal failed'),
                    available_balance=available_balance,
                    can_withdraw=True,
                    wallet_balance=wallet_balance,
                    withdrawal_status=withdrawal_status,
                    loan_status=loan_status)

        except ValueError:
            return render_template("user/withdraw.html",
                error="Invalid amount format",
                available_balance=available_balance,
                can_withdraw=True,
                wallet_balance=wallet_balance,
                withdrawal_status=withdrawal_status,
                loan_status=loan_status)
        except Exception as e:
            logging.error(f"Withdrawal error: {e}")
            return render_template("user/withdraw.html",
                error="System error. Please try again later.",
                available_balance=available_balance,
                can_withdraw=True,
                wallet_balance=wallet_balance,
                withdrawal_status=withdrawal_status,
                loan_status=loan_status)

    # GET request - display withdrawal form
    today = datetime.now().date()
    daily_count = WithdrawalRepository.get_daily_withdrawal_count(user_id, today)
    can_withdraw_again = daily_count < WithdrawalService.DAILY_LIMIT

    history = WithdrawalService.get_withdrawal_history(user_id, 1)
    last_withdrawal = history[0].request_time if history and len(history) > 0 else None

    return render_template("user/withdraw.html",
        available_balance=available_balance,
        can_withdraw=can_withdraw_again and withdrawal_status.get('can_withdraw', False),
        last_withdrawal=last_withdrawal,
        wallet_balance=wallet_balance,
        daily_limit=WithdrawalService.DAILY_LIMIT,
        daily_count=daily_count,
        withdrawal_status=withdrawal_status,
        loan_status=loan_status)

@wallet_bp.route("/withdrawal_receipt/<receipt_code>")
def withdrawal_receipt(receipt_code):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    wallet_balance = WalletService.get_balance(user_id)

    withdrawal = WithdrawalService.get_request_by_receipt(receipt_code)

    if not withdrawal or withdrawal.user_id != session['user_id']:
        return redirect(url_for('game.index', error="Receipt not found"))

    return render_template("user/withdrawal_receipt.html",
        withdrawal=withdrawal,
        wallet_balance=wallet_balance)
