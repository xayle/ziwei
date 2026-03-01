"""migrate case gender M/F to male/female

Revision ID: 26556bfe15de
Revises: 92775bb6552e
Create Date: 2026-02-27 00:00:00.000000

M1 任务 1.13: 将 cases.gender 旧值 'M'→'male', 'F'→'female',
其他非标准值置为 NULL（保持列 nullable, 无约束）。
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "26556bfe15de"
down_revision: str | None = "92775bb6552e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 将旧短码规范化为新长格式
    op.execute("UPDATE cases SET gender = 'male'   WHERE gender = 'M'")
    op.execute("UPDATE cases SET gender = 'female' WHERE gender = 'F'")
    # 其他非标准值（如 'U', 'other' 等）置 NULL
    op.execute("UPDATE cases SET gender = NULL WHERE gender NOT IN ('male', 'female') AND gender IS NOT NULL")


def downgrade() -> None:
    # 回滚: 长格式还原为短码
    op.execute("UPDATE cases SET gender = 'M' WHERE gender = 'male'")
    op.execute("UPDATE cases SET gender = 'F' WHERE gender = 'female'")
