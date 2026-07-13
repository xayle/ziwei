"""fix_delegation_column_names_add_deleted_at

Revision ID: 999dd22bd7c8
Revises: 3b4cde9f1a08
Create Date: 2026-03-04 01:26:16.328739
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op


revision: str = "999dd22bd7c8"
down_revision: Union[str, Sequence[str], None] = "3b4cde9f1a08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """重命名旧列（若存在）并确保 deleted_at 存在；初始迁移已齐时为 no-op。"""
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("delegations")}

    need_rename = (
        ("from_member_id" in cols and "from_user_id" not in cols)
        or ("to_member_id" in cols and "to_user_id" not in cols)
    )
    need_deleted = "deleted_at" not in cols
    if not need_rename and not need_deleted:
        return

    if need_rename or need_deleted:
        with op.batch_alter_table("delegations", schema=None) as batch_op:
            if "from_member_id" in cols and "from_user_id" not in cols:
                batch_op.alter_column(
                    "from_member_id",
                    new_column_name="from_user_id",
                    existing_type=sa.Integer(),
                    existing_nullable=False,
                )
            if "to_member_id" in cols and "to_user_id" not in cols:
                batch_op.alter_column(
                    "to_member_id",
                    new_column_name="to_user_id",
                    existing_type=sa.Integer(),
                    existing_nullable=False,
                )
            if need_deleted:
                batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    pass
