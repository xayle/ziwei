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
    # SQLite 不支持 ADD COLUMN + FK 约束语法，使用无约束的列迁移
    with op.batch_alter_table("cases") as batch_op:
        batch_op.add_column(
            sa.Column("owner_id", sa.Integer(), nullable=True)
        )
    # 手动创建索引
    op.create_index("idx_cases_owner_id", "cases", ["owner_id"])


def downgrade() -> None:
    op.drop_index("idx_cases_owner_id", table_name="cases")
    with op.batch_alter_table("cases") as batch_op:
        batch_op.drop_column("owner_id")
