"""Pytest configuration and shared fixtures"""
import pytest
import os
import tempfile
import shutil
from app import create_app
from app.db import db
from app.models import User, UserRole, Assignment, Submission
from datetime import datetime


@pytest.fixture(scope='function')
def app():
    """Create test app with isolated database"""
    # Set environment variables before creating app
    os.environ['USE_DB_STORAGE'] = 'true'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest'
    os.environ['TESTING'] = 'true'
    os.environ['LLM_PROVIDER'] = 'mock'  # Use mock provider for tests
    os.environ['SPEC_VALIDATE_PUBLIC'] = 'true'  # Spec validation API callable without auth in tests
    
    # Reload config to pick up env vars
    import importlib
    import app.config
    importlib.reload(app.config)
    
    # Create app instance - this will call init_db which binds db to app
    app_instance = create_app()
    app_instance.config['TESTING'] = True
    app_instance.config['USE_DB_STORAGE'] = True
    app_instance.config['DATABASE_URL'] = 'sqlite:///:memory:'
    app_instance.config['SECRET_KEY'] = 'test-secret-key-for-pytest'
    app_instance.config['SPEC_VALIDATE_PUBLIC'] = True  # Allow spec/validate without auth in tests
    
    # Ensure database is initialized
    # init_db was called in create_app, so db should be bound
    # But we need to create tables in app context
    with app_instance.app_context():
        # Create all tables
        db.create_all()
        yield app_instance
        # Clean up
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Provide database session"""
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def init_db(app):
    """Initialize database tables (already done in app fixture, but provided for clarity)"""
    with app.app_context():
        db.create_all()
        yield
        db.drop_all()


@pytest.fixture
def seed_users(app):
    """Seed test users: T001 (teacher), S001/S002 (students), admin. Idempotent."""
    with app.app_context():
        def get_or_create(uid, role, pw):
            u = db.session.get(User, uid)
            if u is None:
                u = User(id=uid, role=role)
                u.set_password(pw)
                db.session.add(u)
            return u

        teacher = get_or_create('T001', UserRole.TEACHER, 'teacher123')
        student1 = get_or_create('S001', UserRole.STUDENT, 'student123')
        student2 = get_or_create('S002', UserRole.STUDENT, 'student123')
        admin = get_or_create('ADMIN001', UserRole.ADMIN, 'admin123')
        db.session.commit()

        yield {
            'teacher': teacher,
            'student1': student1,
            'student2': student2,
            'admin': admin
        }


@pytest.fixture
def seed_test_data(app, seed_users):
    """Seed test data: assignments and submissions"""
    with app.app_context():
        # Create assignment
        assignment = Assignment(
            id='A001',
            title='Test Assignment',
            description='Test assignment description',
            created_at=datetime.utcnow()
        )
        db.session.add(assignment)
        
        # Create submission for S001
        submission1 = Submission(
            id='SUB001',
            assignment_id='A001',
            student_id='S001',
            student_name='Test Student 1',
            content='Test submission content',
            created_at=datetime.utcnow()
        )
        db.session.add(submission1)
        
        # Create submission for S002
        submission2 = Submission(
            id='SUB002',
            assignment_id='A001',
            student_id='S002',
            student_name='Test Student 2',
            content='Test submission content 2',
            created_at=datetime.utcnow()
        )
        db.session.add(submission2)
        
        db.session.commit()
        
        yield {
            'assignment': assignment,
            'submission1': submission1,
            'submission2': submission2
        }
