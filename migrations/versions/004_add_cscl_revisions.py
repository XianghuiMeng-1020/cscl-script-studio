"""add_cscl_revisions

Revision ID: 004
Revises: 003
Create Date: 2025-02-05 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create cscl_script_revisions table
    op.create_table(
        'cscl_script_revisions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('script_id', sa.String(36), nullable=False),
        sa.Column('editor_id', sa.String(36), nullable=False),
        sa.Column('revision_type', sa.String(50), nullable=False),
        sa.Column('before_json', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.Column('after_json', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.Column('diff_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['script_id'], ['cscl_scripts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['editor_id'], ['users.id']),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('cscl_script_revisions')
