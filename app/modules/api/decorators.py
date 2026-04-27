from functools import wraps
from flask import request, jsonify, current_app
import os

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow disabling API temporarily if token is not set or empty
        system_token = os.getenv('API_TOKEN')
        
        if not system_token:
            return jsonify({
                "status": "error",
                "message": "API security not configured on server (Missing API_TOKEN)"
            }), 503

        # Check for X-API-TOKEN header
        request_token = request.headers.get('X-API-TOKEN')
        
        if not request_token or request_token != system_token:
            current_app.logger.warning(f"Unauthorized API access attempt from IP: {request.remote_addr}")
            return jsonify({
                "status": "error",
                "message": "Invalid or missing API Token"
            }), 401
            
        return f(*args, **kwargs)
    return decorated_function
