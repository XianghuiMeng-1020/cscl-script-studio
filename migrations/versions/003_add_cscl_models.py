"""add_cscl_models

Revision ID: 003
Revises: 002
Create Date: 2025-02-05 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create cscl_scripts table
    op.create_table(
        'cscl_scripts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('topic', sa.String(500), nullable=False),
        sa.Column('course_id', sa.String(100), nullable=True),
        sa.Column('learning_objectives', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.Column('task_type', sa.String(100), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )
    
    # Create cscl_scenes table
    op.create_table(
        'cscl_scenes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('script_id', sa.String(36), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('scene_type', sa.String(100), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('transition_rule', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['script_id'], ['cscl_scripts.id'], ondelete='CASCADE'),
    )
    
    # Create cscl_roles table
    op.create_table(
        'cscl_roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('script_id', sa.String(36), nullable=False),
        sa.Column('role_name', sa.String(100), nullable=False),
        sa.Column('responsibilities', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.ForeignKeyConstraint(['script_id'], ['cscl_scripts.id'], ondelete='CASCADE'),
    )
    
    # Create cscl_scriptlets table
    op.create_table(
        'cscl_scriptlets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('scene_id', sa.String(36), nullable=False),
        sa.Column('role_id', sa.String(36), nullable=True),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('prompt_type', sa.String(100), nullable=False),
        sa.Column('resource_ref', sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(['scene_id'], ['cscl_scenes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['cscl_roles.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('cscl_scriptlets')
    op.drop_table('cscl_roles')
    op.drop_table('cscl_scenes')
    op.drop_table('cscl_scripts')
