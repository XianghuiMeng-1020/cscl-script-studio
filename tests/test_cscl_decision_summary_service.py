"""Tests for Decision Summary Service"""
import pytest
from datetime import datetime, timedelta
from app import create_app
from app.db import db
from app.models import User, UserRole, CSCLScript, CSCLTeacherDecision
from app.services.decision_summary_service import DecisionSummaryService


@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['USE_DB_STORAGE'] = True
    app.config['DATABASE_URL'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def seed_teacher(app):
    """Create teacher user T001 so script FK can reference it"""
    with app.app_context():
        user = User(id='T001', role=UserRole.TEACHER)
        user.set_password('teacher123')
        db.session.add(user)
        db.session.commit()
        yield user


@pytest.fixture
def script_id(app, seed_teacher):
    """Create test script and return ID"""
    with app.app_context():
        script = CSCLScript(
            id='script001',
            title='Test Script',
            topic='ML',
            task_type='debate',
            duration_minutes=60,
            created_by='T001'
        )
        db.session.add(script)
        db.session.commit()
        return script.id


def test_compute_summary_empty_decisions(app, script_id):
    """Test summary computation with no decisions"""
    with app.app_context():
        summary = DecisionSummaryService.compute_summary(script_id)
        
        assert summary['total_decisions'] == 0
        assert summary['accept_rate'] == 0.0
        assert summary['reject_rate'] == 0.0
        assert summary['edit_rate'] == 0.0
        assert 'reproducibility' in summary


def test_compute_summary_with_decisions(app, script_id):
    """Test summary computation with decisions"""
    with app.app_context():
        # Create decisions
        for i in range(10):
            decision = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='accept' if i < 6 else 'reject',
                target_type='scriptlet',
                target_id=f's{i}',
                source_stage='planner' if i < 5 else 'manual'
            )
            db.session.add(decision)
        db.session.commit()
        
        summary = DecisionSummaryService.compute_summary(script_id)
        
        assert summary['total_decisions'] == 10
        assert summary['accept_rate'] == 0.6  # 6/10
        assert summary['reject_rate'] == 0.4  # 4/10
        assert 'stage_adoption_rate' in summary


def test_compute_summary_stage_adoption_rate(app, script_id):
    """Test stage adoption rate computation"""
    with app.app_context():
        # Create decisions for planner stage
        for i in range(5):
            decision = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='accept' if i < 3 else 'reject',
                target_type='scriptlet',
                target_id=f's{i}',
                source_stage='planner'
            )
            db.session.add(decision)
        db.session.commit()
        
        summary = DecisionSummaryService.compute_summary(script_id)
        
        assert 'planner' in summary['stage_adoption_rate']
        planner_stats = summary['stage_adoption_rate']['planner']
        assert planner_stats['adoption_rate'] == 0.6  # 3/5
        assert planner_stats['total_decisions'] == 5


def test_compute_summary_evidence_linked_edit_rate(app, script_id):
    """Test evidence linked edit rate computation"""
    with app.app_context():
        # Create edits with and without evidence
        for i in range(5):
            decision = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='edit',
                target_type='scriptlet',
                target_id=f's{i}',
                after_json={'evidence_refs': ['chunk1']} if i < 3 else {}
            )
            db.session.add(decision)
        db.session.commit()
        
        summary = DecisionSummaryService.compute_summary(script_id)
        
        assert summary['evidence_linked_edit_rate'] == 0.6  # 3/5


def test_get_timeline_with_filters(app, script_id):
    """Test timeline retrieval with filters"""
    with app.app_context():
        # Create decisions
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
        timeline = DecisionSummaryService.get_timeline(
            script_id,
            decision_type='accept'
        )
        
        assert len(timeline) == 1
        assert timeline[0]['decision_type'] == 'accept'
        
        # Filter by source_stage
        timeline = DecisionSummaryService.get_timeline(
            script_id,
            source_stage='planner'
        )
        
        assert len(timeline) == 1
        assert timeline[0]['source_stage'] == 'planner'


def test_get_timeline_ordering(app, script_id):
    """Test timeline is ordered by created_at"""
    with app.app_context():
        base_time = datetime.now()
        decisions = []
        for i in range(5):
            decision = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='accept',
                target_type='scriptlet',
                target_id=f's{i}',
                created_at=base_time + timedelta(minutes=i)
            )
            decisions.append(decision)
            db.session.add(decision)
        db.session.commit()
        
        timeline = DecisionSummaryService.get_timeline(script_id)
        
        timestamps = [datetime.fromisoformat(d['created_at'].replace('Z', '+00:00')) for d in timeline]
        assert timestamps == sorted(timestamps)


def test_compute_summary_with_reproducibility(app, script_id):
    """Test summary includes reproducibility fields"""
    with app.app_context():
        summary = DecisionSummaryService.compute_summary(
            script_id,
            spec_hash='abc123',
            config_fingerprint='def456',
            provider='mock',
            model='mock-model',
            pipeline_run_id='run_xyz'
        )
        
        repro = summary['reproducibility']
        assert repro['spec_hash'] == 'abc123'
        assert repro['config_fingerprint'] == 'def456'
        assert repro['provider'] == 'mock'
        assert repro['model'] == 'mock-model'
        assert repro['pipeline_run_id'] == 'run_xyz'
