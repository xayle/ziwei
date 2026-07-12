"""浮生报告 PDF 导出 — 请求/响应模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class FushengReportPdfRequest(BaseModel):
    """档案驱动的浮生报告 PDF 请求（无需登录）。"""

    label: str = Field("浮生报告", max_length=80)
    birth_dt: str = Field(..., description="出生时间 ISO，如 1990-01-15T08:30:00")
    lon: float = Field(..., ge=73, le=135)
    tz: str = Field("Asia/Shanghai")
    gender: Literal["male", "female"]
    solar_time_enabled: bool = False
    mode: Literal["dual", "single"] = "dual"
    city_name: str = ""
    calendar_mode: Literal["gregorian", "lunar"] = "gregorian"
    is_leap_month: bool = False
    surname: str = ""
    given_name: str = ""
    focus_topic: str = ""
    notes: str = ""
    year_divide: str = Field(
        "lichun",
        description="紫微年界：lichun | normal（与 /ziwei/full 一致）",
    )
    day_divide: str = Field(
        "solar_next",
        description="晚子时换日：solar_next | forward | current",
    )
    include_liuri: bool = Field(
        True,
        description="八字是否附带流日/流时（与 /bazi/full 默认一致）",
    )
    zi_day_rule: str = Field(
        "sxtwl",
        description="子时换日：sxtwl | early_zi_prev_day | early_zi_same_day",
    )
    late_zishi: bool = Field(
        True,
        description="晚子时(23:00~00:00)视为次日（与 /ziwei/full 一致）",
    )
    birth_time_precision: Literal["exact", "hour", "approximate", "unknown"] = Field(
        "exact",
        description="出生时辰精度（与 /bazi/full 一致）",
    )
    unknown_time_fallback: Literal["midday", "noon", "start_of_hour"] | None = Field(
        None,
        description="时辰未知时的默认锚点（FE 档案口径，写入 PDF meta）",
    )

    @model_validator(mode="after")
    def _validate_algo_fields(self):
        if self.year_divide not in ("lichun", "normal"):
            raise ValueError("year_divide must be lichun or normal")
        if self.day_divide not in ("solar_next", "forward", "current"):
            raise ValueError("day_divide must be solar_next, forward, or current")
        if self.zi_day_rule not in ("sxtwl", "early_zi_prev_day", "early_zi_same_day"):
            raise ValueError("invalid zi_day_rule")
        if self.unknown_time_fallback is not None and self.unknown_time_fallback not in (
            "midday",
            "noon",
            "start_of_hour",
        ):
            raise ValueError("invalid unknown_time_fallback")
        return self
