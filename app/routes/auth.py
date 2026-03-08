"""Authentication routes"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user
from app.models import User, UserRole
from app.db import db
from app.auth import authenticate_user, authenticate_token, log_audit, login_required
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')
    token = data.get('token')  # For student token-based auth
    
    if not user_id and not token:
        return jsonify({'error': 'user_id/password or token required'}), 400
    
    user = None
    
    # Try password authentication (for teacher/admin)
    if user_id and password:
        user = authenticate_user(user_id, password)
        if user:
            login_user(user, remember=False)
            log_audit(
                'login_success',
                actor_id=user.id,
                role=user.role,
                status='success'
            )
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'role': user.role.value if user.role else None
                }
            }), 200
    
    # Try token authentication (for students)
    if token:
        user = authenticate_token(token)
        if user:
            login_user(user, remember=False)
            log_audit(
                'login_success',
                actor_id=user.id,
                role=user.role,
                status='success',
                meta={'method': 'token'}
            )
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'role': user.role.value if user.role else None
                }
            }), 200
    
    # Login failed
    log_audit(
        'login_failed',
        actor_id=user_id,
        status='failed',
        meta={'reason': 'invalid_credentials'}
    )
    return jsonify({'error': 'Invalid credentials'}), 401


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout endpoint"""
    user_id = current_user.id
    role = current_user.role
    
    logout_user()
    
    log_audit(
        'logout',
        actor_id=user_id,
        role=role,
        status='success'
    )
    
    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify({
        'id': current_user.id,
        'role': current_user.role.value if current_user.role else None
    }), 200
