"""add_teacher_decisions

Revision ID: 007
Revises: 006
Create Date: 2025-02-05 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create cscl_teacher_decisions table
    op.create_table(
        'cscl_teacher_decisions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('script_id', sa.String(36), nullable=False),
        sa.Column('revision_id', sa.String(36), nullable=True),
        sa.Column('actor_id', sa.String(36), nullable=False),
        sa.Column('decision_type', sa.String(50), nullable=False),  # accept/reject/edit/add/delete/reorder/finalize_note
        sa.Column('target_type', sa.String(50), nullable=False),  # scene/role/scriptlet/material/evidence/pipeline_output
        sa.Column('target_id', sa.String(36), nullable=True),
        sa.Column('before_json', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.Column('after_json', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.Column('rationale_text', sa.Text(), nullable=True),
        sa.Column('source_stage', sa.String(50), nullable=True),  # planner/material/critic/refiner/manual
        sa.Column('confidence', sa.Integer(), nullable=True),  # 1-5
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['script_id'], ['cscl_scripts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['revision_id'], ['cscl_script_revisions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
    )
    
    # Create indexes
    op.create_index('idx_decisions_script_created', 'cscl_teacher_decisions', ['script_id', 'created_at'])
    op.create_index('idx_decisions_actor_created', 'cscl_teacher_decisions', ['actor_id', 'created_at'])
    op.create_index('idx_decisions_type', 'cscl_teacher_decisions', ['decision_type'])
    op.create_index('idx_decisions_target', 'cscl_teacher_decisions', ['target_type', 'target_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_decisions_target', 'cscl_teacher_decisions')
    op.drop_index('idx_decisions_type', 'cscl_teacher_decisions')
    op.drop_index('idx_decisions_actor_created', 'cscl_teacher_decisions')
    op.drop_index('idx_decisions_script_created', 'cscl_teacher_decisions')
    op.drop_table('cscl_teacher_decisions')
