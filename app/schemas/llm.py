"""Pydantic 请求/响应模型 — §10 LLM 辅助解读草稿。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 配置查询
# ---------------------------------------------------------------------------


class LlmConfigResponse(BaseModel):
    """当前 LLM provider 配置状态。"""

    provider: str
    model: str
    available: bool
    note: str = ""


# ---------------------------------------------------------------------------
# 生成请求
# ---------------------------------------------------------------------------


class LlmInterpretRequest(BaseModel):
    """提交命盘草稿生成请求。"""

    chart_hash: str = Field(..., max_length=64, description="命盘唯一哈希（来自审核记录）")
    life_palace_gz: str = Field(default="", max_length=10)
    wuxing_ju_name: str = Field(default="", max_length=10)
    pattern_summary: str = Field(default="", max_length=300)
    birth_info_summary: str = Field(default="", max_length=200, description="出生信息文字摘要")
    # Phase A2 — 八字 LLM 证据链字段（向后兼容，均有默认值）
    evidence_snippets: list[str] = Field(
        default_factory=list, description="古籍关联片段列表，由 evidence_retriever 填充"
    )
    geju_name: str = Field(default="", max_length=20, description="格局名称，如'正官格'")
    yongshen_favor: list[str] = Field(default_factory=list, description="用神喜用五行列表，如['水','木']")


# ---------------------------------------------------------------------------
# 草稿响应
# ---------------------------------------------------------------------------


class LlmDraftResponse(BaseModel):
    """单条草稿的完整响应。"""

    id: int
    chart_hash: str
    provider: str
    model: str
    prompt_version: str
    draft_text: str
    status: str
    reviewer: str
    reviewer_notes: str
    input_tokens: int
    output_tokens: int
    cost_usd_estimate: float
    created_at: datetime
    reviewed_at: datetime | None
    deleted_at: datetime | None

    model_config = {"from_attributes": True}


class LlmDraftListResponse(BaseModel):
    total: int
    items: list[LlmDraftResponse]


# ---------------------------------------------------------------------------
# 草稿审核操作
# ---------------------------------------------------------------------------


class LlmDraftUpdate(BaseModel):
    """审核/驳回草稿（仅 status / reviewer / reviewer_notes）。"""

    status: str = Field(..., pattern=r"^(approved|rejected)$")
    reviewer: str = Field(default="", max_length=100)
    reviewer_notes: str = Field(default="", max_length=2000)
