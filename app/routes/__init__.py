"""Routes package"""
from app.routes.teacher import teacher_bp
from app.routes.student import student_bp
from app.routes.api import api_bp
from app.routes.auth import auth_bp

__all__ = ['teacher_bp', 'student_bp', 'api_bp', 'auth_bp']
