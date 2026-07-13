"""add entitlement column to users (T086 / BE-GTM-05)

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-14 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("users")}
    if "entitlement" not in cols:
        op.add_column(
            "users",
            sa.Column("entitlement", sa.String(length=32), nullable=False, server_default="free"),
        )


def downgrade() -> None:
    op.drop_column("users", "entitlement")
