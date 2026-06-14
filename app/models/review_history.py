"""ChartReviewHistory model — 审核操作历史版本记录。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Column, Index, Text
from sqlmodel import Field, SQLModel


class ChartReviewHistory(SQLModel, table=True):
    """
    命盘审核变更历史表。

    每次 PATCH /reviews/{id} 或 bulk_action 更改审核状态时，
    自动追加一条历史记录，实现完整的审计追踪。

    通过 review_id 与 chart_reviews.id 关联。
    """

    __tablename__: ClassVar[str] = "chart_review_history"
    __table_args__ = (
        Index("idx_rv_hist_rid", "review_id"),
        Index("idx_rv_hist_changed", "changed_at"),
    )

    id: int | None = Field(default=None, primary_key=True)

    # 关联的审核记录 ID
    review_id: int = Field(index=True)

    # 本次变更后的状态
    status: str = Field(max_length=20)

    # 操作人
    reviewer: str = Field(default="", max_length=100)

    # 批注 / 拒绝原因（快照，保存变更时的内容）
    notes: str = Field(default="", sa_column=Column(Text))
    reject_reason: str = Field(default="", sa_column=Column(Text))

    # 变更类型：status_change / notes_update / bulk_action
    change_type: str = Field(default="status_change", max_length=30)

    # 变更时间（naive UTC）
    changed_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
