#!/usr/bin/env python3
"""
Authentication utilities for CTF Platform
"""

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app

SECRET_KEY = 'ctf-platform-secret-key-2025'

def generate_jwt_token(student_id, student_name):
    """Generate JWT token for student"""
    payload = {
        'student_id': student_id,
        'student_name': student_name,
        'exp': datetime.utcnow() + timedelta(hours=24),  # 24 hour expiry
        'iat': datetime.utcnow()
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def decode_jwt_token(token):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401

        if not token:
            return jsonify({'error': 'Token missing'}), 401

        payload = decode_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Add student info to request context
        request.student_id = payload['student_id']
        request.student_name = payload['student_name']

        return f(*args, **kwargs)

    return decorated_function