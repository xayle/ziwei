"""
西方占星路由 — §6 出生盘基础

GET /api/v1/western/chart  — 计算出生盘（无需登录）
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query

from app.schemas.western import SolarReturnResponse, WesternChartResponse
from services.western_astrology import compute_chart, solar_return_chart

router = APIRouter(prefix="/api/v1/western", tags=["西方占星"])


@router.get(
    "/chart",
    response_model=WesternChartResponse,
    summary="西方出生盘计算（§6.1）",
)
def get_western_chart(
    dt: str = Query(..., description="出生时间（本地时间），格式 ISO 8601，如 2000-01-01T12:00:00"),
    lat: float = Query(..., ge=-90.0, le=90.0, description="地理纬度（北纬正）"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="地理经度（东经正）"),
    tz: str = Query("Asia/Shanghai", description="时区名称，如 Asia/Shanghai"),
) -> WesternChartResponse:
    """
    根据出生时间和地理坐标计算西方占星出生盘。

    - 行星位置精度：太阳 ±0.01°，月亮 ±1°，其他行星 ±2-5°（判星座足够）
    - 上升/中天精度：±0.1°

    返回：行星在黄道上的位置、上升/中天、行星相位、元素/模式统计。
    """
    # 解析时区
    try:
        zi = ZoneInfo(tz)
    except (ZoneInfoNotFoundError, KeyError):
        raise HTTPException(status_code=422, detail=f"无效时区: {tz!r}")

    # 解析本地时间
    try:
        local_dt = datetime.fromisoformat(dt)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"无效时间格式: {dt!r}，请使用 ISO 8601 格式")

    # 转换为 UTC
    if local_dt.tzinfo is None:
        local_dt = local_dt.replace(tzinfo=zi)

    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

    try:
        result = compute_chart(utc_dt, lat, lon)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"出生盘计算失败: {exc}") from exc

    return WesternChartResponse(**result)


@router.get(
    "/solar-return",
    response_model=SolarReturnResponse,
    summary="太阳回归年盘（§6.2）",
)
def get_solar_return(
    natal_dt:  str   = Query(..., description="出生时间（本地 ISO 8601）"),
    natal_lat: float = Query(..., ge=-90.0, le=90.0,   description="出生地纬度"),
    natal_lon: float = Query(..., ge=-180.0, le=180.0,  description="出生地经度"),
    natal_tz:  str   = Query("Asia/Shanghai",           description="出生时区"),
    sr_year:   int   = Query(..., ge=1900, le=2100,     description="回归年（公历年）"),
    sr_lat:    float = Query(..., ge=-90.0, le=90.0,   description="回归年所在地纬度"),
    sr_lon:    float = Query(..., ge=-180.0, le=180.0,  description="回归年所在地经度"),
) -> SolarReturnResponse:
    """
    计算指定年份的太阳回归年盘。

    首先根据出生数据求出出生太阳黄经，
    然后使用 Newton 迭代精确定位该年太阳回到相同黄经的时刻，
    并在此时刻 + 给定地点计算完整星盘。
    """
    try:
        zi = ZoneInfo(natal_tz)
    except (ZoneInfoNotFoundError, KeyError):
        raise HTTPException(status_code=422, detail=f"无效时区: {natal_tz!r}")

    try:
        local_dt = datetime.fromisoformat(natal_dt)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"无效时间格式: {natal_dt!r}")

    if local_dt.tzinfo is None:
        local_dt = local_dt.replace(tzinfo=zi)
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

    try:
        natal = compute_chart(utc_dt, natal_lat, natal_lon)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"出生盘计算失败: {exc}") from exc

    natal_sun_lon = natal["planets"][0]["longitude"]  # 太阳排第一

    try:
        sr = solar_return_chart(natal_sun_lon, sr_year, sr_lat, sr_lon)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"太阳回归盘计算失败: {exc}") from exc

    return SolarReturnResponse(**sr)
