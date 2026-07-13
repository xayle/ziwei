"""add analytics_events table (T089 / BE-GTM-01)

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-07-14 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "i9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "h8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "analytics_events" in tables:
        return
    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=True),
        sa.Column("volume_id", sa.String(length=32), nullable=True),
        sa.Column("client_ts", sa.DateTime(), nullable=True),
        sa.Column("properties_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_analytics_events_type", "analytics_events", ["event_type"])
    op.create_index("idx_analytics_events_user", "analytics_events", ["user_id"])
    op.create_index("idx_analytics_events_session", "analytics_events", ["session_id"])
    op.create_index("idx_analytics_events_created", "analytics_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_analytics_events_created", table_name="analytics_events")
    op.drop_index("idx_analytics_events_session", table_name="analytics_events")
    op.drop_index("idx_analytics_events_user", table_name="analytics_events")
    op.drop_index("idx_analytics_events_type", table_name="analytics_events")
    op.drop_table("analytics_events")
