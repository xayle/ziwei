"""
app/schemas/ziwei.py — 紫微斗数 API 请求/响应模型
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .disclaimer import DisclaimerBlockModel
from .provenance import ResponseProvenance
from .relation_compat import RelationTypeEnum


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


class PalaceWeightModel(BaseModel):
    palace_name: str
    weight: float
    reason: str | None = None


class BorrowedStarSourceModel(BaseModel):
    palace_name: str
    palace_index: int | None = None
    branch: str | None = None
    stem: str | None = None
    full_gz: str | None = None
    main_stars: list[dict[str, object]] = Field(default_factory=list)
    analysis_tags: list[str] = Field(default_factory=list)
    conclusion: str | None = None
    explanation: str | None = None
    suggestion: str | None = None


class SihuaTraceItemModel(BaseModel):
    phase: Literal["生年", "大限", "流年", "流月"]
    target: str
    transform: str
    palace_name: str | None = None
    summary: str | None = None
    source: str | None = None
    missing: bool = False


class StarBrightnessSummaryModel(BaseModel):
    strong: list[str] = Field(default_factory=list)
    weak: list[str] = Field(default_factory=list)
    details: dict[str, str] = Field(default_factory=dict)


class ChartRelationSummaryModel(BaseModel):
    minggong: str | None = None
    shengong: str | None = None
    wuxing_ju: str | None = None
    triad_tetrad: list[str] = Field(default_factory=list)
    opposition: list[str] = Field(default_factory=list)
    palace_weights: list[PalaceWeightModel] = Field(default_factory=list)
    key_palaces: list[str] = Field(default_factory=list)
    palace_influence_notes: list[str] = Field(default_factory=list)
    source: str | None = None
    missing: list[str] = Field(default_factory=list)
    borrowed_palaces: list[dict[str, object]] = Field(default_factory=list)
    borrowed_sources: list[BorrowedStarSourceModel] = Field(default_factory=list)


class ConfidenceSummaryModel(BaseModel):
    level: Literal["high", "medium", "low"] = "medium"
    score: int | None = None
    evidence: list[EvidenceItemModel] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    inference_notes: list[str] = Field(default_factory=list)
    blocked_fields: list[str] = Field(default_factory=list)


class PalaceRefModel(BaseModel):
    """宫位结构化引用（命/身/三方四正）。"""

    index: int
    name: str
    branch: str
    branch_idx: int
    stem: str = ""
    ganzhi: str = ""
    is_empty_palace: bool = False
    is_body_palace: bool = False


class SanfangStructureModel(BaseModel):
    """三方四正结构化关系。"""

    life_palace: PalaceRefModel
    opposite_palace: PalaceRefModel | None = None
    triad_palaces: list[PalaceRefModel] = Field(default_factory=list)


class ZiweiChartStructuralSummaryModel(BaseModel):
    """命盘宫位结构摘要（纯结构化，替代 loose dict）。"""

    life_palace: PalaceRefModel
    body_palace: PalaceRefModel
    opposite_palace: PalaceRefModel | None = None
    sanfang: SanfangStructureModel
    life_branch_idx: int = 0
    body_branch_idx: int = 0
    source: str | None = None
    missing: list[str] = Field(default_factory=list)


class ZiweiCoreSnapshotModel(BaseModel):
    """核心命盘快照。"""

    life_palace_gz: str = ""
    body_palace_gz: str = ""
    life_palace_branch_idx: int = 0
    body_palace_branch_idx: int = 0
    wuxing_ju: int = 0
    wuxing_ju_name: str = ""
    life_ruler_star: str = ""
    body_ruler_star: str = ""
    laiyin_palace: str = ""


class PatternSummaryBlockModel(BaseModel):
    patterns: list[dict[str, object]] = Field(default_factory=list)
    special_pattern_names: list[str] = Field(default_factory=list)
    summary_text: str = ""
    confidence: Literal["high", "medium", "low"] = "medium"


class ReportSummaryBlockModel(BaseModel):
    title: str = ""
    summary: str = ""
    highlights: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    annotation_prompt: str = ""
    source: str | None = None
    missing: list[str] = Field(default_factory=list)


class SihuaTraceEntryModel(BaseModel):
    """生年四化链条目（宫位级）。"""

    palace: str
    stem: str = ""
    flying_out: dict[str, str] = Field(default_factory=dict)
    conclusion: str = ""
    opposition: str = ""
    source: str = ""
    missing: bool = False


class KeyYearPointModel(BaseModel):
    label: str
    ganzhi: str = ""
    palace: str = ""
    score: int | None = None
    overall: str = ""
    events: list[str] = Field(default_factory=list)


class KeyMonthPointModel(BaseModel):
    month: int
    month_name: str = ""
    month_gz: str = ""
    palace_name: str = ""
    sihua: dict[str, str] = Field(default_factory=dict)


class ZiweiStructuralSummaryModel(BaseModel):
    core_snapshot: ZiweiCoreSnapshotModel = Field(default_factory=ZiweiCoreSnapshotModel)
    chart_relation_summary: ChartRelationSummaryModel | None = None
    sihua_summary: list[SihuaTraceItemModel] = Field(default_factory=list)
    brightness_summary: StarBrightnessSummaryModel | None = None
    timeline_summary: dict[str, list[TimelinePointModel]] = Field(default_factory=dict)
    pattern_summary: PatternSummaryBlockModel = Field(default_factory=PatternSummaryBlockModel)
    confidence_summary: ConfidenceSummaryModel | None = None
    report_summary: ReportSummaryBlockModel = Field(default_factory=ReportSummaryBlockModel)
    source: str | None = None
    missing: list[str] = Field(default_factory=list)


class ZiweiRequest(BaseModel):
    """紫微命盘请求。"""

    year: int = Field(..., ge=1900, le=2100, description="公历出生年")
    month: int = Field(..., ge=1, le=12, description="公历出生月")
    day: int = Field(..., ge=1, le=31, description="公历出生日")
    hour: int = Field(..., ge=0, le=23, description="出生小时（24小时制）")
    minute: int = Field(0, ge=0, le=59, description="出生分钟")
    gender: str = Field(..., description="性别：男/女")
    liunian_year: int | None = Field(None, description="流年年份（不填默认当年）")
    longitude: float | None = Field(None, ge=-180, le=180, description="出生地经度（东经正数），用于真太阳时修正")
    template_version: str = Field("standard", description="响应模板版本：standard, pro, simple")

    # ── 算法设置 ─────────────────────────────────────────────────────────────
    late_zishi: bool = Field(True, description="晚子时(23:00~00:00)视为次日（默认True）")
    year_divide: str = Field(
        "lichun",
        description="年干支界：'lichun'=立春换年（默认，对齐八字节气年）| 'normal'=正月初一换年（对齐 iztro yearDivide=normal）",
    )
    day_divide: str = Field(
        "solar_next",
        description=(
            "晚子时换日：'solar_next'=公历进次日再排盘（默认）| "
            "'forward'=公历不换日、安星农历日+1（对齐 iztro dayDivide=forward）| "
            "'current'=不换日"
        ),
    )
    sihua_stem_indices: dict[str, int] | None = Field(
        None,
        description=(
            "四化表per-stem方案选择，键=天干，值=方案索引(0=标准)。"
            '如 {"庚": 2} 选庚的阳武府同方案。'
            "可选天干: 甲(0/1) 戊(0/1) 庚(0-4) 辛(0/1) 壬(0-2) 癸(0/1)"
        ),
    )
    leap_month_method: str = Field(
        "mid",
        description="闰月处理方式：'mid'=月中分界(默认) | 'next'=视为下月 | 'same'=视为本月",
    )
    kuiyue_method: str = Field(
        "standard",
        description="天魁天钺安法：'standard'(六辛逢虎马) | 'gengxin_mahu' | 'gengxin_huima' | 'liuxin_mahu'",
    )
    # ── A1-A8 新增安星方法 ────────────────────────────────────
    tianma_method: str = Field(
        "year",
        description="天马安法：'year'=依据年支（默认） | 'month'=依据月支",
    )
    tiankong_method: str = Field(
        "standard",
        description="天空安法：'standard'=常规排法（戌起年支顺）| 'shun'=顺加生时",
    )
    brightness_method: str = Field(
        "standard",
        description="星曜亮度：'standard'=斗数全书（默认）| 'zhongzhou'=中州派 | 'mod1'=现代修订一 | 'mod2'=现代修订二",
    )
    jiukong_method: str = Field(
        "dual",
        description="截空旬空安法：'dual'=正副双星法（默认）| 'single'=常规单星法 | 'zhanyan'=占验派排法",
    )
    tianshang_method: str = Field(
        "standard",
        description="天使天伤安法：'standard'=常规（默认）| 'zhongzhou'=中州派",
    )
    mingzhu_method: str = Field(
        "quanshu",
        description="命主安法：'quanshu'=依据斗数全书（默认）| 'zhongzhou'=依据中州派理论",
    )
    liunian_sihua_method: str = Field(
        "year_stem",
        description="流年四化来源：'year_stem'=依据流年天干（默认，《全书》口径）| 'life_palace_stem'=依据流年命宫天干（陆斌兆体系）",
    )
    changsheng_method: str = Field(
        "standard",
        description="长生十二神安法：'standard'=区分阴阳顺逆（默认）| 'water_earth'=水土共长生 | 'fire_earth'=火土共长生",
    )
    wenchang_method: str = Field(
        "hour",
        description="文昌文曲安法：'hour'=依生时（默认）| 'year_branch'=依年支（legacy）",
    )
    youbi_method: str = Field(
        "month",
        description="右弼安法：'month'=依生月（默认）| 'hour'=依生时（legacy）",
    )
    liunian_life_method: str = Field(
        "taisui",
        description="流年命宫：'taisui'=太岁起宫（默认）| 'yin_start'=寅宫起（legacy）",
    )
    liuyue_method: str = Field(
        "doujun",
        description="流月排法：'doujun'=斗君法（默认）| 'simplified'=简化法（legacy）",
    )
    xiaoxian_start_method: str = Field(
        "standard",
        description="小限起点：'standard'=标准（默认）| 'gender_split'=男女分宫（legacy）",
    )
    flow_lunar_day: int | None = Field(
        None,
        ge=1,
        le=30,
        description="流日农历日（1-30），需配合 flow_liuyue_month",
    )
    flow_liuyue_month: int | None = Field(
        None,
        ge=1,
        le=12,
        description="流月序号（1-12），配合 flow_lunar_day 计算流日/流时",
    )
    flow_hour_branch: int | None = Field(
        None,
        ge=0,
        le=11,
        description="流时时辰地支索引（子=0…亥=11），缺省取生时",
    )
    include_flow_liuri: bool | None = Field(
        None,
        description="standard/pro 默认 True：未传 flow_* 时按流年参考日自动计算流日/流时",
    )

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, v: object) -> object:
        if v is None:
            return v
        return str(v).strip()

    @model_validator(mode="after")
    def validate_fields(self):
        try:
            date(self.year, self.month, self.day)
        except ValueError:
            raise ValueError("Invalid date")
        if self.gender not in ["男", "女"]:
            raise ValueError("Invalid gender, must be 男 or 女")
        if self.template_version not in ["standard", "pro", "simple"]:
            raise ValueError("Invalid template_version")
        if self.leap_month_method not in ["mid", "next", "same"]:
            raise ValueError("Invalid leap_month_method, must be mid/next/same")
        if self.year_divide not in ["lichun", "normal"]:
            raise ValueError("Invalid year_divide, must be lichun/normal")
        if self.day_divide not in ["solar_next", "forward", "current"]:
            raise ValueError("Invalid day_divide, must be solar_next/forward/current")
        valid_kuiyue = {"standard", "gengxin_mahu", "gengxin_huima", "liuxin_mahu"}
        if self.kuiyue_method not in valid_kuiyue:
            raise ValueError(f"Invalid kuiyue_method, must be one of {valid_kuiyue}")
        if self.tianma_method not in {"year", "month"}:
            raise ValueError("Invalid tianma_method, must be year/month")
        if self.tiankong_method not in {"standard", "shun"}:
            raise ValueError("Invalid tiankong_method, must be standard/shun")
        if self.brightness_method not in {"standard", "zhongzhou", "mod1", "mod2"}:
            raise ValueError("Invalid brightness_method")
        if self.jiukong_method not in {"dual", "single", "zhanyan"}:
            raise ValueError("Invalid jiukong_method, must be dual/single/zhanyan")
        if self.tianshang_method not in {"standard", "zhongzhou"}:
            raise ValueError("Invalid tianshang_method, must be standard/zhongzhou")
        if self.mingzhu_method not in {"quanshu", "zhongzhou"}:
            raise ValueError("Invalid mingzhu_method, must be quanshu/zhongzhou")
        if self.liunian_sihua_method not in {"year_stem", "life_palace_stem"}:
            raise ValueError("Invalid liunian_sihua_method")
        if self.changsheng_method not in {"standard", "water_earth", "fire_earth"}:
            raise ValueError("Invalid changsheng_method")
        if self.wenchang_method not in {"hour", "year_branch"}:
            raise ValueError("Invalid wenchang_method, must be hour/year_branch")
        if self.youbi_method not in {"month", "hour"}:
            raise ValueError("Invalid youbi_method, must be month/hour")
        if self.liunian_life_method not in {"taisui", "yin_start"}:
            raise ValueError("Invalid liunian_life_method, must be taisui/yin_start")
        if self.liuyue_method not in {"doujun", "simplified"}:
            raise ValueError("Invalid liuyue_method, must be doujun/simplified")
        if self.xiaoxian_start_method not in {"standard", "gender_split"}:
            raise ValueError("Invalid xiaoxian_start_method, must be standard/gender_split")
        if self.flow_lunar_day is not None and self.flow_liuyue_month is None:
            raise ValueError("flow_liuyue_month is required when flow_lunar_day is set")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "year": 2002,
                "month": 3,
                "day": 13,
                "hour": 14,
                "minute": 55,
                "gender": "女",
            }
        }
    }


# ── 子结构 ──────────────────────────────────────────────────────
class StarInfo(BaseModel):
    name: str
    brightness: str
    brightness_val: int
    transforms: list[str] = []


class PalaceStructuredAnalysis(BaseModel):
    """宫位三段式结构化解读（与 prose analysis 字典互补）。"""

    palace_index: int
    palace_name: str
    conclusion: str = ""
    explanation: str = ""
    suggestion: str = ""
    tooltip: str = ""
    analysis_tags: list[str] = Field(default_factory=list)
    is_empty_palace: bool = False


class PalaceResponse(BaseModel):
    index: int
    name: str
    branch: str
    stem: str
    main_stars: list[StarInfo]
    aux_stars: list[StarInfo]
    flying_out: dict[str, str] = {}
    borrowed_main_stars: list[dict[str, object]] = Field(default_factory=list)
    borrowed_from_palace: str | None = None
    borrowed_reason: str | None = None
    is_empty_palace: bool = False
    analysis: str = ""
    analysis_tags: list[str] = []
    xiaoxian_ages: list[int] = []  # 该宫小限对应年龄
    opposition_name: str = ""  # 对宫名称
    # 三段式结构化解读
    conclusion: str = ""  # 一句话结论
    explanation: str = ""  # 2-3行详细解释（\n分隔）
    suggestion: str = ""  # 1行可操作建议
    tooltip: str = (
        ""  # 20-40字宫格悉浮摘要    dayun_boshi: list[str] = []   # 当前大运博士十二流曜（落在该宫的星名列表）
    )
    changsheng: str = ""  # 长生十二神（本命盘固定星）
    jiangqian_star: str = ""  # 将前十二神（流年星）
    suiqian_star: str = ""  # 岁前十二神（流年星）


class LunarResponse(BaseModel):
    lunar_year: int
    lunar_month: int
    lunar_day: int
    is_leap_month: bool
    year_gz: str
    month_gz: str  # 农历月柱
    hour_branch: str
    jieqi_month_gz: str = ""  # 节气月柱（八字法）
    day_gz: str = ""  # 日柱干支
    hour_gz: str = ""  # 时柱干支
    year_divide: str = "lichun"  # 年界口径
    day_divide: str = "solar_next"  # 晚子换日口径


class DayunItemResponse(BaseModel):
    index: int
    ganzhi: str
    branch_idx: int = Field(0, description="大限宫位地支索引（子=0）")
    start_age: int
    end_age: int
    start_year: int
    sihua: dict[str, str] = {}  # 大运四化 {星名: "化禄"/"化权"/"化科"/"化忧"}
    boshi_stars: dict[str, str] = {}  # 博士十二流曜 {星名: 地支}


class DayunResponse(BaseModel):
    forward: bool
    start_age: int
    start_age_exact: float
    start_age_text: str = ""  # 起运年龄文字 "X年X月X天"
    items: list[DayunItemResponse]


class LiunianResponse(BaseModel):
    year: int
    year_gz: str
    life_palace_branch: int
    sihua: dict[str, str]


class LiuyueItem(BaseModel):
    month: int
    month_name: str
    month_gz: str
    life_palace_branch: int
    palace_name: str
    sihua: dict[str, str] = {}  # 流月四化（月干四化）


class IztroDualTrackResponse(BaseModel):
    """iztro 对照轨（典型：ZW03 立春前晚子时边界）。"""

    label: str = "iztro 对照轨"
    year_divide: str = "normal"
    day_divide: str = "forward"
    life_palace_gz: str | None = None
    main_match: int = 0
    main_total: int = 14
    note: str | None = None


class IztroCrosscheckResponse(BaseModel):
    """与 iztro 库的 advisory 交叉核验（可选，不阻断排盘）。"""

    status: str
    main_match: int = 0
    main_total: int = 14
    life_palace_match: bool = True
    iztro_life_palace_gz: str | None = None
    engine_life_palace_gz: str | None = None
    advisory: str | None = None
    dual_track: IztroDualTrackResponse | None = None


class LiuriItem(BaseModel):
    lunar_day: int
    life_palace_branch: int
    branch: str
    palace_name: str = ""
    liuyue_month: int = 1


class LiushiItem(BaseModel):
    hour_branch_idx: int
    life_palace_branch: int
    branch: str
    palace_name: str = ""
    hour_label: str = ""


class LiuriLiushiResponse(BaseModel):
    liuri: LiuriItem
    liushi: LiushiItem
    missing_fields: list[str] = Field(default_factory=list)


class FlyingPalaceResponse(BaseModel):
    palace_name: str
    stem_name: str
    flying_out: dict[str, str]
    opposition_palace: str = ""  # 对冲宫位名
    self_transforms: list[str] = []  # 自化描述列表


class FlyingChartResponse(BaseModel):
    palaces: list[FlyingPalaceResponse]
    received: dict[str, list[str]]
    chonged: dict[str, list[str]] = {}  # 被对冲汇总
    self_transforms: list[str] = []  # 全局自化列表


class ZiweiResponse(BaseModel):
    """完整紫微命盘响应。"""

    birth_solar: str
    gender: str

    # 农历信息
    lunar: LunarResponse

    # 命盘格局
    life_palace_gz: str
    body_palace_gz: str
    life_palace_branch_idx: int = 0  # 命宫地支索引（子=0…亥=11）
    body_palace_branch_idx: int = 0  # 身宫地支索引
    body_palace_branch_name: str = ""  # 身宫地支汉字
    wuxing_ju: int
    wuxing_ju_name: str

    # 12宫
    palaces: list[PalaceResponse]

    # 大运
    dayun: DayunResponse

    # 流年
    liunian: LiunianResponse | None = None

    # 飞星
    flying: FlyingChartResponse | None = None

    # 流月
    liuyue: list[LiuyueItem] = []

    # 流日/流时（Z-P2-01，可选）
    liuri_liushi: LiuriLiushiResponse | None = None

    # 引擎缺失字段
    missing_fields: list[str] = Field(default_factory=list)
    engine_warnings: list[str] = Field(default_factory=list)
    iztro_crosscheck: IztroCrosscheckResponse | None = None

    # 文字
    summary: str = ""
    chart_summary: str = ""
    structural_summary: ZiweiChartStructuralSummaryModel | None = None
    sihua_trace: list[SihuaTraceEntryModel] = Field(default_factory=list)
    key_years: list[KeyYearPointModel] = Field(default_factory=list)
    key_months: list[KeyMonthPointModel] = Field(default_factory=list)
    confidence_level: Literal["high", "medium", "low"] = "medium"
    confidence_score: int | None = None
    evidence_chain: list[EvidenceItemModel] = Field(default_factory=list)
    ziwei_structural_summary: ZiweiStructuralSummaryModel | None = None
    analysis: dict[str, str] = {}
    analysis_structured: list[PalaceStructuredAnalysis] = Field(
        default_factory=list,
        description="逐宫结构化解读（conclusion/explanation/suggestion/tooltip）",
    )

    # 命主/身主
    life_ruler_star: str = ""  # 命主
    body_ruler_star: str = ""  # 身主

    # 来因宫
    laiyin_palace: str = ""  # 来因宫名称（生年天干所在宫位）

    # 真太阳时
    true_solar_time: str = ""  # ""表示未传经度，"HH:MM"表示已修正

    # 运势预测
    forecast: ForecastResultResponse | None = None

    template_version: str = "1.0"
    algorithm_version: str = "2.1.0"
    engine_version: str = "3.0"
    patterns: list[PatternResponse] = []
    remedies: list[RemedyResponse] = []
    life_suggestions: list[LifeSuggestionResponse] = []
    provenance: ResponseProvenance | None = Field(None, description="各层可信度与典籍/启发式分层（9.5 目标计划）")
    trust_level: Literal["full", "degraded", "reference", "advisory", "verified"] = Field(
        "full",
        description="命盘信任级别；degraded 时运限/API 仍 200（Q10）",
    )
    disclaimer_block: DisclaimerBlockModel | None = Field(None, description="合规免责声明块（P0-08）")
    content_versions: dict[str, str] = Field(
        default_factory=dict,
        description="内容资产版本指纹（P0-05 classics/glossary/star_profiles 等）",
    )
    wenmo_advisory: str | None = Field(
        None,
        description="文墨天机 advisory 对照说明（P1-13 / colophon）",
    )
    classic_refs: list[dict] = Field(
        default_factory=list,
        description="古籍语料软提示（主星/格局/宫位，非硬覆盖引擎结论）",
    )


# ── 运势预测 Schema ────────────────────────────────────────────────────────


class EventTagResponse(BaseModel):
    """单个事件/警示标签。"""

    category: str  # 桃花/姻缘、灾祸/健康、财运、事业/官运、变动/迁移、贵人/助力
    level: str  # 强 / 中 / 弱
    description: str
    source: str  # 触发依据


class PeriodForecastResponse(BaseModel):
    """一段时期（年/月）的运势摘要。"""

    period: str  # 如 "2026年" / "2026年正月(寅)"
    ganzhi: str  # 干支
    palace_name: str  # 流年/月命宫对应本命宫位名
    overall: str  # 综合一句话
    details: dict[str, str]  # {感情/财运/事业/健康: 详细文字}
    events: list[EventTagResponse]
    advice: str
    score: int  # 综合运势 1-100
    tier: str = "neutral"
    layer: str = Field("heuristic", description="provenance layer: classical | engine | heuristic")


class ForecastResultResponse(BaseModel):
    """完整运势预测结果。"""

    year: int
    yearly: PeriodForecastResponse  # 年运
    monthly: list[PeriodForecastResponse]  # 12个流月
    current_month: PeriodForecastResponse  # 当前月
    layer: str = Field("heuristic", description="forecast 整体可信度分层")


class PatternResponse(BaseModel):
    name: str = ""
    level: str = ""
    description: str = ""
    palaces: list[str] = []
    stars: list[str] = []
    source: str = ""
    rule_id: str = Field("", description="格局规则 ID，如 ZRULE_001（B-P2 证据链）")
    tier: Literal["canonical", "extended", "heuristic"] = Field(
        "heuristic",
        description="格局可信度层级：canonical 典籍核心 / extended 双条件 / heuristic 启发式",
    )
    classic_ref: str = Field("", description="格局典籍句式（soft narrative）")
    classic_refs: list[dict] = Field(default_factory=list, description="格局相关古籍语料软提示")


class RemedyResponse(BaseModel):
    id: str = ""
    name: str = ""
    priority: int = 0
    cost_level: str = ""
    valid_scope: str = ""
    actions: list[str] = []
    evidence: str = ""
    disclaimer: str = ""


class LifeSuggestionResponse(BaseModel):
    id: str = ""
    category: str = ""
    category_label: str = ""
    name: str = ""
    priority: int = 0
    cost_level: str = ""
    valid_scope: str = ""
    short_desc: str = ""
    actions: list[str] = []


class CompatibilityRequest(BaseModel):
    caller: str = ""
    timestamp: str = ""
    person_a: ZiweiRequest
    person_b: ZiweiRequest


class CompatibilityDimensionResponse(BaseModel):
    dimension: str = Field(alias="name", default="")
    score: int = 0
    max_score: int = 0
    description: str = Field(alias="desc", default="")


class CompatibilityResponse(BaseModel):
    overall_score: int = Field(alias="total_score", default=0)
    max_score: int = 0
    level: str = ""
    summary: str = ""
    dimensions: list[CompatibilityDimensionResponse] = []
    person_a_info: dict = {}
    person_b_info: dict = {}
    harmony_points: list[str] = []
    conflict_points: list[str] = []
    complement_points: list[str] = []
    palace_compare: list[dict] = []


class MultiCompatRequest(BaseModel):
    person_list: list[ZiweiRequest]
    relation_type: RelationTypeEnum = Field(
        "friend",
        description="BE-R14: relation/full 分维对齐时使用的关系类型",
    )
    labels: list[str] | None = Field(None, description="成员显示名，长度与 person_list 一致时可覆盖默认")
    include_relation_dims: bool = Field(
        False,
        description="true 时 pairs 附加 combined_score / bazi_score / ziwei_score（multi-compat@1.1）",
    )
    supervisor_id: Literal["a", "b"] | None = Field(
        None,
        description="relation_type=supervisor_subordinate 时必填",
    )

    @field_validator("person_list")
    @classmethod
    def _check_length(cls, v: list) -> list:
        if len(v) < 2:
            raise ValueError("至少需要 2 人")
        if len(v) > 4:
            raise ValueError("最多支持 4 人")
        return v

    @model_validator(mode="after")
    def _validate_labels_and_supervisor(self):
        if self.labels is not None and len(self.labels) != len(self.person_list):
            raise ValueError("labels 长度须与 person_list 一致")
        if self.relation_type == "supervisor_subordinate" and self.include_relation_dims:
            if not self.supervisor_id:
                raise ValueError("supervisor_subordinate 需 supervisor_id ('a' 或 'b')")
        return self


class MultiCompatPairResponse(BaseModel):
    person_a_idx: int = 0
    person_b_idx: int = 1
    total_score: int = 0
    max_score: int = 100
    level: str = ""
    combined_score: float | None = None
    bazi_score: float | None = None
    ziwei_score: float | None = None
    grade: str | None = None
    dimension_highlights: list[str] = Field(default_factory=list)


class MultiCompatResponse(BaseModel):
    schema_version: Literal["multi-compat@1.0", "multi-compat@1.1"] = "multi-compat@1.0"
    person_count: int = 0
    relation_type: RelationTypeEnum | None = None
    pairs: list[MultiCompatPairResponse] = []
    matrix: list[list[int]] = []
    team_harmony_score: int = 0
