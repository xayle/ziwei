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


class FlyingPalaceResponse(BaseModel):
    palace_name: str
    stem_name: str
    flying_out: dict[str, str]


class FlyingChartResponse(BaseModel):
    palaces: list[FlyingPalaceResponse]
    received: dict[str, list[str]]


class ZiweiResponse(BaseModel):
    """完整紫微命盘响应。"""
    birth_solar: str
    gender: str

    # 农历信息
    lunar: LunarResponse

    # 命盘格局
    life_palace_gz: str
    body_palace_gz: str
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
