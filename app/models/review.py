"""ChartReview model — 命盘审核与版本化工作流。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar, Optional

from sqlalchemy import Column, Index, Text
from sqlmodel import Field, SQLModel


class ChartReview(SQLModel, table=True):
    """
    命盘审核记录表。

    每次命盘计算完成后，可提交审核（status=pending）。
    命理专家在管理面板中对报告进行批注、确认或驳回，并记录版本与修改原因。

    status 取值：
        pending   — 待审核（默认）
        approved  — 已确认（专家签发）
        rejected  — 已驳回（含原因）
        revised   — 已修订并再次提交
    """
    __tablename__: ClassVar[str] = "chart_reviews"
    __table_args__ = (
        Index("idx_chart_reviews_hash", "report_hash"),
        Index("idx_chart_reviews_status", "status"),
        Index("idx_chart_reviews_created", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # 命盘标识：输入参数 SHA-256 摘要（相同输入→相同摘要，便于去重查询）
    report_hash: str = Field(index=True, max_length=64)

    # 出生信息快照（JSON 字符串，含 year/month/day/hour/minute/gender/longitude）
    birth_info: str = Field(sa_column=Column(Text))

    # 命盘关键摘要（从 ZiweiResponse 提取，便于列表浏览）
    life_palace_gz: str = Field(default="", max_length=10)
    wuxing_ju_name: str = Field(default="", max_length=10)
    pattern_summary: str = Field(default="", max_length=200)  # 格局名称逗号分隔

    # 审核状态与元数据
    status: str = Field(default="pending", max_length=20)
    reviewer: str = Field(default="", max_length=100)
    notes: str = Field(default="", sa_column=Column(Text))    # 批注内容
    reject_reason: str = Field(default="", sa_column=Column(Text))

    # 版本追溯
    algorithm_version: str = Field(default="2.1.0", max_length=20)
    template_version: str = Field(default="standard", max_length=20)
    revision: int = Field(default=1)   # 修订次数

    # 时间戳
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
