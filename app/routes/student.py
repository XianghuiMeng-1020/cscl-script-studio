"""Student routes blueprint"""
from flask import Blueprint, render_template, redirect
from flask_login import current_user
from app.config import Config

student_bp = Blueprint('student', __name__)


@student_bp.route('/student')
def student_portal():
    """Student portal - redirect to /login if REQUIRE_LOGIN_FOR_STUDENT and not authenticated"""
    if Config.REQUIRE_LOGIN_FOR_STUDENT and not current_user.is_authenticated:
        return redirect('/login?next=/student')
    return render_template('student.html')
