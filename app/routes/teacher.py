"""Teacher routes blueprint"""
from flask import Blueprint, render_template, redirect
from flask_login import current_user
from app.config import Config

teacher_bp = Blueprint('teacher', __name__)


@teacher_bp.route('/')
def index():
    """Landing page with role selection"""
    return render_template('index.html')


@teacher_bp.route('/login')
def login_page():
    """Login page (role selection + username/password + Quick Demo)"""
    return render_template('login.html')


@teacher_bp.route('/teacher')
def teacher_dashboard():
    """Teacher dashboard - redirect to /login if REQUIRE_LOGIN_FOR_TEACHER and not authenticated"""
    if Config.REQUIRE_LOGIN_FOR_TEACHER and not current_user.is_authenticated:
        return redirect('/login?next=/teacher')
    return render_template('teacher.html')


@teacher_bp.route('/demo')
def demo_page():
    """Quick Demo - no login required, read-only demo data"""
    return render_template('demo.html')
