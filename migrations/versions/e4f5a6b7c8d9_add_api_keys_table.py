"""add_api_keys_table

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-03-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, None] = "d3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id",                 sa.Integer(),   nullable=False),
        sa.Column("user_id",            sa.Integer(),   nullable=False),
        sa.Column("name",               sa.String(64),  nullable=False),
        sa.Column("key_hash",           sa.String(64),  nullable=False),
        sa.Column("key_prefix",         sa.String(16),  nullable=False),
        sa.Column("scopes",             sa.String(128), nullable=False, server_default="read"),
        sa.Column("rate_limit_per_min", sa.Integer(),   nullable=False, server_default="60"),
        sa.Column("last_used_at",       sa.DateTime(),  nullable=True),
        sa.Column("expires_at",         sa.DateTime(),  nullable=True),
        sa.Column("revoked_at",         sa.DateTime(),  nullable=True),
        sa.Column("created_at",         sa.DateTime(),  nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_api_keys_user_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash", name="uq_api_keys_hash"),
    )
    op.create_index("idx_api_keys_hash",    "api_keys", ["key_hash"],  unique=True)
    op.create_index("idx_api_keys_user_id", "api_keys", ["user_id"],   unique=False)
    op.create_index("idx_api_keys_revoked", "api_keys", ["revoked_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_api_keys_revoked", table_name="api_keys")
    op.drop_index("idx_api_keys_user_id", table_name="api_keys")
    op.drop_index("idx_api_keys_hash",    table_name="api_keys")
    op.drop_table("api_keys")
