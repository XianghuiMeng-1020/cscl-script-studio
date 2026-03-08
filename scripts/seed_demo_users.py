#!/usr/bin/env python3
"""Seed demo users (teacher_demo, student_demo, admin_demo) for S2.12. Idempotent: create or reset password."""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.db import db
from app.models import User, UserRole
from werkzeug.security import generate_password_hash

# S2.12 fixed demo accounts (username = id for login)
DEMO_PASSWORD = "Demo@12345"
DEMO_USERS = [
    ("teacher_demo", "teacher"),
    ("student_demo", "student"),
    ("admin_demo", "admin"),
]


def seed():
    app = create_app()
    with app.app_context():
        for user_id, role_val in DEMO_USERS:
            user = User.query.filter_by(id=user_id).first()
            role_enum = UserRole.TEACHER if role_val == "teacher" else (UserRole.ADMIN if role_val == "admin" else UserRole.STUDENT)
            if user:
                user.role = role_enum
                user.set_password(DEMO_PASSWORD)
                db.session.add(user)
            else:
                new_user = User(id=user_id, role=role_enum, created_at=datetime.utcnow())
                new_user.set_password(DEMO_PASSWORD)
                db.session.add(new_user)
        db.session.commit()
        print("Demo users seeded (idempotent): teacher_demo, student_demo, admin_demo / " + DEMO_PASSWORD)


if __name__ == "__main__":
    seed()
