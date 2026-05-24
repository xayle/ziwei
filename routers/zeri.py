"""
routers/zeri.py — §13 择日推荐端点

端点列表：
    GET  /api/v1/zeri/recommend — 按月推荐吉日（无需登录，只需提供命盘参数）
    GET  /api/v1/zeri/purposes  — 返回支持的用途列表
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.zeri import ZeriDayResponse, ZeriMonthResponse
from services.ziwei_engine.tables import BRANCHES
from services.ziwei_engine.zeri_engine import PURPOSES, recommend_month

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/zeri",
    tags=["择日推荐"],
)

# 有效的用途 key 集合
_VALID_PURPOSES = set(PURPOSES.keys())
# 有效的地支集合
_VALID_BRANCHES = set(BRANCHES)
# 有效的五行局名前缀
_VALID_WX = {"水", "木", "火", "土", "金"}


# ─────────────────────────────────────────────────────────────
# GET /api/v1/zeri/purposes
# ─────────────────────────────────────────────────────────────

@router.get(
    "/purposes",
    summary="获取支持的择日用途列表",
    response_model=dict,
)
def list_purposes() -> dict:
    """返回所有支持的用途及其中文标签。"""
    return {"purposes": PURPOSES}


# ─────────────────────────────────────────────────────────────
# GET /api/v1/zeri/recommend
# ─────────────────────────────────────────────────────────────

@router.get(
    "/recommend",
    response_model=ZeriMonthResponse,
    summary="按月择日推荐",
    description=(
        "根据命主紫微命盘参数（命宫地支、五行局）为指定年月逐日评分，"
        "返回吉日日历和推荐日期列表。\n\n"
        "**无需登录**，但需提供命宫地支和五行局。\n\n"
        "| 参数 | 说明 | 示例 |\n"
        "|------|------|---------|\n"
        "| `life_palace_branch` | 命宫地支 | `子` |\n"
        "| `wuxing_ju_name` | 五行局（含数字局也可） | `水二局` |\n"
        "| `natal_year_branch` | 本命年支（可选） | `午` |\n"
        "| `purpose` | 用途 | `marriage` |\n"
    ),
)
def recommend(
    year: int = Query(2026, ge=1900, le=2100, description="公历年份"),
    month: int = Query(..., ge=1, le=12, description="公历月份"),
    life_palace_branch: str = Query(..., description="命宫地支，如 '子'"),
    wuxing_ju_name: str = Query(..., description="五行局名，如 '水二局'"),
    natal_year_branch: str = Query(default="", description="本命年支（可选）"),
    purpose: str = Query(default="general", description="用途"),
) -> ZeriMonthResponse:
    # ── 参数校验
    if life_palace_branch not in _VALID_BRANCHES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"life_palace_branch 必须为有效地支（子丑寅卯辰巳午未申酉戌亥），收到 '{life_palace_branch}'",
        )

    if natal_year_branch and natal_year_branch not in _VALID_BRANCHES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"natal_year_branch 必须为有效地支或空字符串，收到 '{natal_year_branch}'",
        )

    if purpose not in _VALID_PURPOSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"purpose 必须为 {sorted(_VALID_PURPOSES)} 之一，收到 '{purpose}'",
        )

    wx_ok = any(wx in wuxing_ju_name for wx in _VALID_WX)
    if not wx_ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"wuxing_ju_name 必须包含五行字（水/木/火/土/金），收到 '{wuxing_ju_name}'",
        )

    # ── 调用引擎
    try:
        result = recommend_month(
            year=year,
            month=month,
            life_palace_branch=life_palace_branch,
            wuxing_ju_name=wuxing_ju_name,
            natal_year_branch=natal_year_branch,
            purpose=purpose,
        )
    except Exception as exc:
        logger.exception("择日引擎异常: year=%s month=%s", year, month)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"择日计算失败：{exc}",
        ) from exc

    # ── 构造响应
    days_resp = [
        ZeriDayResponse(
            date=d.date,
            weekday=d.weekday,
            day_gz=d.day_gz,
            day_stem=d.day_stem,
            day_branch=d.day_branch,
            lunar_info=d.lunar_info,
            score=d.score,
            level=d.level,
            level_css=d.level_css,
            evidence=d.evidence,
            is_break=d.is_break,
            is_virtue=d.is_virtue,
        )
        for d in result.days
    ]

    return ZeriMonthResponse(
        year=result.year,
        month=result.month,
        purpose=result.purpose,
        purpose_label=result.purpose_label,
        year_gz=result.year_gz,
        month_gz=result.month_gz,
        days=days_resp,
        top_days=result.top_days,
    )
