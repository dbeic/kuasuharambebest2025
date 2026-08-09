import re

def validate_email(email):
    if not email or not isinstance(email, str):
        return False
    email = email.strip()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_username(username):
    if not username or not isinstance(username, str):
        return False
    username = username.strip()
    if len(username) < 3 or len(username) > 50:
        return False
    pattern = r'^[a-zA-Z0-9_.-]+$'
    return bool(re.match(pattern, username))

def validate_password(password):
    if not password or not isinstance(password, str):
        return False
    password = password.strip()
    if len(password) < 6:
        return False
    # At least one letter and one number (optional but recommended)
    # Basic check - at least 6 characters
    return True

def validate_amount(amount, min_amount=0, max_amount=None):
    try:
        if amount is None:
            return False
        amount = float(amount)
        if amount < min_amount:
            return False
        if max_amount and amount > max_amount:
            return False
        return True
    except (ValueError, TypeError):
        return False
