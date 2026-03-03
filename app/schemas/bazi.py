"""BaZi-related schemas for verification and full analysis."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from constants import MAX_LON, MIN_LON
from .common import RangeModel, WarningModel, BackendInfo
from .analysis import (
    WealthAnalysisModel,
    CareerAnalysisModel,
    MarriageAnalysisModel,
    HealthAnalysisModel,
    RelationshipAnalysisModel,
    PersonalityModel,
    MonthlyFortuneModel,
    GejuModel,
    PalaceModel,
    ShenshaModel,
    JewelryModel,
    FengshuiModel,
    LuckyModel,
    LifestyleModel,
    MilestoneModel,
    LiuNianDetailModel,
    LifeArcModel,
    CurrentFortuneSummaryModel,
)


class PillarModel(BaseModel):
    stem: str = Field(..., description="Heavenly stem")
    branch: str = Field(..., description="Earthly branch")
    ganzhi: Optional[str] = Field(None, description="Combined ganzhi, if available")


class PillarsModel(BaseModel):
    year: PillarModel
    month: PillarModel
    day: PillarModel
    hour: PillarModel


class RiskFlagsModel(BaseModel):
    near_shichen_boundary: bool = Field(..., description="True when within shichen boundary threshold")
    near_jieqi_boundary: bool = Field(..., description="True when within jieqi boundary threshold")
    jieqi_boundary_status: Literal["ok", "unavailable"] = Field(
        ..., description="ok=jieqi context present; unavailable=jieqi context missing so near/offset may be null"
    )
    minutes_to_shichen_boundary: Optional[float] = Field(None, description="Minutes to nearest shichen boundary")
    minutes_to_jieqi_boundary: Optional[float] = Field(None, description="Minutes to nearest jieqi boundary")


class ValidationModel(BaseModel):
    level: Literal["L0", "L1", "L2", "L3"] = Field(..., description="Validation level gate")
    mode: Literal["dual", "single"] = Field(..., description="Effective validation mode")
    recommended: Literal["beijing_time", "solar_time", "none"] = Field(
        ..., description="Recommended interpretation basis; may expand in future"
    )
    interpretation_enabled: bool = Field(..., description="Whether interpretation is allowed")
    reasons: list[str] = Field(..., description="Reason codes contributing to validation result")
    diff_fields: list[Literal["year", "month", "day", "hour"]] = Field(
        ..., description="Which pillars differ between primary and secondary"
    )
    risk_flags: RiskFlagsModel
    boundary_risk_shichen: bool = Field(False, description="True when shichen boundary risk blocks interpretation")
    boundary_risk_jieqi: bool = Field(False, description="True when jieqi boundary risk blocks interpretation")
    warnings: list[WarningModel] = Field(default_factory=list, description="Non-blocking warnings for client display")


class MarriageFlagsModel(BaseModel):
    allow_interpret: Optional[bool] = None
    guansha_mix: Optional[bool] = None
    spouse_palace_conflict: Optional[bool] = None

    model_config = ConfigDict(extra="allow")


class LoveWindowModel(BaseModel):
    age_from: Optional[float] = None
    age_to: Optional[float] = None
    label: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ChildHintModel(BaseModel):
    first: Optional[str] = None
    second: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class MarriageModel(BaseModel):
    marriage_flags: Optional[MarriageFlagsModel] = None
    love_window: Optional[list[LoveWindowModel]] = None
    child_hint: Optional[ChildHintModel] = None
    risk_hint: Optional[str] = None
    note: Optional[str] = None
    # 红线#33: 三层模型字段
    inference_tags: list[str] = Field(default_factory=list)
    interpretation_text: str = ""
    fact_data: Optional[dict] = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def _fill_fact_data(self) -> Self:
        if self.fact_data is None:
            self.fact_data = {
                "marriage_flags": self.marriage_flags.model_dump() if self.marriage_flags else None,
                "love_window": [lw.model_dump() for lw in self.love_window] if self.love_window else [],
                "child_hint": self.child_hint.model_dump() if self.child_hint else None,
                "risk_hint": self.risk_hint,
            }
        return self


class WealthModel(BaseModel):
    wealth_range: Optional[RangeModel] = None
    wealth_score: Optional[float] = None
    industry_tags: list[str] = Field(default_factory=list)
    risk_hint: Optional[str] = None
    note: Optional[str] = None
    # 红线#33: 三层模型字段
    inference_tags: list[str] = Field(default_factory=list)
    interpretation_text: str = ""
    fact_data: Optional[dict] = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def _fill_fact_data(self) -> Self:
        if self.fact_data is None:
            self.fact_data = {
                "wealth_score": self.wealth_score,
                "industry_tags": self.industry_tags,
                "wealth_range": self.wealth_range.model_dump() if self.wealth_range else None,
                "risk_hint": self.risk_hint,
            }
        return self


class SocialModel(BaseModel):
    taohua_hit: Optional[bool] = None
    relation_conflict: Optional[bool] = None
    taohua_year_hit: list[int] = Field(default_factory=list)
    social_hint: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class TenGodsModel(BaseModel):
    year: Optional[str] = None
    month: Optional[str] = None
    day: Optional[str] = None
    hour: Optional[str] = None


class StrengthFactorModel(BaseModel):
    name: str
    score: float
    reason: Optional[str] = None


class DayMasterStrengthModel(BaseModel):
    score: float = 0.0
    tier: str = "pending"
    factors: list[StrengthFactorModel] = Field(default_factory=list)


class WuXingScoreModel(BaseModel):
    wood: float = 0.0
    fire: float = 0.0
    earth: float = 0.0
    metal: float = 0.0
    water: float = 0.0


class WuXingBreakdownModel(BaseModel):
    stem_contrib: dict[str, float] = Field(default_factory=dict)
    branch_contrib: dict[str, float] = Field(default_factory=dict)
    hidden_contrib: dict[str, float] = Field(default_factory=dict)
    weights: dict[str, float] = Field(default_factory=dict)


class YongShenModel(BaseModel):
    favor: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    rationale: Optional[str] = None


class DaYunItemModel(BaseModel):
    start_age: Optional[float] = None
    start_year: Optional[int] = None
    start_age_months: Optional[int] = None
    stem: Optional[str] = None
    branch: Optional[str] = None
    ten_god: Optional[str] = None
    flow_wuxing: Optional[str] = None
    wealth_range: Optional[RangeModel] = None
    wealth_hint: Optional[str] = None
    health_hint: Optional[str] = None
    love_hint: Optional[str] = None
    child_hint: Optional[str] = None
    refs: Optional[list[dict]] = None
    narrative: Optional[str] = None   # M3.02: 大运叙事400-600字


class DaYunModel(BaseModel):
    method: str = "pending"
    boundary: str = "pending"
    direction: Optional[str] = None
    direction_basis: Optional[dict] = None
    start_age: Optional[int] = None
    start_age_months: Optional[int] = None
    anchor_jieqi_name: Optional[str] = None
    anchor_jieqi_dt: Optional[str] = None
    items: list[DaYunItemModel] = Field(default_factory=list)


class LiuNianItemModel(BaseModel):
    year: Optional[int] = None
    stem: Optional[str] = None
    branch: Optional[str] = None
    ten_god: Optional[str] = None
    clash: Optional[str] = None


class LiuNianResultModel(BaseModel):
    years_used: list[int] = Field(default_factory=list)
    items: list[LiuNianItemModel] = Field(default_factory=list)


class BaziRawDayunModel(BaseModel):
    birth_to_jieqi_days: Optional[float] = None
    computed_months_before_rounding: Optional[float] = None
    rounding_applied: Optional[str] = None
    anchor_jieqi_name: Optional[str] = None
    anchor_jieqi_dt: Optional[str] = None
    direction: Optional[str] = None
    direction_basis: dict[str, Any] = Field(
        default_factory=lambda: {"gender": None, "year_stem": None, "year_stem_yinyang": None}
    )
    status: str = "placeholder"
    sequence_start: str = "from_month_pillar"


class BaziRawModel(BaseModel):
    tz_used: str
    dt_effective_local: str
    dt_effective_utc: str
    dt_effective_local_offset_minutes: int
    solar_time_offset_minutes: int
    day_boundary_rule_used: str = "zi_initial"
    day_boundary_crossed: bool = False
    jieqi_context: dict[str, Any] = Field(default_factory=dict)
    dayun: BaziRawDayunModel = Field(default_factory=BaziRawDayunModel)


class BaziMethodsModel(BaseModel):
    day_boundary_rule: str = "zi_initial"
    solar_time_rule: str = "longitude_only"
    calendar_calc: str = "sxtwl"
    pillar_month_rule: str = "jieqi"
    ten_god_basis: str = "stem_only"
    liunian_calc: str = "gregorian_year_ganzhi"
    liunian_range_default: str = "[-2,2]"
    dayun_method: str = "sxtwl_next_jieqi_div3"
    dayun_boundary: str = "half_open"
    dayun_jieqi_anchor: str = "next"
    dayun_rounding: str = "ceil"
    dayun_days_per_month: int = 3
    dayun_direction_rule: str = "gender+year_stem_yinyang"
    wuxing_method: str = "stem_branch_hidden_weighted_v1"
    wuxing_weights_version: str = "v1"
    strength_method: str = "season_root_help_score_v1"
    strength_tier_rule: str = "score_threshold_v1"
    yongshen_method: str = "wuxing_balance_from_strength_v1"
    yongshen_output_style: str = "elements_only"
    warnings_format: str = "object_v1"


class VerifyRequest(BaseModel):
    """验证请求"""
    dt: datetime = Field(..., description="Input datetime; aware or naive ISO-8601")
    lon: float = Field(..., description="Longitude in degrees within supported range")
    mode: Literal["dual", "single"] = Field("dual", description="Requested mode")
    solar_time_enabled: bool = Field(False, description="Enable solar-time adjustment when true")
    tz: str = Field("Asia/Shanghai", description="Timezone used only when dt is naive")
    gender: Optional[Literal["male", "female"]] = Field(None, description="Gender for dayun direction: male/female")
    city_tier: Optional[Literal["一线", "新一线", "其余"]] = Field(
        "其余", description="城市层级，影响财富数额地区系数：一线×1.8 / 新一线×1.2 / 其余×1.0 (M3.03)"
    )
    industry: Optional[Literal["金融IT", "教育公务", "其余"]] = Field(
        "其余", description="行业，影响财富行业系数：金融IT×1.5 / 教育公务×0.8 / 其余×1.0 (M3.03)"
    )

    @model_validator(mode="after")
    def validate_lon(self):  # type: ignore[override]
        if not (MIN_LON <= self.lon <= MAX_LON):
            raise ValueError(f"lon must be between {MIN_LON} and {MAX_LON}")
        return self


class BatchVerifyRequest(BaseModel):
    """N5.03 批量验证请求，最多 50 条"""
    items: List[VerifyRequest] = Field(..., description="批量请求列表，最多 50 条")

    @field_validator("items")
    @classmethod
    def validate_items_length(cls, v: List[VerifyRequest]) -> List[VerifyRequest]:
        if len(v) > 50:
            raise ValueError(f"items 最多 50 条，当前 {len(v)} 条")
        if len(v) == 0:
            raise ValueError("items 不能为空")
        return v


class BatchVerifyResponse(BaseModel):
    """N5.03 批量验证响应"""
    results: List[dict] = Field(default_factory=list, description="成功结果列表（有序，与 items 对应）")
    failed: List[dict] = Field(default_factory=list, description="失败列表 [{index: int, error: str}]")


class VerifyResponse(BaseModel):
    """验证响应 - 完整的八字分析结果"""
    api_version: str = Field(..., description="API semantic version")
    rule_version: str = Field(..., description="Rule/data version")
    request_id: str = Field(..., description="Request correlation id")
    backend: BackendInfo
    mode_requested: Literal["dual", "single"] = Field(..., description="Echo of requested mode")
    mode_effective: Literal["dual", "single"] = Field(..., description="Actual mode after fallback")
    pillars_primary: PillarsModel
    pillars_secondary: Optional[PillarsModel] = Field(None, description="Secondary pillars when dual mode succeeds")
    risk_flags: RiskFlagsModel
    validation: ValidationModel
    solar_time_offset_minutes: float = Field(
        ..., description="Solar correction applied in minutes; 0.0 when solar_time_enabled is false"
    )
    dt_input: str = Field(..., description="Parsed input datetime re-serialized via isoformat()")
    dt_effective_utc8: str = Field(..., description="Datetime normalized to Asia/Shanghai")
    tz: str = Field(..., description="Echo of requested timezone; only used when dt is naive")
    wuxing_score: Optional[WuXingScoreModel] = None
    wuxing_breakdown: Optional[WuXingBreakdownModel] = Field(None, description="五行分解（藏干贡献 RL#1）")
    day_master_strength: Optional[DayMasterStrengthModel] = None
    yongshen: Optional[YongShenModel] = None
    ten_gods: Optional[TenGodsModel] = None
    wealth: Optional[WealthModel] = None
    marriage: Optional[MarriageModel] = None
    social: Optional[SocialModel] = None
    dayun: Optional[DaYunModel] = None
    # ── M2 新增字段 ──────────────────────────────────────────────────────
    geju: Optional[GejuModel] = Field(None, description="格局分析")
    palace: Optional[PalaceModel] = Field(None, description="十二宫分析")
    shensha: Optional[list[ShenshaModel]] = Field(None, description="神煞列表")
    wealth_analysis: Optional[WealthAnalysisModel] = Field(None, description="财运详细分析")
    career: Optional[CareerAnalysisModel] = Field(None, description="事业分析")
    marriage_analysis: Optional[MarriageAnalysisModel] = Field(None, description="婚姻详细分析")
    health: Optional[HealthAnalysisModel] = Field(None, description="健康分析")
    relationship: Optional[RelationshipAnalysisModel] = Field(None, description="六亲人际分析")
    personality: Optional[PersonalityModel] = Field(None, description="性格分析")
    monthly_fortune: Optional[list[MonthlyFortuneModel]] = Field(None, description="月运分析（12月）")
    jewelry: Optional[JewelryModel] = Field(None, description="首饰推荐")
    fengshui: Optional[FengshuiModel] = Field(None, description="风水布局建议")
    lucky: Optional[LuckyModel] = Field(None, description="开运数字/颜色/方位")
    lifestyle: Optional[LifestyleModel] = Field(None, description="生活方式建议")
    milestones: Optional[list[MilestoneModel]] = Field(None, description="人生里程碑")
    liunian: Optional[LiuNianResultModel] = Field(None, description="流年排盘（当前年份前后）")
    liunian_detail: Optional[list[LiuNianDetailModel]] = Field(None, description="流年四维分解")
    life_arc: Optional[LifeArcModel] = Field(None, description="人生格局弧线")
    current_fortune_summary: Optional[CurrentFortuneSummaryModel] = Field(None, description="当前运势摘要")
    # ── 任务 2.10: rule_version per-module dict ───────────────────────
    rule_version_detail: Optional[Dict[str, str]] = Field(
        None, description="各模块规则版本字典（M2新增，per-module versions）"
    )
    dizhi_relations: Optional[list[dict]] = Field(
        None, description="地支关系（全合/半合/拱合/六合/六冲）列表，见红线14"
    )
    tiangan_clashes: Optional[list[dict]] = Field(
        None, description="天干相克关系，scope=day_related，见P0-11"
    )
    # ── N2.05 五行均衡评分与建议 ────────────────────────────────────────────
    wuxing_balance_score: Optional[float] = Field(None, description="五行均衡分 [0-100]")
    wuxing_weak: Optional[list[str]] = Field(None, description="偏缺五行列表，如 [\"水\", \"木\"]")
    wuxing_strong: Optional[list[str]] = Field(None, description="偏旺五行列表，如 [\"火\"]")
    balance_advice: Optional[str] = Field(None, description="一句话五行补救建议")
    # ── N2.07 流年运势 ───────────────────────────────────────────────────────
    yearly_fortune: Optional[list[dict]] = Field(None, description="流年运势列表（当前大运覆盖的年份）")


class BaziFullRequest(BaseModel):
    """完整BaZi分析请求"""
    dt: datetime = Field(..., description="Input datetime; aware or naive ISO-8601")
    lon: float = Field(..., description="Longitude in degrees within supported range")
    mode: Literal["dual", "single"] = Field("dual", description="Requested mode")
    solar_time_enabled: bool = Field(False, description="Enable solar-time adjustment when true")
    tz: str = Field("Asia/Shanghai", description="Timezone used only when dt is naive")
    liunian_years: Optional[list[int]] = Field(None, description="Optional liunian year span [-N, N]")

    @model_validator(mode="after")
    def validate_lon(self):  # type: ignore[override]
        if not (MIN_LON <= self.lon <= MAX_LON):
            raise ValueError(f"lon must be between {MIN_LON} and {MAX_LON}")
        return self


class BaziFullResponse(BaseModel):
    """完整的八字分析响应"""
    api_version: str
    rule_version: str
    schema_version: str = "bazi_full@5.0"
    request_id: str
    warnings: list[WarningModel] = Field(default_factory=list)
    methods: BaziMethodsModel
    pillars_primary: PillarsModel
    pillars_secondary: Optional[PillarsModel] = None
    ten_gods: TenGodsModel = Field(default_factory=TenGodsModel)
    day_master_strength: DayMasterStrengthModel = Field(default_factory=DayMasterStrengthModel)
    wuxing_score: WuXingScoreModel = Field(default_factory=WuXingScoreModel)
    wuxing_breakdown: WuXingBreakdownModel = Field(default_factory=WuXingBreakdownModel)
    yongshen: YongShenModel = Field(default_factory=YongShenModel)
    dayun: DaYunModel = Field(default_factory=DaYunModel)
    liunian: LiuNianResultModel = Field(default_factory=LiuNianResultModel)
    raw: BaziRawModel
    # ── M2 新增字段 ──────────────────────────────────────────────────────
    geju: Optional[GejuModel] = None
    palace: Optional[PalaceModel] = None
    shensha: Optional[list[ShenshaModel]] = None
    wealth_analysis: Optional[WealthAnalysisModel] = None
    career: Optional[CareerAnalysisModel] = None
    marriage_analysis: Optional[MarriageAnalysisModel] = None
    health: Optional[HealthAnalysisModel] = None
    relationship: Optional[RelationshipAnalysisModel] = None
    personality: Optional[PersonalityModel] = None
    monthly_fortune: Optional[list[MonthlyFortuneModel]] = None
    jewelry: Optional[JewelryModel] = None
    fengshui: Optional[FengshuiModel] = None
    lucky: Optional[LuckyModel] = None
    lifestyle: Optional[LifestyleModel] = None
    milestones: Optional[list[MilestoneModel]] = None
    liunian_detail: Optional[list[LiuNianDetailModel]] = None
    life_arc: Optional[LifeArcModel] = None
    current_fortune_summary: Optional[CurrentFortuneSummaryModel] = None
