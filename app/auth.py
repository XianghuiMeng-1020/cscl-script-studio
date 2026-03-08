"""Authentication and authorization utilities"""
from functools import wraps
from flask import jsonify, request, current_app
from flask_login import current_user
from app.models import User, UserRole, AuditLog
from app.db import db
from datetime import datetime, timedelta
import secrets


def log_audit(event_type, actor_id=None, role=None, target_id=None, status='success', meta=None):
    """Log audit event"""
    try:
        from flask import current_app
        # Only log if DB storage is enabled
        if not current_app.config.get('USE_DB_STORAGE', False):
            return
        
        audit = AuditLog(
            event_type=event_type,
            actor_id=actor_id,
            role=role,
            target_id=target_id,
            status=status,
            meta_json=meta
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        try:
            current_app.logger.error(f"Failed to log audit event: {e}")
        except:
            pass
        db.session.rollback()


def login_required(f):
    """Decorator to require login. 401 -> 请先登录 (frontend: common.error.login)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_role = current_user.role.value if current_user.role else None
            if user_role not in allowed_roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'code': 'PERMISSION_DENIED',
                    'required_roles': list(allowed_roles),
                    'user_role': user_role
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def student_resource_required(f):
    """Decorator to ensure student can only access their own resources"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # If user is teacher/admin, allow access
        if current_user.role in [UserRole.TEACHER, UserRole.ADMIN]:
            return f(*args, **kwargs)
        
        # If user is student, check resource ownership
        if current_user.role == UserRole.STUDENT:
            # Check if student_id is in kwargs or request args
            resource_student_id = kwargs.get('student_id') or request.args.get('student_id')
            
            # For submission endpoints, check submission ownership
            submission_id = kwargs.get('submission_id')
            if submission_id:
                from app.models import Submission
                submission = Submission.query.get(submission_id)
                if submission and submission.student_id != current_user.id:
                    log_audit(
                        'access_denied',
                        actor_id=current_user.id,
                        role=current_user.role,
                        target_id=submission_id,
                        status='failed',
                        meta={'reason': 'student_accessing_others_resource'}
                    )
                    return jsonify({'error': 'Access denied: cannot access other students\' resources'}), 403
            
            # Check direct student_id parameter
            if resource_student_id and resource_student_id != current_user.id:
                log_audit(
                    'access_denied',
                    actor_id=current_user.id,
                    role=current_user.role,
                    target_id=resource_student_id,
                    status='failed',
                    meta={'reason': 'student_accessing_others_resource'}
                )
                return jsonify({'error': 'Access denied: cannot access other students\' resources'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def authenticate_user(user_id, password):
    """Authenticate user by user_id and password"""
    user = User.query.filter_by(id=user_id).first()
    if user and user.check_password(password):
        return user
    return None


def authenticate_token(token):
    """Authenticate user by token (for students)"""
    user = User.query.filter_by(token=token).first()
    if user:
        # Check token expiration
        if user.token_expires_at and user.token_expires_at < datetime.utcnow():
            return None
        return user
    return None


def generate_student_token(user_id, expires_hours=24):
    """Generate one-time token for student"""
    user = User.query.get(user_id)
    if not user:
        return None
    
    token = secrets.token_urlsafe(32)
    user.token = token
    user.token_expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    
    try:
        db.session.commit()
        return token
    except Exception:
        db.session.rollback()
        return None
