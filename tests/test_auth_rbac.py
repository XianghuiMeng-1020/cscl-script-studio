"""Tests for authentication and RBAC"""
import pytest
import json
import os
from app.db import db
from app.models import User, UserRole, Submission, Assignment, AuditLog
from datetime import datetime


def test_unauthorized_teacher_write_endpoint(client, app, seed_test_data):
    """Test 1: 未登录调用教师写接口 -> 401"""
    # Create submission in JSON file (endpoint uses JSON storage)
    from app.config import Config
    from app.utils import save_json
    
    submissions = [{
        'id': 'SUB001',
        'assignment_id': 'A001',
        'student_id': 'S001',
        'student_name': 'Test Student',
        'content': 'Test content',
        'status': 'pending',
        'submitted_at': datetime.utcnow().isoformat()
    }]
    
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    save_json(Config.SUBMISSIONS_FILE, submissions)
    
    response = client.put(
        '/api/submissions/SUB001/feedback',
        json={'feedback': 'Test feedback', 'rubric_scores': {}}
    )
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Authentication required' in data['error'] or 'authentication' in data['error'].lower()


def test_student_cannot_access_teacher_endpoint(client, app, seed_users):
    """Test 2: student 调用教师写接口 -> 403"""
    # Create submission in JSON file
    from app.config import Config
    from app.utils import save_json
    
    submissions = [{
        'id': 'SUB001',
        'assignment_id': 'A001',
        'student_id': 'S001',
        'student_name': 'Test Student',
        'content': 'Test content',
        'status': 'pending',
        'submitted_at': datetime.utcnow().isoformat()
    }]
    
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    save_json(Config.SUBMISSIONS_FILE, submissions)
    
    # Login as student
    login_response = client.post(
        '/api/auth/login',
        json={'user_id': 'S001', 'password': 'student123'}
    )
    assert login_response.status_code == 200
    
    # Try to access teacher endpoint
    response = client.put(
        '/api/submissions/SUB001/feedback',
        json={'feedback': 'Test feedback', 'rubric_scores': {}}
    )
    assert response.status_code == 403
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Insufficient permissions' in data['error'] or 'permissions' in str(data).lower()


def test_student_cannot_access_other_student_resource(client, app, seed_users, seed_test_data):
    """Test 3: student 访问他人 submission -> 403"""
    # Create submission data in JSON file for stats endpoint
    from app.config import Config
    from app.utils import save_json
    
    submissions = [
        {
            'id': 'SUB001',
            'assignment_id': 'A001',
            'student_id': 'S001',
            'student_name': 'Student 1',
            'content': 'Test content',
            'status': 'pending',
            'submitted_at': datetime.utcnow().isoformat()
        },
        {
            'id': 'SUB002',
            'assignment_id': 'A001',
            'student_id': 'S002',
            'student_name': 'Student 2',
            'content': 'Test content 2',
            'status': 'pending',
            'submitted_at': datetime.utcnow().isoformat()
        }
    ]
    
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    save_json(Config.SUBMISSIONS_FILE, submissions)
    
    # Login as S001
    login_response = client.post(
        '/api/auth/login',
        json={'user_id': 'S001', 'password': 'student123'}
    )
    assert login_response.status_code == 200
    
    # Try to access S002's stats
    response = client.get('/api/stats/student/S002')
    assert response.status_code == 403
    data = json.loads(response.data)
    assert 'error' in data
    assert 'cannot access other students' in data['error'].lower() or 'access denied' in data['error'].lower()


def test_teacher_can_access_teacher_endpoint(client, app, seed_users):
    """Test 4: teacher 登录后调用教师写接口 -> 200"""
    # Create submission in JSON file
    from app.config import Config
    from app.utils import save_json
    
    submissions = [{
        'id': 'SUB001',
        'assignment_id': 'A001',
        'student_id': 'S001',
        'student_name': 'Test Student',
        'content': 'Test content',
        'status': 'pending',
        'submitted_at': datetime.utcnow().isoformat()
    }]
    
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    save_json(Config.SUBMISSIONS_FILE, submissions)
    
    # Login as teacher
    login_response = client.post(
        '/api/auth/login',
        json={'user_id': 'T001', 'password': 'teacher123'}
    )
    assert login_response.status_code == 200
    
    # Access teacher endpoint
    response = client.put(
        '/api/submissions/SUB001/feedback',
        json={'feedback': 'Test feedback', 'rubric_scores': {}}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data


def test_login_failure_logs_audit(app, client):
    """Test 5: login 失败时写入 audit_logs（status=failed）"""
    with app.app_context():
        # Try to login with wrong credentials
        response = client.post(
            '/api/auth/login',
            json={'user_id': 'T999', 'password': 'wrongpassword'}
        )
        assert response.status_code == 401
        
        # Check audit log
        audit = AuditLog.query.filter_by(event_type='login_failed').first()
        assert audit is not None
        assert audit.status == 'failed'
        assert audit.actor_id == 'T999'


def test_login_success_logs_audit(app, client, seed_users):
    """Test login success logs audit"""
    with app.app_context():
        response = client.post(
            '/api/auth/login',
            json={'user_id': 'T001', 'password': 'teacher123'}
        )
        assert response.status_code == 200
        
        audit = AuditLog.query.filter_by(event_type='login_success').first()
        assert audit is not None
        assert audit.status == 'success'
        assert audit.actor_id == 'T001'


def test_student_can_access_own_resource(client, app, seed_users):
    """Test student can access own submission"""
    # Create submission in JSON file
    from app.config import Config
    from app.utils import save_json
    
    submissions = [{
        'id': 'SUB001',
        'assignment_id': 'A001',
        'student_id': 'S001',
        'student_name': 'Test Student',
        'content': 'Test content',
        'status': 'pending',
        'submitted_at': datetime.utcnow().isoformat()
    }]
    
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    save_json(Config.SUBMISSIONS_FILE, submissions)
    
    # Login as student
    login_response = client.post(
        '/api/auth/login',
        json={'user_id': 'S001', 'password': 'student123'}
    )
    assert login_response.status_code == 200
    
    # Access own stats
    response = client.get('/api/stats/student/S001')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_submissions' in data
