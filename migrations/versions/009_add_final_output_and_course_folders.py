"""add final_output_json to pipeline_runs; add course_folders table

Revision ID: 009
Revises: 008
Create Date: 2026-03-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'cscl_pipeline_runs',
        sa.Column('final_output_json', sa.JSON(), nullable=True)
    )

    op.create_table(
        'cscl_course_folders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.add_column(
        'cscl_scripts',
        sa.Column('folder_id', sa.String(36), sa.ForeignKey('cscl_course_folders.id'), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('cscl_scripts', 'folder_id')
    op.drop_table('cscl_course_folders')
    op.drop_column('cscl_pipeline_runs', 'final_output_json')
