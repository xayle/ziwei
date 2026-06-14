"""审核面板 Pydantic 模式"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator

# ---------- 请求体 ----------


class ChartReviewCreate(BaseModel):
    """提交一条命盘进入审核队列"""

    report_hash: str  # SHA-256，由前端/调用方计算
    birth_info: str  # 完整输入参数的 JSON 字符串
    life_palace_gz: str = ""  # 命宫干支，如 "甲子"
    wuxing_ju_name: str = ""  # 五行局，如 "水二局"
    pattern_summary: str = ""  # 格局摘要（逗号分隔）
    template_version: str = "standard"  # 使用的模板版本

    @field_validator("report_hash")
    @classmethod
    def hash_length(cls, v: str) -> str:
        v = v.strip()
        if len(v) == 0:
            raise ValueError("report_hash 不能为空")
        return v


class ChartReviewUpdate(BaseModel):
    """审核员更新状态/备注"""

    status: str  # approved / rejected / revised
    reviewer: str = ""
    notes: str = ""
    reject_reason: str = ""

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"approved", "rejected", "revised"}
        if v not in allowed:
            raise ValueError(f"status 必须为 {allowed} 之一")
        return v


# ---------- 响应体 ----------


class ChartReviewResponse(BaseModel):
    id: int
    report_hash: str
    birth_info: str
    life_palace_gz: str
    wuxing_ju_name: str
    pattern_summary: str
    status: str
    reviewer: str
    notes: str
    reject_reason: str
    algorithm_version: str
    template_version: str
    revision: int
    created_at: datetime
    reviewed_at: datetime | None
    deleted_at: datetime | None

    model_config = {"from_attributes": True}


class ChartReviewListResponse(BaseModel):
    total: int
    items: list[ChartReviewResponse]


# ---------- §8 批量操作 / 统计 ----------


class BulkReviewAction(BaseModel):
    """批量审核操作请求体"""

    ids: list[int]  # 要操作的审核记录 ID 列表
    action: str  # approved / rejected / revised / delete
    reviewer: str = ""
    notes: str = ""
    reject_reason: str = ""

    @field_validator("ids")
    @classmethod
    def ids_not_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("ids 不能为空")
        if len(v) > 100:
            raise ValueError("单次批量操作不得超过 100 条")
        return v


class BulkReviewResult(BaseModel):
    """批量操作结果"""

    succeeded: list[int]
    failed: list[int]
    total: int
    action: str


class ReviewStats(BaseModel):
    """审核记录统计"""

    total: int
    pending: int
    approved: int
    rejected: int
    revised: int


class ReviewHistoryItem(BaseModel):
    """单条审核历史记录"""

    id: int
    review_id: int
    status: str
    reviewer: str
    notes: str
    reject_reason: str
    change_type: str
    changed_at: datetime

    model_config = {"from_attributes": True}


class ReviewHistoryResponse(BaseModel):
    """审核历史列表"""

    review_id: int
    items: list[ReviewHistoryItem]
    total: int


class ReviewAssigneeItem(BaseModel):
    """可选审核员"""

    id: int
    username: str
    email: str
    role: str
    is_admin: bool
    is_current_user: bool = False


class ReviewAssigneeListResponse(BaseModel):
    """审核员候选列表"""

    current_username: str
    items: list[ReviewAssigneeItem]
