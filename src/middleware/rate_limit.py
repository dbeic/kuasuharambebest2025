from flask import session, request

def rate_limit_key():
    if session.get('admin_id'):
        return f"admin_{session.get('admin_id')}"
    elif session.get('user_id'):
        return f"user_{session.get('user_id')}"
    else:
        return request.remote_addr
