"""BaZi-related schemas for verification and full analysis."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from constants import MAX_LON, MIN_LON

from .analysis import (
    CareerAnalysisModel,
    CurrentFortuneSummaryModel,
    FengshuiModel,
    GejuModel,
    HealthAnalysisModel,
    JewelryModel,
    LifeArcModel,
    LifestyleModel,
    LiuNianDetailModel,
    LuckyModel,
    MarriageAnalysisModel,
    MilestoneModel,
    MonthlyFortuneModel,
    PalaceModel,
    PersonalityModel,
    RelationshipAnalysisModel,
    ShenshaModel,
    WealthAnalysisModel,
)
from .common import BackendInfo, RangeModel, WarningModel
from .disclaimer import DisclaimerBlockModel
from .provenance import ResponseProvenance


class EvidenceItemModel(BaseModel):
    title: str
    value: str
    source: str | None = None
    confidence: Literal["high", "medium", "low"] | None = None


class TimelinePointModel(BaseModel):
    year: int
    label: str
    summary: str
    tone: Literal["danger", "warn", "neutral", "info", "current"] = "neutral"


class RelationItemModel(BaseModel):
    type: Literal["刑", "冲", "合", "害", "破", "空亡", "干支互动"]
    subject: str
    target: str | None = None
    summary: str
    strength: Literal["strong", "medium", "weak"] | None = None


class AdjustmentSummaryModel(BaseModel):
    climate: Literal["寒", "暖", "燥", "湿", "平"] | None = None
    climate_source: str | None = None
    climate_reason: str | None = None
    tiaohou: str | None = None
    balance_direction: str | None = None
    season_summary: str | None = None
    rationale: list[str] = Field(default_factory=list)


class ConfidenceSummaryModel(BaseModel):
    level: Literal["high", "medium", "low"] = "medium"
    score: int | None = None
    score_components: dict[str, float] = Field(default_factory=dict)
    score_reason: str | None = None
    evidence: list[EvidenceItemModel] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    inference_notes: list[str] = Field(default_factory=list)
    blocked_fields: list[str] = Field(default_factory=list)


class BaziStructuralSummaryModel(BaseModel):
    core_snapshot: dict[str, object] = Field(default_factory=dict)
    relation_summary: dict[str, object] = Field(default_factory=dict)
    adjustment_summary: AdjustmentSummaryModel | None = None
    timeline_summary: dict[str, list[TimelinePointModel]] = Field(default_factory=dict)
    confidence_summary: ConfidenceSummaryModel | None = None
    report_summary: dict[str, object] = Field(default_factory=dict)


class PillarModel(BaseModel):
    stem: str = Field(..., description="Heavenly stem")
    branch: str = Field(..., description="Earthly branch")
    ganzhi: str | None = Field(None, description="Combined ganzhi, if available")


class PillarsModel(BaseModel):
    year: PillarModel
    month: PillarModel
    day: PillarModel
    hour: PillarModel


class HiddenStemDetailModel(BaseModel):
    stem: str
    weight: float | None = None
    element: str | None = None
    ten_god: str | None = None
    source: str | None = None


class PillarShenshaDetailModel(BaseModel):
    name: str
    priority: str
    polarity: str
    pillar: str
    topic: str
    note: str
    classic: str | None = None
    source: str | None = None


class PillarDetailModel(BaseModel):
    label: str
    stem: str | None = None
    branch: str | None = None
    ganzhi: str | None = None
    ten_god: str | None = None
    hidden_stems: list[HiddenStemDetailModel] = Field(default_factory=list)
    xingyun: str | None = None
    self_seat: str | None = None
    self_seat_source: str | None = None
    kongwang: list[str] = Field(default_factory=list)
    kongwang_source: str | None = None
    kongwang_hit: bool = False
    nayin: str | None = None
    shensha: list[PillarShenshaDetailModel] = Field(default_factory=list)
    wuxing: str | None = None
    yin_yang: str | None = None


class RiskFlagsModel(BaseModel):
    near_shichen_boundary: bool = Field(..., description="True when within shichen boundary threshold")
    near_jieqi_boundary: bool = Field(..., description="True when within jieqi boundary threshold")
    jieqi_boundary_status: Literal["ok", "unavailable"] = Field(
        ..., description="ok=jieqi context present; unavailable=jieqi context missing so near/offset may be null"
    )
    minutes_to_shichen_boundary: float | None = Field(None, description="Minutes to nearest shichen boundary")
    minutes_to_jieqi_boundary: float | None = Field(None, description="Minutes to nearest jieqi boundary")


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
    allow_interpret: bool | None = None
    guansha_mix: bool | None = None
    spouse_palace_conflict: bool | None = None

    model_config = ConfigDict(extra="allow")


class LoveWindowModel(BaseModel):
    age_from: float | None = None
    age_to: float | None = None
    label: str | None = None

    model_config = ConfigDict(extra="allow")


class ChildHintModel(BaseModel):
    first: str | None = None
    second: str | None = None

    model_config = ConfigDict(extra="allow")


class MarriageModel(BaseModel):
    marriage_flags: MarriageFlagsModel | None = None
    love_window: list[LoveWindowModel] | None = None
    child_hint: ChildHintModel | None = None
    risk_hint: str | None = None
    note: str | None = None
    # 红线#33: 三层模型字段
    inference_tags: list[str] = Field(default_factory=list)
    interpretation_text: str = ""
    fact_data: dict | None = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")  # type: ignore[misc]
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
    wealth_range: RangeModel | None = None
    wealth_score: float | None = None
    industry_tags: list[str] = Field(default_factory=list)
    risk_hint: str | None = None
    note: str | None = None
    # 红线#33: 三层模型字段
    inference_tags: list[str] = Field(default_factory=list)
    interpretation_text: str = ""
    fact_data: dict | None = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")  # type: ignore[misc]
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
    taohua_hit: bool | None = None
    relation_conflict: bool | None = None
    taohua_year_hit: list[int] = Field(default_factory=list)
    social_hint: str | None = None

    model_config = ConfigDict(extra="allow")


class TenGodsModel(BaseModel):
    year: str | None = None
    month: str | None = None
    day: str | None = None
    hour: str | None = None


class ShishenPillarSummaryModel(BaseModel):
    pillar: Literal["year", "month", "day", "hour"]
    stem: str | None = None
    ten_god: str | None = None
    note: str | None = None


class ShishenContributionModel(BaseModel):
    pillar: Literal["year", "month", "day", "hour"]
    source: Literal["stem", "hidden"]
    stem: str
    hidden_stem: str | None = None
    ten_god: str | None = None
    weight: float = 0.0
    element: str | None = None


class ShishenSummaryModel(BaseModel):
    day_stem: str
    day_element: str | None = None
    day_yinyang: str | None = None
    pillars: dict[str, ShishenPillarSummaryModel] = Field(default_factory=dict)
    score_total: float = 0.0
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    score_share: dict[str, float] = Field(default_factory=dict)
    dominant: list[str] = Field(default_factory=list)
    hidden_contrib_by_ten_god: dict[str, float] = Field(default_factory=dict)
    contributions: list[ShishenContributionModel] = Field(default_factory=list)
    liuqin_summary: list[str] = Field(default_factory=list)
    summary_text: str = ""


class StrengthFactorModel(BaseModel):
    name: str
    score: float
    weight: float | None = Field(None, description="因子权重 0-1（B-02）")
    weighted_score: float | None = Field(None, description="加权得分")
    reason: str | None = None


class DayMasterStrengthModel(BaseModel):
    score: float = 0.0
    tier: str = "pending"
    factors: list[StrengthFactorModel] = Field(default_factory=list)
    strength_factors: list[StrengthFactorModel] = Field(
        default_factory=list,
        description="旺衰多因子明细（B-02，与 factors 同源）",
    )


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
    rationale: str | None = None
    recorded_favor: list[str] = Field(default_factory=list, description="古籍/recorded 用神五行")
    engine_favor: list[str] = Field(default_factory=list, description="引擎 favor 口径")
    dual_track_note: str | None = Field(None, description="用神双轨说明")
    dual_track_id: str | None = Field(None, description="双轨用例 ID，如 ZIP01")


class DaYunItemModel(BaseModel):
    start_age: float | None = None
    start_year: int | None = None
    start_age_months: int | None = None
    stem: str | None = None
    branch: str | None = None
    ten_god: str | None = None
    hidden_stems: list[HiddenStemDetailModel] = Field(default_factory=list)
    xingyun: str | None = None
    self_seat: str | None = None
    self_seat_source: str | None = None
    kongwang: list[str] = Field(default_factory=list)
    kongwang_source: str | None = None
    kongwang_hit: bool = False
    nayin: str | None = None
    shensha: list[PillarShenshaDetailModel] = Field(default_factory=list)
    wuxing: str | None = None
    yin_yang: str | None = None
    flow_wuxing: str | None = None
    wealth_range: RangeModel | None = None
    wealth_hint: str | None = None
    health_hint: str | None = None
    love_hint: str | None = None
    child_hint: str | None = None
    refs: list[dict] | None = None
    narrative: str | None = None  # M3.02: 大运叙事400-600字


class DaYunModel(BaseModel):
    method: str = "pending"
    boundary: str = "pending"
    direction: str | None = None
    direction_basis: dict | None = None
    start_age: int | None = None
    start_age_months: int | None = None
    start_age_days: int | None = Field(None, description="Birth-to-first-dayun days (B-P2-03)")
    transition_hint: str | None = Field(None, description="换运提示文案")
    days_to_next_transition: int | None = Field(None, description="距下一运剩余天数（B-P2）")
    next_transition_age: int | None = Field(None, description="下一运起运虚岁")
    next_transition_ganzhi: str | None = Field(None, description="下一运干支")
    next_transition_hint: str | None = Field(None, description="动态换运提醒文案")
    anchor_jieqi_name: str | None = None
    anchor_jieqi_dt: str | None = None
    items: list[DaYunItemModel] = Field(default_factory=list)


class LiuNianItemModel(BaseModel):
    year: int | None = None
    stem: str | None = None
    branch: str | None = None
    ten_god: str | None = None
    hidden_stems: list[HiddenStemDetailModel] = Field(default_factory=list)
    xingyun: str | None = None
    self_seat: str | None = None
    self_seat_source: str | None = None
    kongwang: list[str] = Field(default_factory=list)
    kongwang_source: str | None = None
    kongwang_hit: bool = False
    nayin: str | None = None
    shensha: list[PillarShenshaDetailModel] = Field(default_factory=list)
    wuxing: str | None = None
    yin_yang: str | None = None
    clash: str | None = None


class LiuNianResultModel(BaseModel):
    years_used: list[int] = Field(default_factory=list)
    items: list[LiuNianItemModel] = Field(default_factory=list)


class BaziRawDayunModel(BaseModel):
    birth_to_jieqi_days: float | None = None
    computed_months_before_rounding: float | None = None
    rounding_applied: str | None = None
    anchor_jieqi_name: str | None = None
    anchor_jieqi_dt: str | None = None
    direction: str | None = None
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
    day_boundary_rule: str = "sxtwl"
    zi_day_rule: str = Field(
        "sxtwl",
        description="子时换日规则：sxtwl | early_zi_prev_day | early_zi_same_day",
    )
    pillars_layer: str = Field(
        "",
        description="四柱计算层标识，如 bazi_engine.pillars.v2",
    )
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
    gender: Literal["male", "female"] | None = Field(None, description="Gender for dayun direction: male/female")
    city_tier: Literal["一线", "新一线", "其余"] | None = Field(
        "其余", description="城市层级，影响财富数额地区系数：一线×1.8 / 新一线×1.2 / 其余×1.0 (M3.03)"
    )
    industry: Literal["金融IT", "教育公务", "其余"] | None = Field(
        "其余", description="行业，影响财富行业系数：金融IT×1.5 / 教育公务×0.8 / 其余×1.0 (M3.03)"
    )
    target_date: datetime | None = Field(None, description="Optional target date for liuri/liushi")
    target_hour: int | None = Field(None, ge=0, le=23, description="Target hour 0-23 for liushi")
    include_liuri: bool | None = Field(
        None,
        description="是否返回流日/流时；verify 默认 False，设为 True 时未传 target_date 使用当天",
    )

    @model_validator(mode="after")
    def validate_lon(self):  # type: ignore[override]
        if not (MIN_LON <= self.lon <= MAX_LON):
            raise ValueError(f"lon must be between {MIN_LON} and {MAX_LON}")
        return self


class BatchVerifyRequest(BaseModel):
    """N5.03 批量验证请求，最多 50 条"""

    items: list[VerifyRequest] = Field(..., description="批量请求列表，最多 50 条")

    @field_validator("items")
    @classmethod
    def validate_items_length(cls, v: list[VerifyRequest]) -> list[VerifyRequest]:
        if len(v) > 50:
            raise ValueError(f"items 最多 50 条，当前 {len(v)} 条")
        if len(v) == 0:
            raise ValueError("items 不能为空")
        return v


class BatchVerifyResponse(BaseModel):
    """N5.03 批量验证响应"""

    results: list[dict] = Field(default_factory=list, description="成功结果列表（有序，与 items 对应）")
    failed: list[dict] = Field(default_factory=list, description="失败列表 [{index: int, error: str}]")


class VerifyResponse(BaseModel):
    """验证响应 - 完整的八字分析结果"""

    api_version: str = Field(..., description="API semantic version")
    engine_version: str = Field(default="v1", description="Engine version used for calculation (R38)")
    calc_ms: float = Field(default=0.0, description="Calculation elapsed time in milliseconds (R38)")
    rule_version: str = Field(..., description="Rule/data version")
    request_id: str = Field(..., description="Request correlation id")
    backend: BackendInfo
    mode_requested: Literal["dual", "single"] = Field(..., description="Echo of requested mode")
    mode_effective: Literal["dual", "single"] = Field(..., description="Actual mode after fallback")
    pillars_primary: PillarsModel
    pillars_secondary: PillarsModel | None = Field(None, description="Secondary pillars when dual mode succeeds")
    risk_flags: RiskFlagsModel
    validation: ValidationModel
    solar_time_offset_minutes: float = Field(
        ..., description="Solar correction applied in minutes; 0.0 when solar_time_enabled is false"
    )
    dt_input: str = Field(..., description="Parsed input datetime re-serialized via isoformat()")
    dt_effective_utc8: str = Field(..., description="Datetime normalized to Asia/Shanghai")
    tz: str = Field(..., description="Echo of requested timezone; only used when dt is naive")
    wuxing_score: WuXingScoreModel | None = None
    wuxing_breakdown: WuXingBreakdownModel | None = Field(None, description="五行分解（藏干贡献 RL#1）")
    day_master_strength: DayMasterStrengthModel | None = None
    yongshen: YongShenModel | None = None
    ten_gods: TenGodsModel | None = None
    shishen_summary: ShishenSummaryModel | None = None
    wealth: WealthModel | None = None
    marriage: MarriageModel | None = None
    social: SocialModel | None = None
    dayun: DaYunModel | None = None
    # ── M2 新增字段 ──────────────────────────────────────────────────────
    geju: GejuModel | None = Field(None, description="格局分析")
    palace: PalaceModel | None = Field(None, description="十二宫分析")
    shensha: list[ShenshaModel] | None = Field(None, description="神煞列表")
    wealth_analysis: WealthAnalysisModel | None = Field(None, description="财运详细分析")
    career: CareerAnalysisModel | None = Field(None, description="事业分析")
    marriage_analysis: MarriageAnalysisModel | None = Field(None, description="婚姻详细分析")
    health: HealthAnalysisModel | None = Field(None, description="健康分析")
    relationship: RelationshipAnalysisModel | None = Field(None, description="六亲人际分析")
    personality: PersonalityModel | None = Field(None, description="性格分析")
    monthly_fortune: list[MonthlyFortuneModel] | None = Field(None, description="月运分析（12月）")
    jewelry: JewelryModel | None = Field(None, description="首饰推荐")
    fengshui: FengshuiModel | None = Field(None, description="风水布局建议")
    lucky: LuckyModel | None = Field(None, description="开运数字/颜色/方位")
    lifestyle: LifestyleModel | None = Field(None, description="生活方式建议")
    milestones: list[MilestoneModel] | None = Field(None, description="人生里程碑")
    liunian: LiuNianResultModel | None = Field(None, description="流年排盘（当前年份前后）")
    liunian_detail: list[LiuNianDetailModel] | None = Field(None, description="流年四维分解")
    life_arc: LifeArcModel | None = Field(None, description="人生格局弧线")
    current_fortune_summary: CurrentFortuneSummaryModel | None = Field(None, description="当前运势摘要")
    # ── 任务 2.10: rule_version per-module dict ───────────────────────
    rule_version_detail: dict[str, str] | None = Field(
        None, description="各模块规则版本字典（M2新增，per-module versions）"
    )
    dizhi_relations: list[dict] | None = Field(None, description="地支关系（全合/半合/拱合/六合/六冲）列表，见红线14")
    tiangan_clashes: list[dict] | None = Field(None, description="天干相克关系，scope=day_related，见P0-11")
    # ── N2.05 五行均衡评分与建议 ────────────────────────────────────────────
    wuxing_balance_score: float | None = Field(None, description="五行均衡分 [0-100]")
    wuxing_weak: list[str] | None = Field(None, description='偏缺五行列表，如 ["水", "木"]')
    wuxing_strong: list[str] | None = Field(None, description='偏旺五行列表，如 ["火"]')
    balance_advice: str | None = Field(None, description="一句话五行补救建议")
    # ── N2.07 流年运势 ───────────────────────────────────────────────────────
    yearly_fortune: list[dict] | None = Field(None, description="流年运势列表（当前大运覆盖的年份）")
    # ── N5.07 起运年龄 ────────────────────────────────────────────────────────
    start_dayun_age: float | None = Field(
        None, description="大运起运年龄（精确到0.1岁，N5.07）"
    )  # ── 命局综合总评（400-600字六段结构） ──────────────────────────────────
    bazi_summary: str = Field(
        default="", description="命局综合总评（400-600字六段结构，已纳入日主天干特征、格局、应用神等维度）"
    )
    liuri_liushi: LiuriLiushiModel | None = Field(None, description="流日/流时（opt-in via include_liuri）")
    missing_fields: list[str] = Field(default_factory=list, description="缺失或未计算的字段名")


class RuleMatchModel(BaseModel):
    """单条规则命中结果，由 bazi_rule_engine 生成，注入 BaziFullResponse。"""

    rule_id: str = Field(..., description="规则唯一标识，如 BRULE_001")
    name: str = Field(..., description="规则名称")
    flags: list[str] = Field(default_factory=list, description="语义标签列表")
    evidence_text: str = Field(..., description="填充占位符后的规则文本，用于 LLM 提示词")
    classic_hint: str = Field(default="", description="来源古籍参考，如 '神峰通考'")
    disclaimer: str = Field(default="仅供学术研究参考", description="免责声明")


from .analysis_temporal import LiuriLiushiModel  # noqa: E402  — temporal schema home


class BaziFullRequest(BaseModel):
    """完整BaZi分析请求"""

    dt: datetime = Field(..., description="Input datetime; aware or naive ISO-8601")
    lon: float = Field(..., description="Longitude in degrees within supported range")
    mode: Literal["dual", "single"] = Field("dual", description="Requested mode")
    solar_time_enabled: bool = Field(False, description="Enable solar-time adjustment when true")
    tz: str = Field("Asia/Shanghai", description="Timezone used only when dt is naive")
    liunian_years: list[int] | None = Field(None, description="Optional liunian year span [-N, N]")
    gender: Literal["male", "female"] | None = Field(None, description="Gender for dayun direction: male/female")
    city_tier: Literal["一线", "新一线", "其余"] | None = Field(
        None, description="City tier for wealth estimate (M3.03)"
    )
    industry: str | None = Field(None, description="Industry name for wealth estimate (M3.03)")
    target_date: datetime | None = Field(None, description="Optional target date for liuri/liushi (B-P2-01)")
    target_hour: int | None = Field(None, ge=0, le=23, description="Target hour 0-23 for liushi")
    include_liuri: bool | None = Field(
        None,
        description="是否返回流日/流时；默认 True。未传 target_date 时使用当天。",
    )
    zi_day_rule: str = Field(
        "sxtwl",
        description="子时换日规则：sxtwl | early_zi_prev_day | early_zi_same_day",
    )
    birth_time_precision: Literal["exact", "hour", "approximate", "unknown"] = Field(
        "exact",
        description="出生时辰精度；unknown/approximate 时标注 hour_pillar advisory",
    )

    @model_validator(mode="after")
    def validate_zi_day_rule(self):
        if self.zi_day_rule not in ("sxtwl", "early_zi_prev_day", "early_zi_same_day"):
            raise ValueError("Invalid zi_day_rule")
        return self

    @model_validator(mode="after")
    def validate_lon(self):  # type: ignore[override]
        if not (MIN_LON <= self.lon <= MAX_LON):
            raise ValueError(f"lon must be between {MIN_LON} and {MAX_LON}")
        return self


class LiuriLiushiRequest(BaseModel):
    """独立流日/流时计算请求。"""

    dt: datetime = Field(..., description="Birth datetime (ISO-8601)")
    lon: float = Field(..., description="Longitude in degrees")
    tz: str = Field("Asia/Shanghai", description="Timezone when dt is naive")
    gender: Literal["male", "female"] | None = Field(None, description="Gender for dayun linkage")
    solar_time_enabled: bool = Field(False, description="Enable solar-time adjustment")
    target_date: datetime | None = Field(None, description="Target date; defaults to today")
    target_hour: int | None = Field(None, ge=0, le=23, description="Target hour 0-23; defaults to birth hour")
    include_dayun_transition: bool = Field(True, description="Include next dayun transition fields")

    @model_validator(mode="after")
    def validate_lon(self):  # type: ignore[override]
        if not (MIN_LON <= self.lon <= MAX_LON):
            raise ValueError(f"lon must be between {MIN_LON} and {MAX_LON}")
        return self


class DayunTransitionModel(BaseModel):
    """距下一大运起运的动态提醒。"""

    days_to_next_transition: int | None = None
    next_transition_age: int | None = None
    next_transition_ganzhi: str | None = None
    next_transition_hint: str | None = None


class LiuriLiushiEndpointResponse(BaseModel):
    """独立流日/流时 API 响应。"""

    request_id: str
    liuri_liushi: LiuriLiushiModel
    dayun_transition: DayunTransitionModel | None = None


class RelationsSummaryModel(BaseModel):
    """地支/天干关系上浮摘要（BE-P3-05）"""

    items: list[RelationItemModel] = Field(default_factory=list)
    clash_summary: str = ""
    combine_summary: str = ""
    harm_summary: str = ""
    interaction_summary: str = ""
    missing: list[str] = Field(default_factory=list)


class ShenshaSummaryModel(BaseModel):
    """神煞上浮摘要（BE-P3-05）"""

    items: list[ShenshaModel] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


class BaziFullResponse(BaseModel):
    """完整的八字分析响应"""

    api_version: str
    rule_version: str
    schema_version: str = "bazi_full@5.1"
    request_id: str
    warnings: list[WarningModel] = Field(default_factory=list)
    methods: BaziMethodsModel
    pillars_primary: PillarsModel
    pillars_secondary: PillarsModel | None = None
    ten_gods: TenGodsModel = Field(default_factory=TenGodsModel)
    shishen_summary: ShishenSummaryModel | None = None
    day_master_strength: DayMasterStrengthModel = Field(default_factory=DayMasterStrengthModel)
    wuxing_score: WuXingScoreModel = Field(default_factory=WuXingScoreModel)
    wuxing_breakdown: WuXingBreakdownModel = Field(default_factory=WuXingBreakdownModel)
    yongshen: YongShenModel = Field(default_factory=YongShenModel)
    dayun: DaYunModel = Field(default_factory=DaYunModel)
    liunian: LiuNianResultModel = Field(default_factory=LiuNianResultModel)
    pillar_details: dict[str, PillarDetailModel] = Field(default_factory=dict)
    raw: BaziRawModel
    validation: ValidationModel | None = None
    risk_flags: RiskFlagsModel | None = None
    # ── M2 新增字段 ──────────────────────────────────────────────────────
    geju: GejuModel | None = None
    palace: PalaceModel | None = None
    shensha: list[ShenshaModel] | None = None
    wealth_analysis: WealthAnalysisModel | None = None
    career: CareerAnalysisModel | None = None
    marriage_analysis: MarriageAnalysisModel | None = None
    health: HealthAnalysisModel | None = None
    relationship: RelationshipAnalysisModel | None = None
    personality: PersonalityModel | None = None
    monthly_fortune: list[MonthlyFortuneModel] | None = None
    jewelry: JewelryModel | None = None
    fengshui: FengshuiModel | None = None
    lucky: LuckyModel | None = None
    lifestyle: LifestyleModel | None = None
    milestones: list[MilestoneModel] | None = None
    liunian_detail: list[LiuNianDetailModel] | None = None
    life_arc: LifeArcModel | None = None
    current_fortune_summary: CurrentFortuneSummaryModel | None = None
    rule_version_detail: dict[str, str] | None = None
    dizhi_relations: list[dict] | None = None
    tiangan_clashes: list[dict] | None = None
    wuxing_balance_score: float | None = None
    wuxing_weak: list[str] | None = None
    wuxing_strong: list[str] | None = None
    balance_advice: str | None = None
    yearly_fortune: list[dict] | None = None
    start_dayun_age: float | None = Field(None, description="大运起运年龄（精确到0.1岁，N5.07）")
    kongwang: list[str] = Field(default_factory=list)
    key_years: list[TimelinePointModel] = Field(default_factory=list)
    key_months: list[TimelinePointModel] = Field(default_factory=list)
    evidence_chain: list[EvidenceItemModel] = Field(default_factory=list)
    confidence_level: Literal["high", "medium", "low"] = "medium"
    confidence_score: int | None = None
    bazi_structural_summary: BaziStructuralSummaryModel | None = None
    bazi_summary: str = Field(
        default="",
        description="命局综合总评（400-600字六段结构，已纳入日主天干特征、格局、应用神等维度）",
    )
    rule_matches: list[RuleMatchModel] = Field(
        default_factory=list,
        description="规则引擎命中结果（bazi_full@5.1，用于 LLM grounding）",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="规则/典籍/证据链稳定 ID（P2-08，供 explain cite grounding）",
    )
    liuri_liushi: LiuriLiushiModel | None = Field(None, description="流日/流时（B-P2-01）")
    missing_fields: list[str] = Field(default_factory=list, description="缺失或未计算的字段名")
    provenance: ResponseProvenance | None = Field(None, description="各层可信度与典籍/启发式分层（9.5 目标计划）")
    classic_refs: list[dict] = Field(
        default_factory=list,
        description="命局级古籍语料软提示（神煞/格局等聚合）",
    )
    relations_summary: RelationsSummaryModel | None = Field(None, description="地支/天干关系摘要（默认上浮，BE-P3-05）")
    shensha_summary: ShenshaSummaryModel | None = Field(None, description="神煞摘要（默认上浮，BE-P3-05）")
    disclaimer_block: DisclaimerBlockModel | None = Field(None, description="合规免责声明块（P0-08）")
    content_versions: dict[str, str] = Field(
        default_factory=dict,
        description="内容资产版本指纹（P0-05 classics/glossary/star_profiles 等）",
    )


VerifyResponse.model_rebuild()
BaziFullResponse.model_rebuild()
