"""add_chart_reviews_table

Revision ID: 45214759c8f9
Revises: a1b2c3d4e5f6
Create Date: 2026-03-16 19:24:30.577003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45214759c8f9'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'chart_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_hash', sa.String(length=64), nullable=False),
        sa.Column('birth_info', sa.Text(), nullable=True),
        sa.Column('life_palace_gz', sa.String(length=10), nullable=False),
        sa.Column('wuxing_ju_name', sa.String(length=10), nullable=False),
        sa.Column('pattern_summary', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reviewer', sa.String(length=100), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('reject_reason', sa.Text(), nullable=True),
        sa.Column('algorithm_version', sa.String(length=20), nullable=False),
        sa.Column('template_version', sa.String(length=20), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_chart_reviews_hash', 'chart_reviews', ['report_hash'], unique=False)
    op.create_index('idx_chart_reviews_status', 'chart_reviews', ['status'], unique=False)
    op.create_index('idx_chart_reviews_created', 'chart_reviews', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_chart_reviews_created', table_name='chart_reviews')
    op.drop_index('idx_chart_reviews_status', table_name='chart_reviews')
    op.drop_index('idx_chart_reviews_hash', table_name='chart_reviews')
    op.drop_table('chart_reviews')
