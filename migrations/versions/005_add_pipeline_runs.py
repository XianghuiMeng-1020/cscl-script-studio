"""add_pipeline_runs

Revision ID: 005
Revises: 004
Create Date: 2025-02-05 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create cscl_pipeline_runs table
    op.create_table(
        'cscl_pipeline_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(100), nullable=False, unique=True),
        sa.Column('script_id', sa.String(36), nullable=False),
        sa.Column('initiated_by', sa.String(36), nullable=False),
        sa.Column('spec_hash', sa.String(64), nullable=True),
        sa.Column('pipeline_version', sa.String(20), nullable=False, server_default='1.0.0'),
        sa.Column('config_fingerprint', sa.String(128), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='running'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['script_id'], ['cscl_scripts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['initiated_by'], ['users.id']),
    )
    
    # Create cscl_pipeline_stage_runs table
    op.create_table(
        'cscl_pipeline_stage_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(100), nullable=False),
        sa.Column('stage_name', sa.String(50), nullable=False),
        sa.Column('input_json', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.Column('output_json', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('token_usage_json', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.Column('status', sa.String(50), nullable=False, server_default='running'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['cscl_pipeline_runs.run_id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_pipeline_runs_script_id', 'cscl_pipeline_runs', ['script_id'])
    op.create_index('idx_pipeline_runs_status', 'cscl_pipeline_runs', ['status'])
    op.create_index('idx_pipeline_runs_created_at', 'cscl_pipeline_runs', ['created_at'])
    op.create_index('idx_stage_runs_run_id', 'cscl_pipeline_stage_runs', ['run_id'])
    op.create_index('idx_stage_runs_stage_name', 'cscl_pipeline_stage_runs', ['stage_name'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_stage_runs_stage_name', 'cscl_pipeline_stage_runs')
    op.drop_index('idx_stage_runs_run_id', 'cscl_pipeline_stage_runs')
    op.drop_index('idx_pipeline_runs_created_at', 'cscl_pipeline_runs')
    op.drop_index('idx_pipeline_runs_status', 'cscl_pipeline_runs')
    op.drop_index('idx_pipeline_runs_script_id', 'cscl_pipeline_runs')
    op.drop_table('cscl_pipeline_stage_runs')
    op.drop_table('cscl_pipeline_runs')
