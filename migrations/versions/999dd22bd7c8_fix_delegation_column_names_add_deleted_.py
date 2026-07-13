"""fix_delegation_column_names_add_deleted_at

Revision ID: 999dd22bd7c8
Revises: 3b4cde9f1a08
Create Date: 2026-03-04 01:26:16.328739

背景:
  DB 中 delegations 表由旧版 models.py 创建，当时字段名为 from_member_id/to_member_id。
  新版模型（app/models/other.py）已改为 from_user_id/to_user_id，并新增 deleted_at 软删除字段。
  本次迁移使用 SQLite batch_alter_table 完成列重命名和字段添加。
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '999dd22bd7c8'
down_revision: Union[str, Sequence[str], None] = '3b4cde9f1a08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """重命名 from_member_id→from_user_id（若旧列存在），并新增 deleted_at。"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("delegations")}

    with op.batch_alter_table("delegations", schema=None) as batch_op:
        # 初始迁移已是 from_user_id；仅旧库才有 from_member_id
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
        if "deleted_at" not in cols:
            batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """回滚：还原列名，删除 deleted_at。"""
    with op.batch_alter_table("delegations", schema=None) as batch_op:
        batch_op.drop_column("deleted_at")
        batch_op.alter_column(
            "from_user_id",
            new_column_name="from_member_id",
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "to_user_id",
            new_column_name="to_member_id",
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
