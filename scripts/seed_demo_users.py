#!/usr/bin/env python3
"""Seed demo users (teacher_demo, student_demo, admin_demo) for S2.12. Idempotent: create or reset password."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.seed_demo import seed_demo_users, DEMO_PASSWORD


def seed():
    app = create_app()
    with app.app_context():
        seed_demo_users()
        print("Demo users seeded (idempotent): teacher_demo, student_demo, admin_demo / " + DEMO_PASSWORD)


if __name__ == "__main__":
    seed()
