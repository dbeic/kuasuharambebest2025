from flask import Blueprint, render_template, send_from_directory, session
from services.wallet_service import WalletService

pages_bp = Blueprint('pages', __name__)

@pages_bp.route("/offline")
def offline():
    # Get user's wallet balance for header display
    wallet_balance = 0.0
    if 'user_id' in session:
        wallet_balance = WalletService.get_balance(session['user_id'])
    
    return render_template("static/offline.html", wallet_balance=wallet_balance)

@pages_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@pages_bp.route('/service-worker.js')
def sw():
    return send_from_directory('static', 'service-worker.js')

@pages_bp.route("/privacy")
def privacy():
    # Get user's wallet balance for header display
    wallet_balance = 0.0
    if 'user_id' in session:
        wallet_balance = WalletService.get_balance(session['user_id'])
    
    return render_template("static/privacy.html", wallet_balance=wallet_balance)

@pages_bp.route("/terms")
def terms():
    # Get user's wallet balance for header display
    wallet_balance = 0.0
    if 'user_id' in session:
        wallet_balance = WalletService.get_balance(session['user_id'])
    
    return render_template("static/terms.html", wallet_balance=wallet_balance)

@pages_bp.route("/docs")
def docs():
    # Get user's wallet balance for header display
    wallet_balance = 0.0
    if 'user_id' in session:
        wallet_balance = WalletService.get_balance(session['user_id'])
    
    return render_template("static/docs.html", wallet_balance=wallet_balance)

@pages_bp.route('/robots.txt')
def robots_txt():
    return ("User-agent: *\nDisallow:\n", 200, {'Content-Type': 'text/plain'})
