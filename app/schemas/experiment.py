"""Pydantic / SQLModel 请求与响应模型 — §9 A/B 测试平台。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# 变体定义（嵌套对象）
# ---------------------------------------------------------------------------

class VariantDef(BaseModel):
    """单个变体定义。"""
    name: str = Field(..., max_length=50, description="变体标识符，如 control / variant_a")
    description: str = Field(default="", description="变体描述")
    weight: int = Field(default=50, ge=1, le=100, description="流量权重（相对值）")


# ---------------------------------------------------------------------------
# 实验 CRUD 请求
# ---------------------------------------------------------------------------

class ExperimentCreate(BaseModel):
    """创建实验请求体。"""
    name: str = Field(..., max_length=100, description="实验名称（唯一）")
    description: str = Field(default="")
    variants: List[VariantDef] = Field(
        default_factory=lambda: [
            VariantDef(name="control", description="对照组", weight=50),
            VariantDef(name="variant_a", description="实验组 A", weight=50),
        ],
        description="变体列表，最少 2 个",
    )
    target_metric: str = Field(default="chart_generated", max_length=100)
    hypothesis: str = Field(default="")
    min_sample_size: int = Field(default=100, ge=1, le=100_000)

    @field_validator("variants")
    @classmethod
    def at_least_two_variants(cls, v: List[VariantDef]) -> List[VariantDef]:
        if len(v) < 2:
            raise ValueError("实验至少需要 2 个变体")
        names = [vd.name for vd in v]
        if len(names) != len(set(names)):
            raise ValueError("变体名称不能重复")
        if "control" not in names:
            raise ValueError("变体列表必须包含名为 control 的对照组")
        return v


class ExperimentUpdate(BaseModel):
    """更新实验请求体（所有字段可选）。"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(draft|running|paused|completed)$")
    hypothesis: Optional[str] = None
    min_sample_size: Optional[int] = Field(None, ge=1, le=100_000)
    target_metric: Optional[str] = Field(None, max_length=100)


# ---------------------------------------------------------------------------
# 变体分配请求
# ---------------------------------------------------------------------------

class AssignRequest(BaseModel):
    """将会话分配到某个变体。"""
    session_id: str = Field(..., max_length=100, description="前端生成的会话 UUID")


class AssignResponse(BaseModel):
    """变体分配结果。"""
    experiment_id: int
    session_id: str
    variant: str
    is_new: bool = Field(description="True=首次分配，False=已有分配")


# ---------------------------------------------------------------------------
# 事件上报
# ---------------------------------------------------------------------------

class EventCreate(BaseModel):
    """上报一个实验事件。"""
    session_id: str = Field(..., max_length=100)
    variant: str = Field(..., max_length=50)
    event_type: str = Field(..., max_length=50)
    meta: Dict[str, Any] = Field(default_factory=dict, description="附加数据（任意 JSON）")


# ---------------------------------------------------------------------------
# 实验响应（读）
# ---------------------------------------------------------------------------

class ExperimentResponse(BaseModel):
    """单个实验的完整响应。"""
    id: int
    name: str
    description: str
    status: str
    variants: List[VariantDef]
    traffic_split: Dict[str, int]
    target_metric: str
    hypothesis: str
    min_sample_size: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ExperimentListResponse(BaseModel):
    total: int
    items: List[ExperimentResponse]


# ---------------------------------------------------------------------------
# 结果分析
# ---------------------------------------------------------------------------

class VariantStats(BaseModel):
    """单个变体的汇总统计。"""
    variant: str
    assigned: int        # 分配事件数（即样本量）
    conversions: int     # 目标事件触发次数（target_metric）
    conversion_rate: float  # conversions / assigned（0-1）
    other_events: Dict[str, int]  # 其他事件类型及计数


class ExperimentResults(BaseModel):
    """实验结果汇总。"""
    experiment_id: int
    experiment_name: str
    status: str
    target_metric: str
    min_sample_size: int
    total_assigned: int
    variants: List[VariantStats]
    winner: Optional[str] = Field(
        None,
        description="转化率最高的变体名称（仅在 total_assigned >= min_sample_size 时设置）",
    )
    note: str = Field(default="")
