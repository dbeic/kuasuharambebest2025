from .auth import auth_bp
from .game import game_bp
from .wallet import wallet_bp
from .admin import admin_bp
from .api import api_bp
from .static_pages import pages_bp

__all__ = [
    'auth_bp',
    'game_bp', 
    'wallet_bp',
    'admin_bp',
    'api_bp',
    'pages_bp'
]
