"""Tests for CSCL Retriever service"""
import pytest
from app import create_app
from app.db import db
from app.models import User, UserRole, CSCLCourseDocument, CSCLDocumentChunk
from app.services.cscl_retriever import CSCLRetriever


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
    """Create teacher user T001 for document uploaded_by FK"""
    with app.app_context():
        user = User(id='T001', role=UserRole.TEACHER)
        user.set_password('teacher123')
        db.session.add(user)
        db.session.commit()
        yield user


@pytest.fixture
def course_id():
    """Course ID for testing"""
    return 'CS101'


@pytest.fixture
def retriever():
    """Create retriever instance"""
    return CSCLRetriever(k=5)


@pytest.fixture
def sample_documents(app, seed_teacher, course_id):
    """Create sample documents for testing"""
    with app.app_context():
        # Create document 1
        doc1 = CSCLCourseDocument(
            id='doc1',
            course_id=course_id,
            title='Machine Learning Basics',
            source_type='text',
            mime_type='text/plain',
            uploaded_by='T001'
        )
        db.session.add(doc1)
        db.session.flush()
        
        # Create chunks for doc1
        chunk1 = CSCLDocumentChunk(
            document_id=doc1.id,
            chunk_index=0,
            chunk_text='Machine learning is a subset of artificial intelligence that focuses on algorithms.',
            token_count=15
        )
        chunk2 = CSCLDocumentChunk(
            document_id=doc1.id,
            chunk_index=1,
            chunk_text='Neural networks are computational models inspired by biological neural networks.',
            token_count=14
        )
        db.session.add(chunk1)
        db.session.add(chunk2)
        
        # Create document 2
        doc2 = CSCLCourseDocument(
            id='doc2',
            course_id=course_id,
            title='Deep Learning',
            source_type='text',
            mime_type='text/plain',
            uploaded_by='T001'
        )
        db.session.add(doc2)
        db.session.flush()
        
        chunk3 = CSCLDocumentChunk(
            document_id=doc2.id,
            chunk_index=0,
            chunk_text='Deep learning uses multiple layers of neural networks.',
            token_count=10
        )
        db.session.add(chunk3)
        
        db.session.commit()
        
        return {'doc1': doc1, 'doc2': doc2, 'chunks': [chunk1, chunk2, chunk3]}


def test_retriever_initialization(retriever):
    """Test retriever can be initialized"""
    assert retriever is not None
    assert retriever.k == 5


def test_retrieve_with_matching_query(app, retriever, course_id, sample_documents):
    """Test retrieval returns relevant chunks"""
    with app.app_context():
        query = 'machine learning neural networks'
        results = retriever.retrieve(query, course_id, 'planner')
        
        assert len(results) > 0
        assert all('chunk_id' in r for r in results)
        assert all('relevance_score' in r for r in results)
        assert all('snippet' in r for r in results)


def test_retrieve_with_no_documents(app, retriever):
    """Test retrieval with no documents returns empty list"""
    with app.app_context():
        results = retriever.retrieve('test query', 'NONEXISTENT', 'planner')
        assert results == []


def test_retrieve_relevance_scoring(app, retriever, course_id, sample_documents):
    """Test that relevance scores are computed"""
    with app.app_context():
        query = 'machine learning'
        results = retriever.retrieve(query, course_id, 'planner')
        
        if results:
            # Results should be sorted by relevance score
            scores = [r['relevance_score'] for r in results]
            assert scores == sorted(scores, reverse=True)
            assert all(s > 0 for s in scores)


def test_construct_query_from_spec(retriever):
    """Test query construction from spec"""
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'Machine Learning'
        },
        'learning_objectives': {
            'knowledge': ['Understand ML'],
            'skills': ['Apply algorithms']
        },
        'task_requirements': {
            'task_type': 'debate',
            'expected_output': 'argument'
        }
    }
    
    query = retriever.construct_query(spec, 'planner')
    assert 'Machine Learning' in query
    assert 'Data Science' in query
    assert isinstance(query, str)
    assert len(query) > 0


def test_retrieve_top_k_limit(app, retriever, course_id, sample_documents):
    """Test that retrieval respects k limit"""
    retriever_k2 = CSCLRetriever(k=2)
    
    with app.app_context():
        query = 'machine learning neural networks deep learning'
        results = retriever_k2.retrieve(query, course_id, 'planner')
        
        assert len(results) <= 2


def test_retrieve_empty_query(app, retriever, course_id, sample_documents):
    """Test retrieval with empty query returns empty list"""
    with app.app_context():
        results = retriever.retrieve('', course_id, 'planner')
        assert results == []


def test_retrieve_different_binding_types(app, retriever, course_id, sample_documents):
    """Test retrieval works for different binding types"""
    with app.app_context():
        query = 'machine learning'
        
        for binding_type in ['planner', 'material', 'critic', 'refiner']:
            results = retriever.retrieve(query, course_id, binding_type)
            # Should not crash, may return empty or results
            assert isinstance(results, list)
