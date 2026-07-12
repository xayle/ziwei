"""LlmDraft 模型 — §10 LLM 辅助解读草稿。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Column, Index, Text
from sqlmodel import Field, SQLModel


class LlmDraft(SQLModel, table=True):
    """
    LLM 辅助生成的命盘解读草稿表。

    生命周期：
        pending_review  — AI 刚生成，待命理专家审核
        approved        — 专家已确认可用
        rejected        — 专家驳回（含原因）
    """

    __tablename__: ClassVar[str] = "llm_drafts"
    __table_args__ = (
        Index("idx_llm_drafts_hash", "chart_hash"),
        Index("idx_llm_drafts_status", "status"),
        Index("idx_llm_drafts_created", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)

    # 关联命盘（同 ChartReview.report_hash）
    chart_hash: str = Field(index=True, max_length=64)

    # 生成来源
    provider: str = Field(default="mock", max_length=30)  # openai / anthropic / mock
    model: str = Field(default="mock-v1", max_length=60)
    prompt_version: str = Field(default="ziwei_interpret_v1", max_length=40)

    # 生成内容
    draft_text: str = Field(sa_column=Column(Text))
    evidence_refs_json: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="JSON: provenance evidence refs (layer/rule_id/classic_ref)",
    )

    # 人工审核字段
    status: str = Field(default="pending_review", max_length=20)
    reviewer: str = Field(default="", max_length=100)
    reviewer_notes: str = Field(default="", sa_column=Column(Text))

    # Token 用量与费用估算
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    cost_usd_estimate: float = Field(default=0.0)

    # 时间戳
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = None
    deleted_at: datetime | None = None
