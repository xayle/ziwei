"""Temporal analysis schemas extracted from app.schemas.analysis."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

__all__ = [
    "CurrentFortuneSummaryModel",
    "LiuriLiushiModel",
    "LiuNianDetailModel",
    "MilestoneModel",
    "MonthlyFortuneModel",
]


class LiuriLiushiModel(BaseModel):
    """流日/流时最小输出（B-P2-01）。"""

    date: str
    day_ganzhi: str
    day_stem: str
    day_branch: str
    hour_ganzhi: str
    hour_stem: str
    hour_branch: str
    hour_branch_idx: int = 0
    hour_label: str = ""
    day_ten_god: str | None = None
    hour_ten_god: str | None = None
    method: str = "ganzhi_day_pillar"
    missing_fields: list[str] = Field(default_factory=list)
    flow_score: int | None = Field(None, description="流日运限联动评分 0-100（B-P2）")
    flow_score_dayun: int | None = Field(None, ge=0, le=100, description="流日大运维度分（B-P2）")
    flow_score_liunian: int | None = Field(None, ge=0, le=100, description="流日流年维度分（B-P2）")
    flow_score_geju: int | None = Field(None, ge=0, le=100, description="流日格局/用神维度分（B-P2）")
    flow_tone: str | None = Field(None, description="顺/平/逆")
    transition_hint: str | None = Field(None, description="换运/近运提醒文案（B-P2）")
    dayun_link: str | None = Field(None, description="与当前大运联动说明")
    liunian_link: str | None = Field(None, description="与流年联动说明")
    current_dayun_ganzhi: str | None = None
    current_liunian_ganzhi: str | None = None
    flow_summary: str | None = Field(None, description="流日运限联动摘要")
    warnings: list[str] = Field(default_factory=list, description="流日子时边界等提示（zi_day_rule 联动）")


class MonthlyFortuneModel(BaseModel):
    """月运模型 §4.11-G"""

    month: int = Field(..., ge=1, le=12)
    lunar_month: int = Field(..., ge=1, le=12, description="农历月份（1-12）")
    month_dizhi: str
    luck_level: Literal["吉", "平", "凶"]
    color_hint: str
    tip: str
    clash_with: str | None = None
    month_ganzhi: str | None = None
    dayun_stem: str | None = None
    relation_to_rizhu: str | None = None
    disclaimer: str = "仅供学术研究参考"


class MilestoneModel(BaseModel):
    """人生里程碑节点"""

    age: int
    year: int
    milestone_type: Literal["犯太岁", "岁运并临", "大运交接", "社会节点"]
    ganzhi_context: str
    description: str
    risk_level: Literal["高", "中", "低"]
    advice: str


class LiuNianDetailModel(BaseModel):
    """流年四维详情"""

    year: int
    ganzhi: str
    tai_sui_relations: list[str]
    clash_pillars: list[str]
    notable_months: list[int]
    annual_score: int = Field(..., ge=0, le=100)
    domain_forecasts: dict[str, str]
    optimal_action: str | None = None
    inference_tags: list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"
    ten_god: str | None = None
    flow_wuxing: str | None = None
    clash: str | None = None


class CurrentFortuneSummaryModel(BaseModel):
    """当前运势摘要（Tab 0 精简卡片）"""

    current_dayun: str
    dayun_years_remaining: int
    current_liunian: str
    this_year_domains: dict[str, str]
    top3_actions: list[str]
