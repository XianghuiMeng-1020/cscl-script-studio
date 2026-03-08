"""Tests for CSCL Script API"""
import pytest
import json
import os
from app.db import db
from app.models import User, UserRole, CSCLScript
from datetime import datetime


def test_teacher_can_create_script(client, app, seed_users):
    """Test 1: Teacher can create script -> 200"""
    # Login as teacher
    login_resp = client.post(
        '/api/auth/login',
        json={'user_id': 'T001', 'password': 'teacher123'}
    )
    assert login_resp.status_code == 200
    
    # Create script
    resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'learning_objectives': ['Understand ethical issues'],
            'task_type': 'debate',
            'duration_minutes': 60,
            'generate_template': True
        }
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['success'] is True
    assert 'script' in data
    assert data['script']['title'] == 'Test Script'
    assert data['script']['status'] == 'draft'


def test_student_cannot_create_script(client, app, seed_users):
    """Test 2: Student cannot create script -> 403"""
    # Login as student
    login_resp = client.post(
        '/api/auth/login',
        json={'user_id': 'S001', 'password': 'student123'}
    )
    assert login_resp.status_code == 200
    
    # Try to create script
    resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics'
        }
    )
    assert resp.status_code == 403
    data = json.loads(resp.data)
    assert 'error' in data


def test_teacher_can_finalize_script(client, app, seed_users):
    """Test 3: Teacher can finalize script -> 200"""
    # Login as teacher
    login_resp = client.post(
        '/api/auth/login',
        json={'user_id': 'T001', 'password': 'teacher123'}
    )
    assert login_resp.status_code == 200
    
    # Create script
    create_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'debate',
            'duration_minutes': 60
        }
    )
    assert create_resp.status_code == 201
    script_id = json.loads(create_resp.data)['script']['id']
    
    # Finalize script
    resp = client.post(f'/api/cscl/scripts/{script_id}/finalize')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['success'] is True
    assert data['script']['status'] == 'final'


def test_teacher_can_export_script(client, app, seed_users):
    """Test 4: Teacher can export script -> 200 with full structure"""
    # Login as teacher
    login_resp = client.post(
        '/api/auth/login',
        json={'user_id': 'T001', 'password': 'teacher123'}
    )
    assert login_resp.status_code == 200
    
    # Create script with template
    create_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'debate',
            'duration_minutes': 60,
            'generate_template': True
        }
    )
    assert create_resp.status_code == 201
    script_id = json.loads(create_resp.data)['script']['id']
    
    # Export script
    resp = client.get(f'/api/cscl/scripts/{script_id}/export')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['success'] is True
    assert 'script' in data
    assert 'scenes' in data['script']
    assert 'roles' in data['script']
    assert len(data['script']['scenes']) > 0
    assert len(data['script']['roles']) > 0
    # Check scriptlets in scenes
    assert 'scriptlets' in data['script']['scenes'][0]


def test_student_cannot_export_script(client, app, seed_users):
    """Test 5: Student cannot export script -> 403"""
    # Login as student
    login_resp = client.post(
        '/api/auth/login',
        json={'user_id': 'S001', 'password': 'student123'}
    )
    assert login_resp.status_code == 200
    
    # Try to export (even if script exists)
    resp = client.get('/api/cscl/scripts/any-id/export')
    assert resp.status_code == 403
    data = json.loads(resp.data)
    assert 'error' in data
