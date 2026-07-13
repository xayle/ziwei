"""add archive columns to cases

Revision ID: e5f6a7b8c9d0
Revises: 3b4cde9f1a08
Create Date: 2026-06-15 00:00:00.000000

Add the archive-style residence and calendar metadata to cases.
Keep the upgrade backward-compatible so older rows can still load safely.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "3b4cde9f1a08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 使用 ADD COLUMN（SQLite≥3.35 / PostgreSQL 均支持），避免 batch_alter 在 PG 上重建表失败
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("cases")}
    adds = [
        ("current_city", sa.Column("current_city", sa.String(), nullable=True)),
        ("current_province", sa.Column("current_province", sa.String(), nullable=True)),
        ("current_lon", sa.Column("current_lon", sa.Float(), nullable=True)),
        ("current_tz", sa.Column("current_tz", sa.String(), nullable=True)),
        ("calendar_mode", sa.Column("calendar_mode", sa.String(), nullable=False, server_default="gregorian")),
        ("is_leap_month", sa.Column("is_leap_month", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("birth_time_precision", sa.Column("birth_time_precision", sa.String(), nullable=False, server_default="exact")),
        ("unknown_time_fallback", sa.Column("unknown_time_fallback", sa.String(), nullable=False, server_default="midday")),
    ]
    for name, col in adds:
        if name not in cols:
            op.add_column("cases", col)


def downgrade() -> None:
    op.drop_column("cases", "unknown_time_fallback")
    op.drop_column("cases", "birth_time_precision")
    op.drop_column("cases", "is_leap_month")
    op.drop_column("cases", "calendar_mode")
    op.drop_column("cases", "current_tz")
    op.drop_column("cases", "current_lon")
    op.drop_column("cases", "current_province")
    op.drop_column("cases", "current_city")
