import secrets
import string
from datetime import datetime

def generate_game_code():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def format_currency(amount):
    return f"KES {amount:.2f}"

def generate_otp():
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def truncate_string(text, max_length=50):
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def generate_secure_token(length=32):
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def generate_secure_key(length=32):
    """Generate a cryptographically secure random key"""
    return secrets.token_hex(length)
