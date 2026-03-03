"""add_delegation_workflow_status

Revision ID: a1b2c3d4e5f6
Revises: 999dd22bd7c8
Create Date: 2026-03-04 12:00:00.000000

背景:
  N3.00 — 为 delegations 表添加权限申请工作流所需字段：
    status        : 申请状态，取值 pending/approved/rejected/revoked，默认 'approved'（旧数据兼容）
    requested_by  : 申请人 FK→users.id
    approved_by   : 审批人 FK→users.id
    approved_at   : 批准时间
    reject_reason : 拒绝原因文本

  旧数据迁移策略：
    UPDATE delegations SET status='approved' WHERE is_active=1 AND deleted_at IS NULL
    说明：旧系统无申请工作流概念，所有 is_active=1 且未软删除的记录均视为已批准委托。
    is_active=0 的记录视为历史无效委托，不做状态迁移（保持 'approved' 默认值即可，
    查询时通过 is_active=0 已自然过滤）。

  并发防护:
    approve 操作使用 UPDATE ... WHERE status='pending' 乐观状态检查。
    若 rowcount==0 则返回 409（已被其他管理员处理）。

  回滚注意:
    alembic downgrade -1 只回滚 DB schema，需同步在代码中还原 Delegation ORM 模型字段，
    再重启应用验证 /health 无报错。

  SQLite 约束:
    使用 batch_alter_table 完成列操作（SQLite 不支持直接 ALTER TABLE ADD COLUMN with FK）。
"""
from typing import Sequence, Union
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '999dd22bd7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """新增工作流状态字段，迁移旧数据到 status='approved'。"""
    with op.batch_alter_table("delegations", schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="approved",
        ))
        # SQLite 不强制 FK，直接添加 Integer 列；PostgreSQL 可通过后续 migration 补 FK 约束
        batch_op.add_column(sa.Column("requested_by", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("approved_by",  sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("approved_at",  sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("reject_reason", sa.Text(),   nullable=True))

    # 旧数据迁移：is_active=1 且未软删除 → status='approved'
    # 说明：旧系统无工作流，所有活跃委托均视为已批准。
    # is_active=0 的记录不做状态迁移（历史无效委托，默认值 'approved' 不影响查询）。
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE delegations SET status='approved' "
            "WHERE is_active=1 AND deleted_at IS NULL"
        )
    )


def downgrade() -> None:
    """回滚：删除工作流字段。"""
    with op.batch_alter_table("delegations", schema=None) as batch_op:
        batch_op.drop_column("reject_reason")
        batch_op.drop_column("approved_at")
        batch_op.drop_column("approved_by")
        batch_op.drop_column("requested_by")
        batch_op.drop_column("status")
