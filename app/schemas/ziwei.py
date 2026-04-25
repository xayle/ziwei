"""
app/schemas/ziwei.py — 紫微斗数 API 请求/响应模型
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, model_validator, field_validator
from datetime import date

class ZiweiRequest(BaseModel):
    """紫微命盘请求。"""
    year: int = Field(..., ge=1900, le=2100, description="公历出生年")
    month: int = Field(..., ge=1, le=12, description="公历出生月")
    day: int = Field(..., ge=1, le=31, description="公历出生日")
    hour: int = Field(..., ge=0, le=23, description="出生小时（24小时制）")
    minute: int = Field(0, ge=0, le=59, description="出生分钟")
    gender: str = Field(..., description="性别：男/女")
    liunian_year: Optional[int] = Field(None, description="流年年份（不填默认当年）")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="出生地经度（东经正数），用于真太阳时修正")
    template_version: str = Field("standard", description="响应模板版本：standard, pro, simple")

    # ── 算法设置 ─────────────────────────────────────────────────────────────
    late_zishi: bool = Field(True, description="晚子时(23:00~00:00)视为次日（默认True）")
    sihua_stem_indices: Optional[dict[str, int]] = Field(
        None,
        description=(
            "四化表per-stem方案选择，键=天干，值=方案索引(0=标准)。"
            "如 {\"庚\": 2} 选庚的阳武府同方案。"
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
        description="流年四化来源：'year_stem'=依据流年天干（默认）| 'life_palace_stem'=依据流年命宫天干",
    )
    changsheng_method: str = Field(
        "standard",
        description="长生十二神安法：'standard'=区分阴阳顺逆（默认）| 'water_earth'=水土共长生 | 'fire_earth'=火土共长生",
    )

    @model_validator(mode='after')
    def validate_fields(self):
        try:
            date(self.year, self.month, self.day)
        except ValueError:
            raise ValueError('Invalid date')
        if self.gender not in ['男', '女']:
            raise ValueError('Invalid gender, must be 男 or 女')
        if self.template_version not in ['standard', 'pro', 'simple']:
            raise ValueError('Invalid template_version')
        if self.leap_month_method not in ['mid', 'next', 'same']:
            raise ValueError('Invalid leap_month_method, must be mid/next/same')
        valid_kuiyue = {'standard', 'gengxin_mahu', 'gengxin_huima', 'liuxin_mahu'}
        if self.kuiyue_method not in valid_kuiyue:
            raise ValueError(f'Invalid kuiyue_method, must be one of {valid_kuiyue}')
        if self.tianma_method not in {'year', 'month'}:
            raise ValueError('Invalid tianma_method, must be year/month')
        if self.tiankong_method not in {'standard', 'shun'}:
            raise ValueError('Invalid tiankong_method, must be standard/shun')
        if self.brightness_method not in {'standard', 'zhongzhou', 'mod1', 'mod2'}:
            raise ValueError('Invalid brightness_method')
        if self.jiukong_method not in {'dual', 'single', 'zhanyan'}:
            raise ValueError('Invalid jiukong_method, must be dual/single/zhanyan')
        if self.tianshang_method not in {'standard', 'zhongzhou'}:
            raise ValueError('Invalid tianshang_method, must be standard/zhongzhou')
        if self.mingzhu_method not in {'quanshu', 'zhongzhou'}:
            raise ValueError('Invalid mingzhu_method, must be quanshu/zhongzhou')
        if self.liunian_sihua_method not in {'year_stem', 'life_palace_stem'}:
            raise ValueError('Invalid liunian_sihua_method')
        if self.changsheng_method not in {'standard', 'water_earth', 'fire_earth'}:
            raise ValueError('Invalid changsheng_method')
        return self

    model_config = {"json_schema_extra": {"example": {
        "year": 2002, "month": 3, "day": 13,
        "hour": 14, "minute": 55,
        "gender": "女",
    }}}


# ── 子结构 ──────────────────────────────────────────────────────
class StarInfo(BaseModel):
    name: str
    brightness: str
    brightness_val: int
    transforms: list[str] = []


class PalaceResponse(BaseModel):
    index: int
    name: str
    branch: str
    stem: str
    main_stars: list[StarInfo]
    aux_stars: list[str]
    flying_out: dict[str, str] = {}
    analysis: str = ""
    analysis_tags: list[str] = []
    xiaoxian_ages: list[int] = []  # 该宫小限对应年龄
    opposition_name: str = ""      # 对宫名称
    # 三段式结构化解读
    conclusion: str = ""    # 一句话结论
    explanation: str = ""   # 2-3行详细解释（\n分隔）
    suggestion: str = ""    # 1行可操作建议
    tooltip: str = ""       # 20-40字宫格悉浮摘要    dayun_boshi: list[str] = []   # 当前大运博士十二流曜（落在该宫的星名列表）
    changsheng: str = ""          # 长生十二神（本命盘固定星）
    jiangqian_star: str = ""      # 将前十二神（流年星）
    suiqian_star: str = ""        # 岁前十二神（流年星）

class LunarResponse(BaseModel):
    lunar_year: int
    lunar_month: int
    lunar_day: int
    is_leap_month: bool
    year_gz: str
    month_gz: str         # 农历月柱
    hour_branch: str
    jieqi_month_gz: str = ""  # 节气月柱（八字法）
    day_gz: str = ""          # 日柱干支
    hour_gz: str = ""         # 时柱干支


class DayunItemResponse(BaseModel):
    index: int
    ganzhi: str
    start_age: int
    end_age: int
    start_year: int
    sihua: dict[str, str] = {}       # 大运四化 {星名: "化禄"/"化权"/"化科"/"化忧"}
    boshi_stars: dict[str, str] = {} # 博士十二流曜 {星名: 地支}


class DayunResponse(BaseModel):
    forward: bool
    start_age: int
    start_age_exact: float
    start_age_text: str = ""   # 起运年龄文字 "X年X月X天"
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


class FlyingPalaceResponse(BaseModel):
    palace_name: str
    stem_name: str
    flying_out: dict[str, str]
    opposition_palace: str = ""       # 对冲宫位名
    self_transforms: list[str] = []  # 自化描述列表


class FlyingChartResponse(BaseModel):
    palaces: list[FlyingPalaceResponse]
    received: dict[str, list[str]]
    chonged: dict[str, list[str]] = {}          # 被对冲汇总
    self_transforms: list[str] = []             # 全局自化列表


class ZiweiResponse(BaseModel):
    """完整紫微命盘响应。"""
    birth_solar: str
    gender: str

    # 农历信息
    lunar: LunarResponse

    # 命盘格局
    life_palace_gz: str
    body_palace_gz: str
    life_palace_branch_idx: int = 0   # 命宫地支索引（子=0…亥=11）
    body_palace_branch_idx: int = 0   # 身宫地支索引
    body_palace_branch_name: str = ""   # 身宫地支汉字
    wuxing_ju: int
    wuxing_ju_name: str

    # 12宫
    palaces: list[PalaceResponse]

    # 大运
    dayun: DayunResponse

    # 流年
    liunian: Optional[LiunianResponse] = None

    # 飞星
    flying: Optional[FlyingChartResponse] = None

    # 流月
    liuyue: list[LiuyueItem] = []

    # 文字
    summary: str = ""
    analysis: dict[str, str] = {}

    # 命主/身主
    life_ruler_star: str = ""   # 命主
    body_ruler_star: str = ""   # 身主

    # 真太阳时
    true_solar_time: str = ""   # ""表示未传经度，"HH:MM"表示已修正

    # 运势预测
    forecast: Optional["ForecastResultResponse"] = None

    template_version: str = "1.0"
    algorithm_version: str = "2.1.0"
    engine_version: str = "3.0"
    patterns: list["PatternResponse"] = []
    remedies: list["RemedyResponse"] = []
    life_suggestions: list["LifeSuggestionResponse"] = []


# ── 运势预测 Schema ────────────────────────────────────────────────────────

class EventTagResponse(BaseModel):
    """单个事件/警示标签。"""
    category: str    # 桃花/姻缘、灾祸/健康、财运、事业/官运、变动/迁移、贵人/助力
    level: str       # 强 / 中 / 弱
    description: str
    source: str      # 触发依据


class PeriodForecastResponse(BaseModel):
    """一段时期（年/月）的运势摘要。"""
    period: str              # 如 "2026年" / "2026年正月(寅)"
    ganzhi: str              # 干支
    palace_name: str         # 流年/月命宫对应本命宫位名
    overall: str             # 综合一句话
    details: dict[str, str]  # {感情/财运/事业/健康: 详细文字}
    events: list[EventTagResponse]
    advice: str
    score: int               # 综合运势 1-100


class ForecastResultResponse(BaseModel):
    """完整运势预测结果。"""
    year: int
    yearly: PeriodForecastResponse           # 年运
    monthly: list[PeriodForecastResponse]    # 12个流月
    current_month: PeriodForecastResponse    # 当前月


class PatternResponse(BaseModel):
    name: str = ""
    level: str = ""
    description: str = ""
    palaces: list[str] = []
    stars: list[str] = []
    source: str = ""

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
    person_list: list["ZiweiRequest"]

    @field_validator("person_list")
    @classmethod
    def _check_length(cls, v: list) -> list:
        if len(v) < 2:
            raise ValueError("至少需要 2 人")
        if len(v) > 4:
            raise ValueError("最多支持 4 人")
        return v


class MultiCompatPairResponse(BaseModel):
    person_a_idx: int = 0
    person_b_idx: int = 1
    total_score: int = 0
    max_score: int = 100
    level: str = ""


class MultiCompatResponse(BaseModel):
    person_count: int = 0
    pairs: list[MultiCompatPairResponse] = []
    matrix: list[list[int]] = []
    team_harmony_score: int = 0
