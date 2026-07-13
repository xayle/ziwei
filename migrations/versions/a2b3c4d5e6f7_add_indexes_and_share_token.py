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
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("cases")}
    if "share_token" not in cols:
        op.add_column("cases", sa.Column("share_token", sa.String(), nullable=True))
    if "share_expires_at" not in cols:
        op.add_column("cases", sa.Column("share_expires_at", sa.DateTime(), nullable=True))

    indexes = {i["name"] for i in sa.inspect(bind).get_indexes("cases")}
    if "idx_cases_share_token" not in indexes and "ix_cases_share_token" not in indexes:
        op.create_index("idx_cases_share_token", "cases", ["share_token"])

    tables = set(sa.inspect(bind).get_table_names())
    if "snapshots" in tables:
        snap_idx = {i["name"] for i in sa.inspect(bind).get_indexes("snapshots")}
        if "idx_snapshots_case_id" not in snap_idx:
            try:
                op.create_index("idx_snapshots_case_id", "snapshots", ["case_id"])
            except Exception:
                pass
    if "audit_logs" in tables:
        audit_idx = {i["name"] for i in sa.inspect(bind).get_indexes("audit_logs")}
        if "idx_audit_logs_created_at" not in audit_idx:
            try:
                op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
            except Exception:
                pass
        if "idx_audit_logs_user_id" not in audit_idx:
            try:
                op.create_index("idx_audit_logs_user_id", "audit_logs", ["user_id"])
            except Exception:
                pass


def downgrade() -> None:
    for idx, tbl in [
        ("idx_audit_logs_user_id", "audit_logs"),
        ("idx_audit_logs_created_at", "audit_logs"),
        ("idx_snapshots_case_id", "snapshots"),
        ("idx_cases_share_token", "cases"),
    ]:
        try:
            op.drop_index(idx, table_name=tbl)
        except Exception:
            pass

    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("cases")}
    if "share_expires_at" in cols:
        op.drop_column("cases", "share_expires_at")
    if "share_token" in cols:
        op.drop_column("cases", "share_token")
