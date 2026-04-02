"""Tests for CSCL Pipeline Service (unit tests)"""
import pytest
from app.services.cscl_pipeline_service import (
    CSCLPipelineService, compute_spec_hash, compute_config_fingerprint
)
import json


def test_compute_spec_hash():
    """Test spec hash computation"""
    spec1 = {
        'course_context': {'subject': 'DS', 'topic': 'ML', 'class_size': 30, 'mode': 'sync', 'duration': 90},
        'learning_objectives': {'knowledge': ['Test'], 'skills': ['Test']},
        'task_requirements': {'task_type': 'debate', 'expected_output': 'test', 'collaboration_form': 'group'}
    }
    
    spec2 = spec1.copy()
    
    hash1 = compute_spec_hash(spec1)
    hash2 = compute_spec_hash(spec2)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length


def test_compute_config_fingerprint():
    """Test config fingerprint computation"""
    options1 = {'temperature': 0.7, 'max_tokens': 1000}
    options2 = {'temperature': 0.7, 'max_tokens': 1000}
    options3 = {'temperature': 0.8, 'max_tokens': 1000}
    
    fp1 = compute_config_fingerprint(options1, 'mock', 'mock-model')
    fp2 = compute_config_fingerprint(options2, 'mock', 'mock-model')
    fp3 = compute_config_fingerprint(options3, 'mock', 'mock-model')
    
    assert fp1 == fp2
    assert fp1 != fp3
    assert len(fp1) == 64


def test_pipeline_service_initialization():
    """Test pipeline service can be initialized"""
    service = CSCLPipelineService()
    assert service.planner is not None
    assert service.material_generator is not None
    assert service.critic_refiner is not None
