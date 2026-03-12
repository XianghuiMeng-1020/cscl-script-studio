"""Database models - minimal schema"""
from app.db import db
from datetime import datetime
import uuid
import json
from sqlalchemy import Text, Enum, TypeDecorator, UniqueConstraint
import enum

# JSON column type that works with both PostgreSQL and SQLite
class JSON(TypeDecorator):
    """JSON type that works with both PostgreSQL JSONB and SQLite TEXT"""
    impl = Text
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(Text())
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            if isinstance(value, str):
                return json.loads(value)
            return value
        return value


class UserRole(enum.Enum):
    """User role enumeration"""
    TEACHER = 'teacher'
    STUDENT = 'student'
    ADMIN = 'admin'


class SubmissionStatus(enum.Enum):
    """Submission status enumeration"""
    PENDING = 'pending'
    GRADED = 'graded'


class User(db.Model):
    """User model with authentication support"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role = db.Column(Enum(UserRole, values_callable=lambda enum_cls: [e.value for e in enum_cls], name='userrole'), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Only for teacher/admin
    token = db.Column(db.String(255), nullable=True)  # For student one-time token
    token_expires_at = db.Column(db.DateTime, nullable=True)  # Token expiration
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Flask-Login required methods
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return self.id
    
    def check_password(self, password):
        """Check password using werkzeug"""
        if not self.password_hash:
            return False
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Set password using werkzeug"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role.value if self.role else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Assignment(db.Model):
    """Assignment model"""
    __tablename__ = 'assignments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(Text, nullable=True)
    course_id = db.Column(db.String(100), nullable=True)
    due_date = db.Column(db.String(50), nullable=True)
    rubric_id = db.Column(db.String(36), nullable=True)
    status = db.Column(db.String(50), default='active', nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'course_id': self.course_id,
            'due_date': self.due_date,
            'rubric_id': self.rubric_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Rubric(db.Model):
    """Rubric model"""
    __tablename__ = 'rubrics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(500), nullable=False)
    description = db.Column(Text, nullable=True)
    criteria = db.Column(JSON, nullable=True)  # Store criteria as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'criteria': self.criteria if isinstance(self.criteria, (dict, list)) else json.loads(self.criteria) if isinstance(self.criteria, str) else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Submission(db.Model):
    """Submission model"""
    __tablename__ = 'submissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assignment_id = db.Column(db.String(36), db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    student_name = db.Column(db.String(200), nullable=True)
    content = db.Column(Text, nullable=False)
    status = db.Column(Enum(SubmissionStatus, values_callable=lambda enum_cls: [e.value for e in enum_cls], name='submissionstatus'), default=SubmissionStatus.PENDING, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dict with compatibility fields for JSON format"""
        result = {
            'id': self.id,
            'assignment_id': self.assignment_id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'content': self.content,
            'status': self.status.value if self.status else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'graded_at': self.graded_at.isoformat() if self.graded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Compatibility fields (stored in Feedback model, but included here for JSON compatibility)
            'feedback': None,
            'rubric_scores': None,
            'visual_summary': None,
            'video_script': None,
            'feedback_quality': None
        }
        return result


class Feedback(db.Model):
    """Feedback model - minimal fields"""
    __tablename__ = 'feedback'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = db.Column(db.String(36), db.ForeignKey('submissions.id'), nullable=False)
    rubric_scores = db.Column(JSON, nullable=True)
    written_feedback = db.Column(Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'submission_id': self.submission_id,
            'rubric_scores': self.rubric_scores if isinstance(self.rubric_scores, dict) else json.loads(self.rubric_scores) if isinstance(self.rubric_scores, str) else None,
            'written_feedback': self.written_feedback,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AuditLog(db.Model):
    """Audit log model for tracking system events"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = db.Column(db.String(100), nullable=False)  # login_success, login_failed, logout, demo_init, etc.
    actor_id = db.Column(db.String(36), nullable=True)  # User ID who performed the action
    role = db.Column(Enum(UserRole, values_callable=lambda enum_cls: [e.value for e in enum_cls], name='userrole'), nullable=True)  # Role of the actor
    target_id = db.Column(db.String(36), nullable=True)  # Target resource ID (e.g., submission_id)
    status = db.Column(db.String(50), nullable=False, default='success')  # success, failed
    meta_json = db.Column(JSON, nullable=True)  # Additional metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'actor_id': self.actor_id,
            'role': self.role.value if self.role else None,
            'target_id': self.target_id,
            'status': self.status,
            'meta_json': self.meta_json,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CSCLScript(db.Model):
    """CSCL Script model"""
    __tablename__ = 'cscl_scripts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(500), nullable=False)
    topic = db.Column(db.String(500), nullable=False)
    course_id = db.Column(db.String(100), nullable=True)
    learning_objectives = db.Column(JSON, nullable=True)  # Array of objectives
    task_type = db.Column(db.String(100), nullable=False)  # e.g., "debate", "collaborative_writing"
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    status = db.Column(db.String(50), nullable=False, default='draft')  # draft, final
    published_at = db.Column(db.DateTime, nullable=True)  # when teacher published for students
    share_code = db.Column(db.String(12), unique=True, nullable=True, index=True)  # short code for student access
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'topic': self.topic,
            'course_id': self.course_id,
            'learning_objectives': self.learning_objectives,
            'task_type': self.task_type,
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'share_code': self.share_code,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CSCLScene(db.Model):
    """CSCL Scene model"""
    __tablename__ = 'cscl_scenes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_id = db.Column(db.String(36), db.ForeignKey('cscl_scripts.id'), nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    scene_type = db.Column(db.String(100), nullable=False)  # confrontation, opening, argumentation, conclusion
    purpose = db.Column(Text, nullable=True)
    transition_rule = db.Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'script_id': self.script_id,
            'order_index': self.order_index,
            'scene_type': self.scene_type,
            'purpose': self.purpose,
            'transition_rule': self.transition_rule
        }


class CSCLRole(db.Model):
    """CSCL Role model"""
    __tablename__ = 'cscl_roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_id = db.Column(db.String(36), db.ForeignKey('cscl_scripts.id'), nullable=False)
    role_name = db.Column(db.String(100), nullable=False)  # advocate, challenger, synthesizer, evidence_checker
    responsibilities = db.Column(JSON, nullable=True)  # Array of responsibilities
    
    def to_dict(self):
        return {
            'id': self.id,
            'script_id': self.script_id,
            'role_name': self.role_name,
            'responsibilities': self.responsibilities
        }


class CSCLScriptlet(db.Model):
    """CSCL Scriptlet model"""
    __tablename__ = 'cscl_scriptlets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = db.Column(db.String(36), db.ForeignKey('cscl_scenes.id'), nullable=False)
    role_id = db.Column(db.String(36), db.ForeignKey('cscl_roles.id'), nullable=True)
    prompt_text = db.Column(Text, nullable=False)
    prompt_type = db.Column(db.String(100), nullable=False)  # claim, evidence, counterargument, synthesis
    resource_ref = db.Column(db.String(500), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'scene_id': self.scene_id,
            'role_id': self.role_id,
            'prompt_text': self.prompt_text,
            'prompt_type': self.prompt_type,
            'resource_ref': self.resource_ref
        }


class CSCLScriptRevision(db.Model):
    """CSCL Script revision tracking model"""
    __tablename__ = 'cscl_script_revisions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_id = db.Column(db.String(36), db.ForeignKey('cscl_scripts.id'), nullable=False)
    editor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    revision_type = db.Column(db.String(50), nullable=False)  # create, update, finalize, regenerate
    before_json = db.Column(JSON, nullable=True)  # Script state before change
    after_json = db.Column(JSON, nullable=True)  # Script state after change
    diff_summary = db.Column(Text, nullable=True)  # Human-readable summary of changes
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'script_id': self.script_id,
            'editor_id': self.editor_id,
            'revision_type': self.revision_type,
            'before_json': self.before_json,
            'after_json': self.after_json,
            'diff_summary': self.diff_summary,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CSCLPipelineRun(db.Model):
    """CSCL Pipeline run tracking model"""
    __tablename__ = 'cscl_pipeline_runs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = db.Column(db.String(100), nullable=False, unique=True)
    script_id = db.Column(db.String(36), db.ForeignKey('cscl_scripts.id'), nullable=False)
    initiated_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    spec_hash = db.Column(db.String(64), nullable=True)
    pipeline_version = db.Column(db.String(20), nullable=False, default='1.0.0')
    config_fingerprint = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='running')  # running, success, partial_failed, failed
    error_message = db.Column(Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'run_id': self.run_id,
            'script_id': self.script_id,
            'initiated_by': self.initiated_by,
            'spec_hash': self.spec_hash,
            'pipeline_version': self.pipeline_version,
            'config_fingerprint': self.config_fingerprint,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None
        }


class CSCLPipelineStageRun(db.Model):
    """CSCL Pipeline stage run tracking model"""
    __tablename__ = 'cscl_pipeline_stage_runs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = db.Column(db.String(100), db.ForeignKey('cscl_pipeline_runs.run_id'), nullable=False)
    stage_name = db.Column(db.String(50), nullable=False)  # planner, material_generator, critic, refiner
    input_json = db.Column(JSON, nullable=True)
    output_json = db.Column(JSON, nullable=True)
    provider = db.Column(db.String(50), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)
    token_usage_json = db.Column(JSON, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='running')  # running, success, failed, skipped
    error_message = db.Column(Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'run_id': self.run_id,
            'stage_name': self.stage_name,
            'input_json': self.input_json,
            'output_json': self.output_json,
            'provider': self.provider,
            'model': self.model,
            'latency_ms': self.latency_ms,
            'token_usage_json': self.token_usage_json,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CSCLCourseDocument(db.Model):
    """Course document model for RAG grounding"""
    __tablename__ = 'cscl_course_documents'
    __table_args__ = (UniqueConstraint('course_id', 'checksum', name='uq_cscl_course_doc_course_checksum'),)
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    source_type = db.Column(db.String(50), nullable=False)  # file, url, text
    storage_uri = db.Column(db.String(1000), nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    checksum = db.Column(db.String(64), nullable=True)
    material_level = db.Column(db.String(20), nullable=False, default='course')  # course | lesson
    uploaded_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    chunks = db.relationship('CSCLDocumentChunk', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'source_type': self.source_type,
            'storage_uri': self.storage_uri,
            'mime_type': self.mime_type,
            'checksum': self.checksum,
            'material_level': self.material_level,
            'uploaded_by': self.uploaded_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CSCLDocumentChunk(db.Model):
    """Document chunk model for RAG retrieval"""
    __tablename__ = 'cscl_document_chunks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey('cscl_course_documents.id'), nullable=False)
    chunk_index = db.Column(db.Integer(), nullable=False)
    chunk_text = db.Column(Text, nullable=False)
    token_count = db.Column(db.Integer(), nullable=True)
    embedding_vector = db.Column(Text, nullable=True)  # JSON/TEXT for compatibility
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    evidence_bindings = db.relationship('CSCLEvidenceBinding', backref='chunk', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'chunk_text': self.chunk_text[:500] if self.chunk_text else None,  # Snippet
            'token_count': self.token_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CSCLEvidenceBinding(db.Model):
    """Evidence binding model linking scriptlets to document chunks"""
    __tablename__ = 'cscl_evidence_bindings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_id = db.Column(db.String(36), db.ForeignKey('cscl_scripts.id'), nullable=False)
    scene_id = db.Column(db.String(36), db.ForeignKey('cscl_scenes.id'), nullable=True)
    scriptlet_id = db.Column(db.String(36), db.ForeignKey('cscl_scriptlets.id'), nullable=True)
    chunk_id = db.Column(db.String(36), db.ForeignKey('cscl_document_chunks.id'), nullable=False)
    relevance_score = db.Column(db.Float(), nullable=True)
    binding_type = db.Column(db.String(50), nullable=False)  # planner, material, critic, refiner
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'script_id': self.script_id,
            'scene_id': self.scene_id,
            'scriptlet_id': self.scriptlet_id,
            'chunk_id': self.chunk_id,
            'relevance_score': self.relevance_score,
            'binding_type': self.binding_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CSCLTeacherDecision(db.Model):
    """Teacher decision tracking model for teacher-in-the-loop analysis"""
    __tablename__ = 'cscl_teacher_decisions'
    
    VALID_DECISION_TYPES = ['accept', 'reject', 'edit', 'add', 'delete', 'reorder', 'finalize_note']
    VALID_TARGET_TYPES = ['scene', 'role', 'scriptlet', 'material', 'evidence', 'pipeline_output']
    VALID_SOURCE_STAGES = ['planner', 'material', 'critic', 'refiner', 'manual']
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_id = db.Column(db.String(36), db.ForeignKey('cscl_scripts.id', ondelete='CASCADE'), nullable=False)
    revision_id = db.Column(db.String(36), db.ForeignKey('cscl_script_revisions.id', ondelete='SET NULL'), nullable=True)
    actor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    decision_type = db.Column(db.String(50), nullable=False)  # accept/reject/edit/add/delete/reorder/finalize_note
    target_type = db.Column(db.String(50), nullable=False)  # scene/role/scriptlet/material/evidence/pipeline_output
    target_id = db.Column(db.String(36), nullable=True)
    before_json = db.Column(JSON, nullable=True)
    after_json = db.Column(JSON, nullable=True)
    rationale_text = db.Column(Text, nullable=True)
    source_stage = db.Column(db.String(50), nullable=True)  # planner/material/critic/refiner/manual
    confidence = db.Column(db.Integer(), nullable=True)  # 1-5
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'script_id': self.script_id,
            'revision_id': self.revision_id,
            'actor_id': self.actor_id,
            'decision_type': self.decision_type,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'before_json': self.before_json,
            'after_json': self.after_json,
            'rationale_text': self.rationale_text,
            'source_stage': self.source_stage,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StudentGroup(db.Model):
    """One group per published script; students join to collaborate and chat."""
    __tablename__ = 'student_groups'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_id = db.Column(db.String(36), db.ForeignKey('cscl_scripts.id', ondelete='CASCADE'), nullable=False)
    group_name = db.Column(db.String(200), nullable=False, default='Group')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'script_id': self.script_id,
            'group_name': self.group_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StudentGroupMember(db.Model):
    """Student membership in a group; optional role_label from CSCLRole.role_name."""
    __tablename__ = 'student_group_members'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = db.Column(db.String(36), db.ForeignKey('student_groups.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role_label = db.Column(db.String(100), nullable=True)  # e.g. advocate, challenger
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'role_label': self.role_label,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }


class GroupMessage(db.Model):
    """Chat message in a student group."""
    __tablename__ = 'group_messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = db.Column(db.String(36), db.ForeignKey('student_groups.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StudentTaskSubmission(db.Model):
    """Student's submission for a scene task (one per user per scene per script)."""
    __tablename__ = 'student_task_submissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_id = db.Column(db.String(36), db.ForeignKey('cscl_scripts.id', ondelete='CASCADE'), nullable=False)
    scene_id = db.Column(db.String(36), db.ForeignKey('cscl_scenes.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='pending')  # pending, submitted, reviewed
    submitted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'script_id': self.script_id,
            'scene_id': self.scene_id,
            'user_id': self.user_id,
            'content': self.content,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
