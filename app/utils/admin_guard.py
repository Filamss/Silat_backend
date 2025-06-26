from flask import request, jsonify
import os
from functools import wraps

def require_admin_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        admin_key = os.getenv('ADMIN_API_KEY')

        if api_key and api_key == admin_key:
            return view_function(*args, **kwargs)
        else:
            return jsonify({"message": "Unauthorized: Admin access only"}), 403

    return decorated_function
