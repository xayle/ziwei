"""add indexes and share_token columns

Revision ID: a2b3c4d5e6f7
Revises: f5a6b7c8d9e0
Create Date: 2026-03-23 00:00:00.000000

O5: 数据库查询索引（cases/snapshots/audit_logs）
B6: cases 表添加 share_token / share_expires_at 字段
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "a2b3c4d5e6f7"
down_revision: str | None = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── B6: share_token 列 ────────────────────────────────────
    with op.batch_alter_table("cases") as batch_op:
        batch_op.add_column(
            sa.Column("share_token", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("share_expires_at", sa.DateTime(), nullable=True)
        )

    # ── O5: 性能索引 ─────────────────────────────────────────
    # cases 表：分享 token 快查
    op.create_index("idx_cases_share_token",   "cases",      ["share_token"])

    # snapshots 表：按 case_id 快查（如果表存在）
    try:
        op.create_index("idx_snapshots_case_id", "snapshots",  ["case_id"])
    except Exception:
        pass  # 表不存在时跳过

    # audit_logs 表：按 created_at / user_id 过滤
    try:
        op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
        op.create_index("idx_audit_logs_user_id",    "audit_logs", ["user_id"])
    except Exception:
        pass  # 表不存在时跳过


def downgrade() -> None:
    # 删除索引（忽略不存在的）
    for idx, tbl in [
        ("idx_audit_logs_user_id",    "audit_logs"),
        ("idx_audit_logs_created_at", "audit_logs"),
        ("idx_snapshots_case_id",     "snapshots"),
        ("idx_cases_share_token",     "cases"),
    ]:
        try:
            op.drop_index(idx, table_name=tbl)
        except Exception:
            pass

    # 删除 share_token 列
    with op.batch_alter_table("cases") as batch_op:
        batch_op.drop_column("share_expires_at")
        batch_op.drop_column("share_token")
