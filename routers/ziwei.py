"""
routers/ziwei.py — 紫微斗数 API 路由

POST /api/v1/ziwei/full  → 完整命盘计算
GET  /api/v1/ziwei/demo  → 演示命盘（用黄金测试案例）
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.ziwei import (
    ZiweiRequest,
    ZiweiResponse,
    LunarResponse,
    PalaceResponse,
    StarInfo,
    DayunResponse,
    DayunItemResponse,
    LiunianResponse,
    FlyingChartResponse,
    FlyingPalaceResponse,
)
from services.ziwei_engine import ziwei_full, ZiweiChart

router = APIRouter(prefix="/api/v1/ziwei", tags=["紫微斗数"])


def _chart_to_response(chart: ZiweiChart) -> ZiweiResponse:
    """将 ZiweiChart 数据对象转换为 Pydantic 响应模型。"""
    lunar_resp = LunarResponse(
        lunar_year=chart.lunar.lunar_year,
        lunar_month=chart.lunar.lunar_month,
        lunar_day=chart.lunar.lunar_day,
        is_leap_month=chart.lunar.is_leap_month,
        year_gz=chart.lunar.year_gz,
        month_gz=chart.lunar.month_gz,
        hour_branch=chart.lunar.hour_branch,
    )

    palaces_resp = [
        PalaceResponse(
            index=p.index,
            name=p.name,
            branch=p.branch,
            stem=p.stem,
            main_stars=[
                StarInfo(
                    name=s["name"],
                    brightness=s["brightness"],
                    brightness_val=s["brightness_val"],
                    transforms=s["transforms"],
                )
                for s in p.main_stars
            ],
            aux_stars=p.aux_stars,
            flying_out=p.flying_out,
            analysis=p.analysis,
        )
        for p in chart.palaces
    ]

    dayun_resp = DayunResponse(
        forward=chart.dayun.forward,
        start_age=chart.dayun.start_age,
        start_age_exact=chart.dayun.start_age_exact,
        items=[
            DayunItemResponse(
                index=d.index,
                ganzhi=d.ganzhi,
                start_age=d.start_age,
                end_age=d.end_age,
                start_year=d.start_year,
            )
            for d in chart.dayun.items
        ],
    )

    liunian_resp = None
    if chart.liunian:
        liunian_resp = LiunianResponse(
            year=chart.liunian.year,
            year_gz=chart.liunian.year_gz,
            life_palace_branch=chart.liunian.life_palace_branch,
            sihua=chart.liunian.sihua,
        )

    flying_resp = None
    if chart.flying:
        flying_resp = FlyingChartResponse(
            palaces=[
                FlyingPalaceResponse(
                    palace_name=fp.palace_name,
                    stem_name=fp.stem_name,
                    flying_out=fp.flying_out,
                )
                for fp in chart.flying.palaces
            ],
            received=chart.flying.received,
        )

    return ZiweiResponse(
        birth_solar=chart.birth_solar,
        gender=chart.gender,
        lunar=lunar_resp,
        life_palace_gz=chart.life_palace_gz,
        body_palace_gz=chart.body_palace_gz,
        wuxing_ju=chart.wuxing_ju,
        wuxing_ju_name=chart.wuxing_ju_name,
        palaces=palaces_resp,
        dayun=dayun_resp,
        liunian=liunian_resp,
        flying=flying_resp,
        summary=chart.summary,
        analysis=chart.analysis,
    )


@router.post("/full", response_model=ZiweiResponse, summary="计算完整紫微命盘")
async def compute_ziwei(req: ZiweiRequest) -> ZiweiResponse:
    """
    输入公历出生时间和性别，返回完整紫微斗数命盘。

    包含：农历信息、命宫身宫、五行局、14主星亮度、
    辅星杂曜、四化、大运、流年、飞星盘、逐宫解读。
    """
    try:
        chart = ziwei_full(
            year=req.year,
            month=req.month,
            day=req.day,
            hour=req.hour,
            minute=req.minute,
            gender=req.gender,
            liunian_year=req.liunian_year,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _chart_to_response(chart)


@router.get("/demo", response_model=ZiweiResponse, summary="演示命盘（壬午年正月三十未时女）")
async def demo_ziwei() -> ZiweiResponse:
    """
    黄金测试案例：2002-03-13 14:55 女
    预期：水二局，命宫丁未，紫微在辰宫，天府在子宫。
    """
    try:
        chart = ziwei_full(2002, 3, 13, 14, 55, "女")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _chart_to_response(chart)
