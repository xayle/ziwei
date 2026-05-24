"""
合婚 API 路由（§5.1 四柱合婚）

GET /api/v1/compat/bazi  — 无需登录
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.compatibility import compute_compatibility

router = APIRouter(prefix="/api/v1/compat", tags=["合婚"])


class CompatDetail(BaseModel):
    dimension:   str
    score:       float
    max:         int
    description: str
    level:       str


class PersonSummary(BaseModel):
    pillars:  dict[str, Any]
    weights:  dict[str, float]
    day_stem: str
    day_elem: str


class CompatResponse(BaseModel):
    score:    int
    grade:    str
    summary:  str
    details:  list[CompatDetail]
    person_a: PersonSummary
    person_b: PersonSummary


@router.get(
    "/bazi",
    response_model=CompatResponse,
    summary="四柱合婚评分（§5.1）",
)
def get_bazi_compat(
    a_dt:  str   = Query(..., description="甲方出生时间（本地 ISO 8601）"),
    a_tz:  str   = Query("Asia/Shanghai", description="甲方时区"),
    a_lon: float = Query(116.41, ge=-180, le=180, description="甲方出生地经度"),
    b_dt:  str   = Query(..., description="乙方出生时间（本地 ISO 8601）"),
    b_tz:  str   = Query("Asia/Shanghai", description="乙方时区"),
    b_lon: float = Query(116.41, ge=-180, le=180, description="乙方出生地经度"),
) -> CompatResponse:
    """
    四柱合婚综合评分（0-100 分）。

    评分维度：
    - 日主五行生克（40分）：产生/被产生 > 同行 > 克/被克
    - 年支合冲（30分）：六合 > 三合 > 无关系 > 六冲
    - 五行互补（20分）：双方五行分布互补程度
    - 天干合化（10分）：四柱天干间的五合/冲克数量
    """
    for name, dt_str, tz_str in [("甲方", a_dt, a_tz), ("乙方", b_dt, b_tz)]:
        try:
            ZoneInfo(tz_str)
        except (ZoneInfoNotFoundError, KeyError):
            raise HTTPException(422, f"{name}时区无效: {tz_str!r}")
        try:
            datetime.fromisoformat(dt_str)
        except ValueError:
            raise HTTPException(422, f"{name}时间格式无效: {dt_str!r}")

    def _parse(dt_str: str) -> datetime:
        dt = datetime.fromisoformat(dt_str)
        return dt.replace(tzinfo=None)  # verify_full 接受 naive datetime

    try:
        result = compute_compatibility(
            _parse(a_dt), a_lon, a_tz,
            _parse(b_dt), b_lon, b_tz,
        )
    except Exception as exc:
        raise HTTPException(500, f"合婚计算失败: {exc}") from exc

    return CompatResponse(**result)
