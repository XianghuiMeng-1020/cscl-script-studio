#!/usr/bin/env python3
"""Seed 20 teacher users for concurrent load test. Idempotent. Run with same env as app (e.g. .venv)."""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.db import db
from app.models import User, UserRole

PASSWORD = "LoadTest@20"

def seed():
    app = create_app()
    with app.app_context():
        # Ensure tables exist (when using file SQLite)
        db.create_all()
        for i in range(1, 21):
            uid = f"teacher_load_{i}"
            user = User.query.filter_by(id=uid).first()
            if user:
                user.role = UserRole.TEACHER
                user.set_password(PASSWORD)
                db.session.add(user)
            else:
                u = User(id=uid, role=UserRole.TEACHER, created_at=datetime.utcnow())
                u.set_password(PASSWORD)
                db.session.add(u)
        db.session.commit()
        print("Seeded 20 users: teacher_load_1 .. teacher_load_20")
        print("Password:", PASSWORD)

if __name__ == "__main__":
    seed()
