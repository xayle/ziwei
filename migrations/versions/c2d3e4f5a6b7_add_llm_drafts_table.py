"""add_llm_drafts_table

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-16 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'llm_drafts',
        sa.Column('id',                sa.Integer(),           nullable=False),
        sa.Column('chart_hash',        sa.String(length=64),   nullable=False),
        sa.Column('provider',          sa.String(length=30),   nullable=False),
        sa.Column('model',             sa.String(length=60),   nullable=False),
        sa.Column('prompt_version',    sa.String(length=40),   nullable=False),
        sa.Column('draft_text',        sa.Text(),              nullable=True),
        sa.Column('status',            sa.String(length=20),   nullable=False),
        sa.Column('reviewer',          sa.String(length=100),  nullable=False),
        sa.Column('reviewer_notes',    sa.Text(),              nullable=True),
        sa.Column('input_tokens',      sa.Integer(),           nullable=False),
        sa.Column('output_tokens',     sa.Integer(),           nullable=False),
        sa.Column('cost_usd_estimate', sa.Float(),             nullable=False),
        sa.Column('created_at',        sa.DateTime(),          nullable=False),
        sa.Column('reviewed_at',       sa.DateTime(),          nullable=True),
        sa.Column('deleted_at',        sa.DateTime(),          nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_llm_drafts_hash',    'llm_drafts', ['chart_hash'], unique=False)
    op.create_index('idx_llm_drafts_status',  'llm_drafts', ['status'],     unique=False)
    op.create_index('idx_llm_drafts_created', 'llm_drafts', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_llm_drafts_created', table_name='llm_drafts')
    op.drop_index('idx_llm_drafts_status',  table_name='llm_drafts')
    op.drop_index('idx_llm_drafts_hash',    table_name='llm_drafts')
    op.drop_table('llm_drafts')
