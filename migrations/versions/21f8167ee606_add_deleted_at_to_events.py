"""add_deleted_at_to_events

Merge heads a2b3c4d5e6f7 and e4f5a6b7c8d9, add deleted_at column to events table.

Revision ID: 21f8167ee606
Revises: a2b3c4d5e6f7, e4f5a6b7c8d9
Create Date: 2026-05-23 13:11:16.310310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21f8167ee606'
down_revision: Union[str, Sequence[str], None] = ('a2b3c4d5e6f7', 'e4f5a6b7c8d9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add deleted_at column to events table for soft-delete support."""
    with op.batch_alter_table('events') as batch_op:
        batch_op.add_column(
            sa.Column('deleted_at', sa.DateTime(), nullable=True)
        )


def downgrade() -> None:
    """Remove deleted_at column from events table."""
    with op.batch_alter_table('events') as batch_op:
        batch_op.drop_column('deleted_at')
