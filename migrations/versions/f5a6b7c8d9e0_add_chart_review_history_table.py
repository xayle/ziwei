"""add_chart_review_history_table

Revision ID: f5a6b7c8d9e0
Revises: 45214759c8f9
Create Date: 2026-03-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, Sequence[str], None] = "45214759c8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建审核历史表。"""
    op.create_table(
        "chart_review_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("review_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reviewer", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("change_type", sa.String(length=30), nullable=False, server_default="status_change"),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rv_hist_rid", "chart_review_history", ["review_id"], unique=False)
    op.create_index("idx_rv_hist_changed", "chart_review_history", ["changed_at"], unique=False)


def downgrade() -> None:
    """删除审核历史表。"""
    op.drop_index("idx_rv_hist_changed", table_name="chart_review_history")
    op.drop_index("idx_rv_hist_rid", table_name="chart_review_history")
    op.drop_table("chart_review_history")
