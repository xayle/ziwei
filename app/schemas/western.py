"""
西方占星 Pydantic 模型（§6.1 出生盘基础）
"""

from __future__ import annotations

from pydantic import BaseModel


class PlanetDetail(BaseModel):
    name_en: str
    name_cn: str
    symbol: str
    longitude: float
    retrograde: bool
    sign_index: int
    sign_cn: str
    sign_en: str
    sign_symbol: str
    element: str
    element_cn: str
    mode: str
    mode_cn: str
    degree: float
    degree_str: str


class ChartPoint(BaseModel):
    longitude: float
    sign_index: int
    sign_cn: str
    sign_en: str
    sign_symbol: str
    element: str
    element_cn: str
    mode: str
    mode_cn: str
    degree: float
    degree_str: str


class AspectItem(BaseModel):
    planet1: str
    planet2: str
    aspect_cn: str
    aspect_en: str
    angle: int
    orb: float
    color: str


class WesternChartResponse(BaseModel):
    julian_day: float
    planets: list[PlanetDetail]
    ascendant: ChartPoint
    midheaven: ChartPoint
    aspects: list[AspectItem]
    element_counts: dict[str, int]
    mode_counts: dict[str, int]
    geocentric_longitudes: dict[str, float]
    heliocentric_longitudes: dict[str, float]


class SolarReturnResponse(WesternChartResponse):
    """太阳回归年盘响应（§6.2）"""

    sr_dt_utc: str
    sr_year: int
    natal_sun_lon: float
