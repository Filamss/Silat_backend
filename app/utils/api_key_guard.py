from flask import request, jsonify
import os

def require_api_key(view_function):
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        env_key = os.getenv('API_KEY')
        if api_key and api_key == env_key:
            return view_function(*args, **kwargs)
        else:
            return jsonify({"message": "Unauthorized: Invalid or missing API key"}), 401

    decorated_function.__name__ = view_function.__name__
    return decorated_function



