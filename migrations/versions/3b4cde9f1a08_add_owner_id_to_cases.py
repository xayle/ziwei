"""add owner_id to cases

Revision ID: 3b4cde9f1a08
Revises: 26556bfe15de
Create Date: 2026-02-27 01:00:00.000000

M1 任务 1.18: Cases 表添加 owner_id FK → users.id
允许 NULL（向后兼容），添加索引。
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "3b4cde9f1a08"
down_revision: str | None = "26556bfe15de"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("cases")}
    if "owner_id" not in cols:
        op.add_column("cases", sa.Column("owner_id", sa.Integer(), nullable=True))
    indexes = {i["name"] for i in sa.inspect(bind).get_indexes("cases")}
    if "idx_cases_owner_id" not in indexes:
        op.create_index("idx_cases_owner_id", "cases", ["owner_id"])


def downgrade() -> None:
    bind = op.get_bind()
    indexes = {i["name"] for i in sa.inspect(bind).get_indexes("cases")}
    if "idx_cases_owner_id" in indexes:
        op.drop_index("idx_cases_owner_id", table_name="cases")
    cols = {c["name"] for c in sa.inspect(bind).get_columns("cases")}
    if "owner_id" in cols:
        op.drop_column("cases", "owner_id")
