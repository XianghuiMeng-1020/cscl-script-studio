"""Canonical demo user seed logic. Used at app startup (when no DATABASE_URL) and by scripts/seed_demo_users.py."""
from datetime import datetime

from app.db import db
from app.models import User, UserRole

DEMO_PASSWORD = "Demo@12345"
DEMO_USERS = [
    ("teacher_demo", "teacher"),
    ("student_demo", "student"),
    ("admin_demo", "admin"),
]


def seed_demo_users():
    """Create or update demo users (idempotent). Must be called within an app context."""
    for user_id, role_val in DEMO_USERS:
        user = User.query.filter_by(id=user_id).first()
        role_enum = (
            UserRole.TEACHER
            if role_val == "teacher"
            else (UserRole.ADMIN if role_val == "admin" else UserRole.STUDENT)
        )
        if user:
            user.role = role_enum
            user.set_password(DEMO_PASSWORD)
            db.session.add(user)
        else:
            new_user = User(id=user_id, role=role_enum, created_at=datetime.utcnow())
            new_user.set_password(DEMO_PASSWORD)
            db.session.add(new_user)
    db.session.commit()
