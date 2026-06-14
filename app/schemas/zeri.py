"""app/schemas/zeri.py — §13 择日推荐 Pydantic 模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ZeriRequest(BaseModel):
    """择日推荐请求参数。"""

    year: int = Field(default=2026, ge=1900, le=2100, description="公历年份")
    month: int = Field(..., ge=1, le=12, description="公历月份（1-12）")
    life_palace_branch: str = Field(..., description="命宫地支，如 '子'")
    wuxing_ju_name: str = Field(..., description="五行局名，如 '水二局'")
    natal_year_branch: str = Field(default="", description="本命年支（可选），如 '午'")
    purpose: str = Field(
        default="general",
        description="用途：marriage/business/travel/medical/move/career/general",
    )


class ZeriDayResponse(BaseModel):
    """单日评分结果。"""

    date: str = Field(description="公历日期，如 '2026-04-01'")
    weekday: str = Field(description="星期，如 '一'～'日'")
    day_gz: str = Field(description="日干支，如 '乙巳'")
    day_stem: str = Field(description="日天干")
    day_branch: str = Field(description="日地支")
    lunar_info: str = Field(description="农历简要，如 '三月初五'")
    score: int = Field(description="综合评分 0-100")
    level: str = Field(description="评级：大吉/吉/中/凶")
    level_css: str = Field(description="CSS 类名：daji/ji/zhong/xiong")
    evidence: list[str] = Field(description="得分依据说明列表")
    is_break: bool = Field(description="是否岁破/月破日")
    is_virtue: bool = Field(description="是否天德/月德日")


class ZeriMonthResponse(BaseModel):
    """整月择日结果。"""

    year: int
    month: int
    purpose: str
    purpose_label: str = Field(description="用途中文名称")
    year_gz: str = Field(description="年干支，如 '丙午'")
    month_gz: str = Field(description="月干支，如 '甲子'")
    days: list[ZeriDayResponse] = Field(description="当月逐日评分")
    top_days: list[str] = Field(description="推荐日期列表（按评分排序，最多8个）")
