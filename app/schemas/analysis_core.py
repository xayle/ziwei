"""Core analysis schemas extracted from app.schemas.analysis."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class LifeArcModel(BaseModel):
    """一生运势总论（Tab 0 总览精简卡片 + Tab 5 摘要完整展示）"""

    overall_tier: Literal["局高", "局中", "局小"]
    early_fortune: str
    mid_fortune: str
    late_fortune: str
    peak_periods: list[str]
    caution_periods: list[str]
    life_motto: str
    inference_tags: list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"
    optimal_action: str | None = None


class GejuModel(BaseModel):
    """格局模型"""

    geju_name: str
    geju_level: Literal["上格", "中格", "下格", "无格"]
    month_stem_shishen: str
    is_broken: bool = False
    inference_tags: list[str]
    interpretation_text: str
    classic_ref: str
    disclaimer: str = "仅供学术研究参考"
    fact_data: dict | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="格局判断置信度 0-1")
    geju_detail: str | None = None
    derived_geju: str | None = Field(None, description="衍生格名（不覆盖八正格 geju_name）")
    geju_candidates: list[dict[str, object]] = Field(
        default_factory=list,
        description="格局古籍语料软提示（非硬覆盖引擎结论）",
    )
    po_geju: dict | None = Field(None, description="破格/救应结构")
    recorded_geju: str | None = Field(None, description="古籍/recorded 口径（双轨时）")
    engine_geju: str | None = Field(None, description="引擎判定格名")
    dual_track_note: str | None = Field(None, description="双轨说明")
    dual_track_id: str | None = Field(None, description="双轨用例 ID，如 ZIP09")

    @model_validator(mode="after")  # type: ignore[misc]
    def _fill_fact_data(self) -> Self:
        if self.fact_data is None:
            self.fact_data = {
                "geju_name": self.geju_name,
                "geju_level": self.geju_level,
                "month_stem_shishen": self.month_stem_shishen,
                "is_broken": self.is_broken,
                "derived_geju": self.derived_geju,
                "recorded_geju": self.recorded_geju,
                "engine_geju": self.engine_geju or self.geju_name,
            }
        return self


class PalaceItemModel(BaseModel):
    """单宫位"""

    palace_name: str
    dizhi: str
    tiangan: str | None = None
    strength: Literal["旺", "相", "休", "囚", "死"]
    shishen: str | None = None
    note: str = ""


class PalaceModel(BaseModel):
    """十二宫模型"""

    ming_gong: PalaceItemModel
    shen_gong: PalaceItemModel
    twelve_palaces: list[PalaceItemModel]
    inference_tags: list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"
    fact_data: dict | None = None

    @model_validator(mode="after")  # type: ignore[misc]
    def _fill_fact_data(self) -> Self:
        if self.fact_data is None:
            self.fact_data = {
                "ming_gong": self.ming_gong.model_dump(),
                "shen_gong": self.shen_gong.model_dump(),
                "twelve_palaces_count": len(self.twelve_palaces),
            }
        return self


class ShenshaModel(BaseModel):
    """单神煞条目"""

    name: str
    dizhi: str
    pillar: Literal["year", "month", "day", "hour"]
    is_beneficial: bool
    is_star: bool = False
    priority: Literal["A", "B", "C"] = "B"
    meaning: str
    classic_source: str
    classic_refs: list[dict[str, object]] = Field(
        default_factory=list,
        description="神煞相关古籍语料软提示",
    )
