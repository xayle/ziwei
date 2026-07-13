"""add_deleted_at_to_members_and_scenarios

Revision ID: 794e459da9e2
Revises: 21f8167ee606
Create Date: 2026-05-25 18:54:54.382324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "794e459da9e2"
down_revision: Union[str, Sequence[str], None] = "21f8167ee606"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ensure_column(table: str, column: str, col: sa.Column) -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns(table)}
    if column not in cols:
        op.add_column(table, col)


def upgrade() -> None:
    """Upgrade schema — idempotent ADD COLUMN（初始迁移可能已含 deleted_at）。"""
    _ensure_column("members", "deleted_at", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    _ensure_column("scenarios", "deleted_at", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    _ensure_column("refresh_tokens", "deleted_at", sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    # 不在 downgrade 删除：初始迁移也会建这些列，回滚风险过高
    pass
