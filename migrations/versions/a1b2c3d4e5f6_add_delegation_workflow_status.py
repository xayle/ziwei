"""add_delegation_workflow_status

Revision ID: a1b2c3d4e5f6
Revises: 999dd22bd7c8
Create Date: 2026-03-04 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "999dd22bd7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("delegations")}
    if "status" not in cols:
        op.add_column(
            "delegations",
            sa.Column("status", sa.String(length=20), nullable=False, server_default="approved"),
        )
    if "requested_by" not in cols:
        op.add_column("delegations", sa.Column("requested_by", sa.Integer(), nullable=True))
    if "approved_by" not in cols:
        op.add_column("delegations", sa.Column("approved_by", sa.Integer(), nullable=True))
    if "approved_at" not in cols:
        op.add_column("delegations", sa.Column("approved_at", sa.DateTime(), nullable=True))
    if "reject_reason" not in cols:
        op.add_column("delegations", sa.Column("reject_reason", sa.Text(), nullable=True))

    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE delegations SET status='approved' "
            "WHERE is_active IS TRUE AND deleted_at IS NULL"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("delegations")}
    for name in ("reject_reason", "approved_at", "approved_by", "requested_by", "status"):
        if name in cols:
            op.drop_column("delegations", name)
