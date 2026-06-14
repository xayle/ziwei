"""add_deleted_at_to_members_and_scenarios

Revision ID: 794e459da9e2
Revises: 21f8167ee606
Create Date: 2026-05-25 18:54:54.382324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '794e459da9e2'
down_revision: Union[str, Sequence[str], None] = '21f8167ee606'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — SQLite safe: only ADD COLUMN operations."""
    # members 表添加 deleted_at（软删除字段）
    op.add_column('members', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    # scenarios 表添加 deleted_at（软删除字段）
    op.add_column('scenarios', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    # refresh_tokens 表添加 deleted_at（软删除字段）
    op.add_column('refresh_tokens', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # SKIPPED: alter_column / create_index / drop_index operations that SQLite does not support
    # ### end Alembic commands ###


def _upgrade_ORIGINAL_AUTOGENERATE_DO_NOT_USE() -> None:
    """Original autogenerate output — kept for reference, NOT executed."""
    op.alter_column('api_keys', 'scopes',
               existing_type=sa.VARCHAR(length=128),
               server_default=None,
               existing_nullable=False)
    op.alter_column('api_keys', 'rate_limit_per_min',
               existing_type=sa.INTEGER(),
               server_default=None,
               existing_nullable=False)
    op.drop_index(op.f('idx_api_keys_revoked'), table_name='api_keys')
    op.drop_index(op.f('idx_api_keys_hash'), table_name='api_keys')
    op.create_index('idx_api_keys_hash', 'api_keys', ['key_hash'], unique=False)
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)
    op.drop_index(op.f('idx_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('idx_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('idx_cases_share_token'), table_name='cases')
    op.create_index(op.f('ix_cases_share_token'), 'cases', ['share_token'], unique=False)
    op.alter_column('chart_cases', 'birth_year',
               existing_type=sa.INTEGER(),
               server_default=None,
               existing_nullable=False)
    op.alter_column('chart_cases', 'birth_month',
               existing_type=sa.INTEGER(),
               server_default=None,
               existing_nullable=False)
    op.alter_column('chart_cases', 'birth_day',
               existing_type=sa.INTEGER(),
               server_default=None,
               existing_nullable=False)
    op.alter_column('chart_cases', 'birth_hour',
               existing_type=sa.INTEGER(),
               server_default=None,
               existing_nullable=False)
    op.alter_column('chart_cases', 'gender',
               existing_type=sa.VARCHAR(length=4),
               server_default=None,
               existing_nullable=False)
    op.alter_column('chart_cases', 'wuxing_ju_name',
               existing_type=sa.VARCHAR(length=10),
               server_default=None,
               existing_nullable=False)
    op.alter_column('chart_cases', 'life_palace_gz',
               existing_type=sa.VARCHAR(length=10),
               server_default=None,
               existing_nullable=False)
    op.alter_column('chart_cases', 'pattern_summary',
               existing_type=sa.VARCHAR(length=400),
               server_default=None,
               existing_nullable=False)
    op.alter_column('chart_cases', 'vector_json',
               existing_type=sa.TEXT(),
               server_default=None,
               nullable=True)
    op.alter_column('chart_cases', 'source_label',
               existing_type=sa.VARCHAR(length=32),
               server_default=None,
               existing_nullable=False)
    op.drop_index(op.f('idx_chart_cases_created'), table_name='chart_cases')
    op.drop_index(op.f('idx_chart_cases_hash'), table_name='chart_cases')
    op.drop_index(op.f('idx_chart_cases_wj'), table_name='chart_cases')
    op.create_index(op.f('ix_chart_cases_chart_hash'), 'chart_cases', ['chart_hash'], unique=False)
    op.alter_column('chart_review_history', 'reviewer',
               existing_type=sa.VARCHAR(length=100),
               server_default=None,
               existing_nullable=False)
    op.alter_column('chart_review_history', 'change_type',
               existing_type=sa.VARCHAR(length=30),
               server_default=None,
               existing_nullable=False)
    op.create_index(op.f('ix_chart_review_history_review_id'), 'chart_review_history', ['review_id'], unique=False)
    op.alter_column('delegations', 'status',
               existing_type=sa.VARCHAR(length=20),
               server_default=None,
               existing_nullable=False)
    op.drop_index(op.f('ix_delegations_from_member_id'), table_name='delegations')
    op.drop_index(op.f('ix_delegations_to_member_id'), table_name='delegations')
    op.create_index(op.f('ix_delegations_from_user_id'), 'delegations', ['from_user_id'], unique=False)
    op.create_index(op.f('ix_delegations_to_user_id'), 'delegations', ['to_user_id'], unique=False)
    op.create_foreign_key(None, 'delegations', 'users', ['requested_by'], ['id'])
    op.create_foreign_key(None, 'delegations', 'users', ['approved_by'], ['id'])
    op.drop_index(op.f('idx_events_owner_member_active'), table_name='events')
    op.create_index('idx_events_member_created', 'events', ['member_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_experiment_events_experiment_id'), 'experiment_events', ['experiment_id'], unique=False)
    op.create_index(op.f('ix_llm_drafts_chart_hash'), 'llm_drafts', ['chart_hash'], unique=False)
    op.add_column('members', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index('idx_members_created', 'members', ['created_at'], unique=False)
    op.add_column('refresh_tokens', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('scenarios', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.alter_column('snapshots', 'deleted_at',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(),
               existing_nullable=True)
    op.drop_index(op.f('idx_snapshots_case_id'), table_name='snapshots')
    op.alter_column('users', 'deleted_at',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema — SQLite safe: only DROP COLUMN operations."""
    # SQLite 3.35+ supports DROP COLUMN
    op.drop_column('refresh_tokens', 'deleted_at')
    op.drop_column('scenarios', 'deleted_at')
    op.drop_column('members', 'deleted_at')
    # ### end Alembic commands ###


def _downgrade_ORIGINAL_AUTOGENERATE_DO_NOT_USE() -> None:
    """Original autogenerate output — NOT executed."""
    op.alter_column('users', 'deleted_at',
               existing_type=sa.DateTime(),
               type_=sa.TIMESTAMP(),
               existing_nullable=True)
    op.create_index(op.f('idx_snapshots_case_id'), 'snapshots', ['case_id'], unique=False)
    op.alter_column('snapshots', 'deleted_at',
               existing_type=sa.DateTime(),
               type_=sa.TIMESTAMP(),
               existing_nullable=True)
    op.drop_column('scenarios', 'deleted_at')
    op.drop_column('refresh_tokens', 'deleted_at')
    op.drop_index('idx_members_created', table_name='members')
    op.drop_column('members', 'deleted_at')
    op.drop_index(op.f('ix_llm_drafts_chart_hash'), table_name='llm_drafts')
    op.drop_index(op.f('ix_experiment_events_experiment_id'), table_name='experiment_events')
    op.drop_index('idx_events_member_created', table_name='events')
    op.create_index(op.f('idx_events_owner_member_active'), 'events', ['owner_id', 'member_id'], unique=False)
    op.drop_constraint(None, 'delegations', type_='foreignkey')
    op.drop_constraint(None, 'delegations', type_='foreignkey')
    op.drop_index(op.f('ix_delegations_to_user_id'), table_name='delegations')
    op.drop_index(op.f('ix_delegations_from_user_id'), table_name='delegations')
    op.create_index(op.f('ix_delegations_to_member_id'), 'delegations', ['to_user_id'], unique=False)
    op.create_index(op.f('ix_delegations_from_member_id'), 'delegations', ['from_user_id'], unique=False)
    op.alter_column('delegations', 'status',
               existing_type=sa.VARCHAR(length=20),
               server_default=sa.text("'approved'"),
               existing_nullable=False)
    op.drop_index(op.f('ix_chart_review_history_review_id'), table_name='chart_review_history')
    op.alter_column('chart_review_history', 'change_type',
               existing_type=sa.VARCHAR(length=30),
               server_default=sa.text("'status_change'"),
               existing_nullable=False)
    op.alter_column('chart_review_history', 'reviewer',
               existing_type=sa.VARCHAR(length=100),
               server_default=sa.text("('')"),
               existing_nullable=False)
    op.drop_index(op.f('ix_chart_cases_chart_hash'), table_name='chart_cases')
    op.create_index(op.f('idx_chart_cases_wj'), 'chart_cases', ['wuxing_ju_name'], unique=False)
    op.create_index(op.f('idx_chart_cases_hash'), 'chart_cases', ['chart_hash'], unique=False)
    op.create_index(op.f('idx_chart_cases_created'), 'chart_cases', ['created_at'], unique=False)
    op.alter_column('chart_cases', 'source_label',
               existing_type=sa.VARCHAR(length=32),
               server_default=sa.text("'user'"),
               existing_nullable=False)
    op.alter_column('chart_cases', 'vector_json',
               existing_type=sa.TEXT(),
               server_default=sa.text("'[]'"),
               nullable=False)
    op.alter_column('chart_cases', 'pattern_summary',
               existing_type=sa.VARCHAR(length=400),
               server_default=sa.text("('')"),
               existing_nullable=False)
    op.alter_column('chart_cases', 'life_palace_gz',
               existing_type=sa.VARCHAR(length=10),
               server_default=sa.text("('')"),
               existing_nullable=False)
    op.alter_column('chart_cases', 'wuxing_ju_name',
               existing_type=sa.VARCHAR(length=10),
               server_default=sa.text("('')"),
               existing_nullable=False)
    op.alter_column('chart_cases', 'gender',
               existing_type=sa.VARCHAR(length=4),
               server_default=sa.text("('')"),
               existing_nullable=False)
    op.alter_column('chart_cases', 'birth_hour',
               existing_type=sa.INTEGER(),
               server_default=sa.text("'0'"),
               existing_nullable=False)
    op.alter_column('chart_cases', 'birth_day',
               existing_type=sa.INTEGER(),
               server_default=sa.text("'0'"),
               existing_nullable=False)
    op.alter_column('chart_cases', 'birth_month',
               existing_type=sa.INTEGER(),
               server_default=sa.text("'0'"),
               existing_nullable=False)
    op.alter_column('chart_cases', 'birth_year',
               existing_type=sa.INTEGER(),
               server_default=sa.text("'0'"),
               existing_nullable=False)
    op.drop_index(op.f('ix_cases_share_token'), table_name='cases')
    op.create_index(op.f('idx_cases_share_token'), 'cases', ['share_token'], unique=False)
    op.create_index(op.f('idx_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('idx_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    op.drop_index('idx_api_keys_hash', table_name='api_keys')
    op.create_index(op.f('idx_api_keys_hash'), 'api_keys', ['key_hash'], unique=1)
    op.create_index(op.f('idx_api_keys_revoked'), 'api_keys', ['revoked_at'], unique=False)
    op.alter_column('api_keys', 'rate_limit_per_min',
               existing_type=sa.INTEGER(),
               server_default=sa.text("'60'"),
               existing_nullable=False)
    op.alter_column('api_keys', 'scopes',
               existing_type=sa.VARCHAR(length=128),
               server_default=sa.text("'read'"),
               existing_nullable=False)
    # ### end Alembic commands ###
