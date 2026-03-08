"""add_rag_grounding

Revision ID: 006
Revises: 005
Create Date: 2025-02-05 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create cscl_course_documents table
    op.create_table(
        'cscl_course_documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('course_id', sa.String(100), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),  # file, url, text
        sa.Column('storage_uri', sa.String(1000), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('checksum', sa.String(64), nullable=True),
        sa.Column('uploaded_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
    )
    
    # Create cscl_document_chunks table
    op.create_table(
        'cscl_document_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('embedding_vector', sa.Text(), nullable=True),  # JSON/TEXT for SQLite/Postgres compatibility
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['cscl_course_documents.id'], ondelete='CASCADE'),
    )
    
    # Create cscl_evidence_bindings table
    op.create_table(
        'cscl_evidence_bindings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('script_id', sa.String(36), nullable=False),
        sa.Column('scene_id', sa.String(36), nullable=True),
        sa.Column('scriptlet_id', sa.String(36), nullable=True),
        sa.Column('chunk_id', sa.String(36), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('binding_type', sa.String(50), nullable=False),  # planner, material, critic, refiner
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['script_id'], ['cscl_scripts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scene_id'], ['cscl_scenes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scriptlet_id'], ['cscl_scriptlets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chunk_id'], ['cscl_document_chunks.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_course_docs_course_id', 'cscl_course_documents', ['course_id'])
    op.create_index('idx_course_docs_uploaded_by', 'cscl_course_documents', ['uploaded_by'])
    op.create_index('idx_chunks_document_id', 'cscl_document_chunks', ['document_id'])
    op.create_index('idx_chunks_chunk_index', 'cscl_document_chunks', ['document_id', 'chunk_index'])
    op.create_index('idx_evidence_bindings_script_id', 'cscl_evidence_bindings', ['script_id'])
    op.create_index('idx_evidence_bindings_chunk_id', 'cscl_evidence_bindings', ['chunk_id'])
    op.create_index('idx_evidence_bindings_type', 'cscl_evidence_bindings', ['binding_type'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_evidence_bindings_type', 'cscl_evidence_bindings')
    op.drop_index('idx_evidence_bindings_chunk_id', 'cscl_evidence_bindings')
    op.drop_index('idx_evidence_bindings_script_id', 'cscl_evidence_bindings')
    op.drop_index('idx_chunks_chunk_index', 'cscl_document_chunks')
    op.drop_index('idx_chunks_document_id', 'cscl_document_chunks')
    op.drop_index('idx_course_docs_uploaded_by', 'cscl_course_documents')
    op.drop_index('idx_course_docs_course_id', 'cscl_course_documents')
    op.drop_table('cscl_evidence_bindings')
    op.drop_table('cscl_document_chunks')
    op.drop_table('cscl_course_documents')
