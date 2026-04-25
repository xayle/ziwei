"""add_experiments_and_experiment_events_tables

Revision ID: b1c2d3e4f5a6
Revises: 45214759c8f9
Create Date: 2026-03-16 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = '45214759c8f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # experiments 表
    op.create_table(
        'experiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('variants', sa.Text(), nullable=True),
        sa.Column('traffic_split', sa.Text(), nullable=True),
        sa.Column('target_metric', sa.String(length=100), nullable=False),
        sa.Column('hypothesis', sa.Text(), nullable=True),
        sa.Column('min_sample_size', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_experiments_status', 'experiments', ['status'], unique=False)
    op.create_index('idx_experiments_name', 'experiments', ['name'], unique=False)
    op.create_index('idx_experiments_created', 'experiments', ['created_at'], unique=False)

    # experiment_events 表
    op.create_table(
        'experiment_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('variant', sa.String(length=50), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('meta', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_exp_events_exp_id', 'experiment_events', ['experiment_id'], unique=False)
    op.create_index('idx_exp_events_variant', 'experiment_events', ['experiment_id', 'variant'], unique=False)
    op.create_index('idx_exp_events_session', 'experiment_events', ['session_id'], unique=False)
    op.create_index('idx_exp_events_created', 'experiment_events', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_exp_events_created', table_name='experiment_events')
    op.drop_index('idx_exp_events_session', table_name='experiment_events')
    op.drop_index('idx_exp_events_variant', table_name='experiment_events')
    op.drop_index('idx_exp_events_exp_id', table_name='experiment_events')
    op.drop_table('experiment_events')

    op.drop_index('idx_experiments_created', table_name='experiments')
    op.drop_index('idx_experiments_name', table_name='experiments')
    op.drop_index('idx_experiments_status', table_name='experiments')
    op.drop_table('experiments')
