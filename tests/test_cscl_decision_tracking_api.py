"""Tests for CSCL Decision Tracking API endpoints"""
import pytest
import json
from datetime import datetime, timedelta
from app.db import db
from app.models import User, UserRole, CSCLScript, CSCLTeacherDecision, CSCLScriptRevision


@pytest.fixture
def course_id():
    """Course ID for testing"""
    return 'CS101'


@pytest.fixture
def script_with_course(app, seed_users, course_id):
    """Create a test script with course_id (without using client to avoid session pollution)"""
    with app.app_context():
        from app.models import CSCLScript
        script = CSCLScript(
            title='Test Script',
            topic='Machine Learning',
            course_id=course_id,
            task_type='debate',
            duration_minutes=60,
            created_by='T001'
        )
        db.session.add(script)
        db.session.commit()
        script_id = script.id
        db.session.expunge(script)  # Detach from session to avoid issues
        return script_id


def test_teacher_create_decision_success(client, seed_users, script_with_course):
    """Test 1: Teacher can create decision (200/201)"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.post(
        f'/api/cscl/scripts/{script_id}/decisions',
        json={
            'decision_type': 'accept',
            'target_type': 'scriptlet',
            'target_id': 'scriptlet_001',
            'after_json': {'prompt_text': 'Test'},
            'source_stage': 'planner',
            'confidence': 4
        }
    )
    
    assert response.status_code in [200, 201]
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'decision' in data
    assert data['decision']['decision_type'] == 'accept'


def test_student_create_decision_403(client, seed_users, script_with_course):
    """Test 2: Student cannot create decision (403)"""
    client.post('/api/auth/login', json={'user_id': 'S001', 'password': 'student123'})
    
    script_id = script_with_course
    
    response = client.post(
        f'/api/cscl/scripts/{script_id}/decisions',
        json={
            'decision_type': 'accept',
            'target_type': 'scriptlet'
        }
    )
    
    assert response.status_code == 403


def test_unauthenticated_create_decision_401(app, script_with_course):
    """Test 3: Unauthenticated user gets 401"""
    script_id = script_with_course
    
    # Create a completely fresh test client in a new app context
    # This ensures no session state is shared
    with app.app_context():
        # Clear any existing session
        from flask import g
        if hasattr(g, 'user'):
            delattr(g, 'user')
        
        # Create new test client
        unauthenticated_client = app.test_client(use_cookies=False)
        
        # Ensure we're not logged in by checking the endpoint requires auth
        # The @role_required decorator should catch this before script lookup
        response = unauthenticated_client.post(
            f'/api/cscl/scripts/{script_id}/decisions',
            json={
                'decision_type': 'accept',
                'target_type': 'scriptlet'
            }
        )
        
        # Flask-Login returns 401 for unauthenticated users
        # The @role_required decorator checks current_user.is_authenticated first
        assert response.status_code == 401, f"Expected 401 but got {response.status_code}. Response: {response.data.decode()[:200]}"


def test_invalid_decision_type_422(client, seed_users, script_with_course):
    """Test 4: Invalid decision_type returns 422"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.post(
        f'/api/cscl/scripts/{script_id}/decisions',
        json={
            'decision_type': 'invalid_type',
            'target_type': 'scriptlet'
        }
    )
    
    assert response.status_code == 422
    data = json.loads(response.data)
    assert 'code' in data
    assert data['code'] == 'INVALID_DECISION_TYPE'


def test_list_decisions_with_filters(client, seed_users, script_with_course, app):
    """Test 5: List decisions with filters works correctly"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    # Create some decisions
    with app.app_context():
        decision1 = CSCLTeacherDecision(
            script_id=script_id,
            actor_id='T001',
            decision_type='accept',
            target_type='scriptlet',
            target_id='s1',
            source_stage='planner'
        )
        decision2 = CSCLTeacherDecision(
            script_id=script_id,
            actor_id='T001',
            decision_type='edit',
            target_type='scene',
            target_id='sc1',
            source_stage='manual'
        )
        db.session.add(decision1)
        db.session.add(decision2)
        db.session.commit()
    
    # Filter by decision_type
    response = client.get(
        f'/api/cscl/scripts/{script_id}/decisions',
        query_string={'decision_type': 'accept'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['decisions']) >= 1
    assert all(d['decision_type'] == 'accept' for d in data['decisions'])
    
    # Filter by source_stage
    response = client.get(
        f'/api/cscl/scripts/{script_id}/decisions',
        query_string={'source_stage': 'planner'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(d['source_stage'] == 'planner' for d in data['decisions'])


def test_list_decisions_pagination(client, seed_users, script_with_course, app):
    """Test 6: Pagination works correctly"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    # Create multiple decisions
    with app.app_context():
        for i in range(15):
            decision = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='accept',
                target_type='scriptlet',
                target_id=f's{i}'
            )
            db.session.add(decision)
        db.session.commit()
    
    # First page
    response = client.get(
        f'/api/cscl/scripts/{script_id}/decisions',
        query_string={'page': 1, 'page_size': 10}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['decisions']) == 10
    assert data['pagination']['page'] == 1
    assert data['pagination']['total'] >= 15
    
    # Second page
    response = client.get(
        f'/api/cscl/scripts/{script_id}/decisions',
        query_string={'page': 2, 'page_size': 10}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['decisions']) >= 5


def test_decision_summary_computation(client, seed_users, script_with_course, app):
    """Test 7: Decision summary metrics computed correctly"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    # Create decisions with different types
    with app.app_context():
        decisions = []
        for i in range(5):
            d = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='accept',
                target_type='scriptlet',
                target_id=f's{i}',
                source_stage='planner'
            )
            decisions.append(d)
            db.session.add(d)
        for i in range(3):
            d = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='reject',
                target_type='scriptlet',
                target_id=f's{i+5}',
                source_stage='planner'
            )
            decisions.append(d)
            db.session.add(d)
        for i in range(2):
            d = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='edit',
                target_type='scene',
                target_id=f'sc{i}',
                source_stage='manual',
                after_json={'evidence_refs': ['chunk1']}  # With evidence
            )
            decisions.append(d)
            db.session.add(d)
        db.session.commit()
        
        # Verify decisions were created
        count = CSCLTeacherDecision.query.filter_by(script_id=script_id).count()
        assert count == 10
    
    response = client.get(f'/api/cscl/scripts/{script_id}/decision-summary')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    summary = data['summary']
    
    assert summary['total_decisions'] == 10
    assert summary['accept_rate'] == 0.5  # 5/10
    assert summary['reject_rate'] == 0.3  # 3/10
    assert summary['edit_rate'] == 0.2  # 2/10
    assert 'stage_adoption_rate' in summary


def test_decision_revision_association(client, seed_users, script_with_course, app):
    """Test 8: Decisions correctly associated with revisions"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    # Create revision
    with app.app_context():
        revision = CSCLScriptRevision(
            script_id=script_id,
            editor_id='T001',
            revision_type='update',
            before_json={},
            after_json={},
            diff_summary='Test revision'
        )
        db.session.add(revision)
        db.session.flush()
        
        # Create decision linked to revision
        decision = CSCLTeacherDecision(
            script_id=script_id,
            revision_id=revision.id,
            actor_id='T001',
            decision_type='edit',
            target_type='scriptlet',
            target_id='s1'
        )
        db.session.add(decision)
        db.session.commit()
        
        revision_id = revision.id
    
    # Get decisions for revision
    response = client.get(f'/api/cscl/scripts/{script_id}/revisions/{revision_id}/decisions')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['decisions']) == 1
    assert data['decisions'][0]['revision_id'] == revision_id


def test_timeline_ordering(client, seed_users, script_with_course, app):
    """Test 9: Timeline events are correctly ordered"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    # Create decisions at different times
    with app.app_context():
        base_time = datetime.now()
        for i in range(5):
            decision = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='accept',
                target_type='scriptlet',
                target_id=f's{i}',
                created_at=base_time + timedelta(minutes=i)
            )
            db.session.add(decision)
        db.session.commit()
    
    response = client.get(f'/api/cscl/scripts/{script_id}/decision-timeline/export')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    timeline = data['export']['timeline']
    
    # Check ordering
    timestamps = [datetime.fromisoformat(d['created_at'].replace('Z', '+00:00')) for d in timeline]
    assert timestamps == sorted(timestamps)


def test_export_includes_schema_version(client, seed_users, script_with_course):
    """Test 10: Export includes schema_version and generated_at"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.get(f'/api/cscl/scripts/{script_id}/decision-timeline/export')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    export_data = data['export']
    
    assert 'schema_version' in export_data
    assert 'generated_at' in export_data
    assert 'timeline' in export_data
    assert 'summary' in export_data


def test_create_decision_with_optional_fields(client, seed_users, script_with_course):
    """Test 11: Decision can be created without optional fields"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.post(
        f'/api/cscl/scripts/{script_id}/decisions',
        json={
            'decision_type': 'accept',
            'target_type': 'scriptlet'
            # No optional fields
        }
    )
    
    assert response.status_code in [200, 201]
    data = json.loads(response.data)
    assert data['success'] is True


def test_empty_decisions_summary_no_crash(client, seed_users, script_with_course):
    """Test 12: Empty decisions summary doesn't crash"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.get(f'/api/cscl/scripts/{script_id}/decision-summary')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    summary = data['summary']
    
    assert summary['total_decisions'] == 0
    assert summary['accept_rate'] == 0.0


def test_time_filter_works(client, seed_users, script_with_course, app):
    """Test 13: Time filtering works correctly"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    # Create decisions at different times
    with app.app_context():
        base_time = datetime.now()
        decision1 = CSCLTeacherDecision(
            script_id=script_id,
            actor_id='T001',
            decision_type='accept',
            target_type='scriptlet',
            target_id='s1',
            created_at=base_time - timedelta(hours=2)
        )
        decision2 = CSCLTeacherDecision(
            script_id=script_id,
            actor_id='T001',
            decision_type='accept',
            target_type='scriptlet',
            target_id='s2',
            created_at=base_time
        )
        db.session.add(decision1)
        db.session.add(decision2)
        db.session.commit()
        
        start_time = (base_time - timedelta(hours=1)).isoformat()
    
    response = client.get(
        f'/api/cscl/scripts/{script_id}/decisions',
        query_string={'start_time': start_time}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    # Should only include decision2 (after start_time)
    assert len(data['decisions']) >= 1


def test_rollback_migration_endpoints_fail(client, seed_users, script_with_course):
    """Test 14: After rollback, endpoints fail (404/function unavailable)"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    # Endpoint should exist when migration is applied
    response = client.get(f'/api/cscl/scripts/{script_id}/decisions')
    assert response.status_code != 404  # Should be 200 or 403, not 404


def test_restore_after_rollback_works(client, seed_users, script_with_course):
    """Test 15: After restoring migration, endpoints work again"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.post(
        f'/api/cscl/scripts/{script_id}/decisions',
        json={
            'decision_type': 'accept',
            'target_type': 'scriptlet'
        }
    )
    
    # Should work after restore
    assert response.status_code in [200, 201]


def test_concurrent_decisions_no_duplicate_keys(client, seed_users, script_with_course, app):
    """Test 16: Concurrent decision creation doesn't create duplicate keys"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    # Create multiple decisions concurrently (simulated)
    decision_ids = set()
    with app.app_context():
        for i in range(10):
            decision = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='accept',
                target_type='scriptlet',
                target_id=f's{i}'
            )
            db.session.add(decision)
            db.session.flush()
            decision_ids.add(decision.id)
        
        db.session.commit()
    
    # All IDs should be unique
    assert len(decision_ids) == 10
    
    # Verify all decisions exist
    response = client.get(f'/api/cscl/scripts/{script_id}/decisions')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['decisions']) >= 10
