"""add utm attribution columns to users and cases (T088 / BE-GTM-02)

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-07-14 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "h8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "g7b8c9d0e1f2"
branch_labels = None
depends_on = None


def _add_utm_cols(table: str) -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns(table)}
    adds = [
        ("utm_source", sa.Column("utm_source", sa.String(length=128), nullable=True)),
        ("utm_campaign", sa.Column("utm_campaign", sa.String(length=128), nullable=True)),
        ("content_id", sa.Column("content_id", sa.String(length=64), nullable=True)),
    ]
    for name, col in adds:
        if name not in cols:
            op.add_column(table, col)


def upgrade() -> None:
    _add_utm_cols("users")
    _add_utm_cols("cases")


def downgrade() -> None:
    for table in ("cases", "users"):
        op.drop_column(table, "content_id")
        op.drop_column(table, "utm_campaign")
        op.drop_column(table, "utm_source")
