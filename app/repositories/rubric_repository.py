"""Rubric repository - DB and JSON implementations"""
from abc import ABC, abstractmethod
from app.db import db
from app.models import Rubric
from app.config import Config
from app.utils import load_json, save_json
from datetime import datetime


class RubricRepository(ABC):
    """Abstract rubric repository"""
    
    @abstractmethod
    def get_all(self):
        """Get all rubrics"""
        pass
    
    @abstractmethod
    def get_by_id(self, rubric_id):
        """Get rubric by ID"""
        pass
    
    @abstractmethod
    def create(self, rubric_data):
        """Create new rubric"""
        pass
    
    @abstractmethod
    def delete_all(self):
        """Delete all rubrics (for demo init idempotency)"""
        pass


class DBRubricRepository(RubricRepository):
    """Database-backed rubric repository"""
    
    def get_all(self):
        """Get all rubrics from DB"""
        rubrics = Rubric.query.all()
        return [r.to_dict() for r in rubrics]
    
    def get_by_id(self, rubric_id):
        """Get rubric by ID from DB"""
        rubric = Rubric.query.filter_by(id=rubric_id).first()
        return rubric.to_dict() if rubric else None
    
    def create(self, rubric_data):
        """Create rubric in DB"""
        created_at = datetime.utcnow()
        if rubric_data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(rubric_data['created_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                created_at = datetime.utcnow()
        
        rubric = Rubric(
            id=rubric_data.get('id'),
            name=rubric_data.get('name', ''),
            description=rubric_data.get('description'),
            criteria=rubric_data.get('criteria', []),
            created_at=created_at
        )
        db.session.add(rubric)
        db.session.commit()
        return rubric.to_dict()
    
    def delete_all(self):
        """Delete all rubrics (for demo init idempotency)"""
        Rubric.query.delete()
        db.session.commit()


class JsonRubricRepository(RubricRepository):
    """JSON file-backed rubric repository"""
    
    def get_all(self):
        """Get all rubrics from JSON file"""
        return load_json(Config.RUBRICS_FILE)
    
    def get_by_id(self, rubric_id):
        """Get rubric by ID from JSON file"""
        rubrics = load_json(Config.RUBRICS_FILE)
        return next((r for r in rubrics if r.get('id') == rubric_id), None)
    
    def create(self, rubric_data):
        """Create rubric in JSON file"""
        rubrics = load_json(Config.RUBRICS_FILE)
        rubrics.append(rubric_data)
        save_json(Config.RUBRICS_FILE, rubrics)
        return rubric_data
    
    def delete_all(self):
        """Delete all rubrics (clear JSON file)"""
        save_json(Config.RUBRICS_FILE, [])
