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
    with op.batch_alter_table("cases") as batch_op:
        batch_op.add_column(sa.Column("current_city", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("current_province", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("current_lon", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("current_tz", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("calendar_mode", sa.String(), nullable=False, server_default=sa.text("'gregorian'"))
        )
        batch_op.add_column(
            sa.Column("is_leap_month", sa.Boolean(), nullable=False, server_default=sa.text("false"))
        )
        batch_op.add_column(
            sa.Column("birth_time_precision", sa.String(), nullable=False, server_default=sa.text("'exact'"))
        )
        batch_op.add_column(
            sa.Column("unknown_time_fallback", sa.String(), nullable=False, server_default=sa.text("'midday'"))
        )


def downgrade() -> None:
    with op.batch_alter_table("cases") as batch_op:
        batch_op.drop_column("unknown_time_fallback")
        batch_op.drop_column("birth_time_precision")
        batch_op.drop_column("is_leap_month")
        batch_op.drop_column("calendar_mode")
        batch_op.drop_column("current_tz")
        batch_op.drop_column("current_lon")
        batch_op.drop_column("current_province")
        batch_op.drop_column("current_city")
