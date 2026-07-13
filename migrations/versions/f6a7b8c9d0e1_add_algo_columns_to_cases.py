"""add algorithm preference columns to cases

Revision ID: f6a7b8c9d0e1
Revises: 794e459da9e2, e5f6a7b8c9d0
Create Date: 2026-07-12 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = ("794e459da9e2", "e5f6a7b8c9d0")
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("cases")}
    adds = [
        ("year_divide", sa.Column("year_divide", sa.String(), nullable=False, server_default="lichun")),
        ("day_divide", sa.Column("day_divide", sa.String(), nullable=False, server_default="solar_next")),
        ("zi_day_rule", sa.Column("zi_day_rule", sa.String(), nullable=False, server_default="sxtwl")),
    ]
    for name, col in adds:
        if name not in cols:
            op.add_column("cases", col)


def downgrade() -> None:
    op.drop_column("cases", "zi_day_rule")
    op.drop_column("cases", "day_divide")
    op.drop_column("cases", "year_divide")
