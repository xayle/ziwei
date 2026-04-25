"""add_chart_cases_table

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-03-16 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chart_cases",
        sa.Column("id",              sa.Integer(),     primary_key=True, autoincrement=True),
        sa.Column("chart_hash",      sa.String(64),    nullable=False),
        sa.Column("birth_year",      sa.Integer(),     nullable=False, server_default="0"),
        sa.Column("birth_month",     sa.Integer(),     nullable=False, server_default="0"),
        sa.Column("birth_day",       sa.Integer(),     nullable=False, server_default="0"),
        sa.Column("birth_hour",      sa.Integer(),     nullable=False, server_default="0"),
        sa.Column("gender",          sa.String(4),     nullable=False, server_default=""),
        sa.Column("wuxing_ju_name",  sa.String(10),    nullable=False, server_default=""),
        sa.Column("life_palace_gz",  sa.String(10),    nullable=False, server_default=""),
        sa.Column("pattern_summary", sa.String(400),   nullable=False, server_default=""),
        sa.Column("vector_json",     sa.Text(),        nullable=False, server_default="[]"),
        sa.Column("source_label",    sa.String(32),    nullable=False, server_default="user"),
        sa.Column("created_at",      sa.DateTime(),    nullable=False),
        sa.Column("deleted_at",      sa.DateTime(),    nullable=True),
    )
    op.create_index("idx_chart_cases_hash",    "chart_cases", ["chart_hash"])
    op.create_index("idx_chart_cases_created", "chart_cases", ["created_at"])
    op.create_index("idx_chart_cases_wj",      "chart_cases", ["wuxing_ju_name"])


def downgrade() -> None:
    op.drop_index("idx_chart_cases_wj",      table_name="chart_cases")
    op.drop_index("idx_chart_cases_created", table_name="chart_cases")
    op.drop_index("idx_chart_cases_hash",    table_name="chart_cases")
    op.drop_table("chart_cases")
