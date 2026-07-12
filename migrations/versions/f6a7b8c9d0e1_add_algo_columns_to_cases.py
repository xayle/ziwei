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
    with op.batch_alter_table("cases") as batch_op:
        batch_op.add_column(
            sa.Column("year_divide", sa.String(), nullable=False, server_default=sa.text("'lichun'"))
        )
        batch_op.add_column(
            sa.Column("day_divide", sa.String(), nullable=False, server_default=sa.text("'solar_next'"))
        )
        batch_op.add_column(
            sa.Column("zi_day_rule", sa.String(), nullable=False, server_default=sa.text("'sxtwl'"))
        )


def downgrade() -> None:
    with op.batch_alter_table("cases") as batch_op:
        batch_op.drop_column("zi_day_rule")
        batch_op.drop_column("day_divide")
        batch_op.drop_column("year_divide")
