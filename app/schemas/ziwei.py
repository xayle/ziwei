"""
app/schemas/ziwei.py — 紫微斗数 API 请求/响应模型
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


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
    tooltip: str = ""       # 20-40字宫格悉浮摘要


class LunarResponse(BaseModel):
    lunar_year: int
    lunar_month: int
    lunar_day: int
    is_leap_month: bool
    year_gz: str
    month_gz: str
    hour_branch: str


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
