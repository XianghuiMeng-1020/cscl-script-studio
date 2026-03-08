"""Canonical demo user seed logic. Used at app startup (when no DATABASE_URL) and by scripts/seed_demo_users.py."""
from datetime import datetime

from app.db import db
from app.models import User, UserRole, CSCLScript, CSCLScene, CSCLRole, CSCLScriptlet, StudentGroup

DEMO_PASSWORD = "Demo@12345"
DEMO_USERS = [
    ("teacher_demo", "teacher"),
    ("student_demo", "student"),
    ("admin_demo", "admin"),
]

DEMO_SHARE_CODE = "DEMO"


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


def seed_demo_published_activity():
    """Create one published activity with share_code DEMO for student testing (idempotent)."""
    existing = CSCLScript.query.filter_by(share_code=DEMO_SHARE_CODE).first()
    if existing:
        return
    script = CSCLScript(
        title="Demo collaborative activity",
        topic="Introduction to collaborative learning",
        course_id="default-course",
        learning_objectives=["Share ideas", "Build on others' contributions"],
        task_type="structured_debate",
        duration_minutes=30,
        status="final",
        published_at=datetime.utcnow(),
        share_code=DEMO_SHARE_CODE,
        created_by="teacher_demo",
    )
    db.session.add(script)
    db.session.flush()
    scene = CSCLScene(
        script_id=script.id,
        order_index=0,
        scene_type="opening",
        purpose="Introduce the topic and your position.",
        transition_rule="Move to next when everyone has shared.",
    )
    db.session.add(scene)
    db.session.flush()
    role = CSCLRole(
        script_id=script.id,
        role_name="Participant",
        responsibilities=["Contribute one idea", "Respond to one peer"],
    )
    db.session.add(role)
    db.session.flush()
    scriptlet = CSCLScriptlet(
        scene_id=scene.id,
        role_id=role.id,
        prompt_text="Write a short statement of your initial position on the topic.",
        prompt_type="claim",
    )
    db.session.add(scriptlet)
    group = StudentGroup(script_id=script.id, group_name="Demo group")
    db.session.add(group)
    db.session.commit()
