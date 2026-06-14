"""
合婚 API 路由（§5.1 四柱合婚）

GET  /api/v1/compat/bazi  — 无需登录（已弃用，请改用 POST /full）
POST /api/v1/compat/full  — 综合合婚（八字 + 紫微双引擎）
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.compatibility import compute_compatibility

router = APIRouter(prefix="/api/v1/compat", tags=["合婚"])


class CompatDetail(BaseModel):
    dimension: str
    score: float
    max: int
    description: str
    level: str


class PersonSummary(BaseModel):
    pillars: dict[str, Any]
    weights: dict[str, float]
    day_stem: str
    day_elem: str


class CompatResponse(BaseModel):
    score: int
    grade: str
    summary: str
    details: list[CompatDetail]
    person_a: PersonSummary
    person_b: PersonSummary


@router.get(
    "/bazi",
    response_model=CompatResponse,
    summary="四柱合婚评分（§5.1）[已弃用，请改用 POST /full]",
    deprecated=True,
)
def get_bazi_compat(
    a_dt: str = Query(..., description="甲方出生时间（本地 ISO 8601）"),
    a_tz: str = Query("Asia/Shanghai", description="甲方时区"),
    a_lon: float = Query(116.41, ge=-180, le=180, description="甲方出生地经度"),
    b_dt: str = Query(..., description="乙方出生时间（本地 ISO 8601）"),
    b_tz: str = Query("Asia/Shanghai", description="乙方时区"),
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
            _parse(a_dt),
            a_lon,
            a_tz,
            _parse(b_dt),
            b_lon,
            b_tz,
        )
    except Exception as exc:
        raise HTTPException(500, f"合婚计算失败: {exc}") from exc

    return CompatResponse(**result)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/compat/full  — 双引擎综合合婚
# ─────────────────────────────────────────────────────────────────────────────


class PersonFullInput(BaseModel):
    """同时满足八字和紫微双引擎所需的人员输入。"""

    birth_datetime: str = Field(..., description="本地出生时间，ISO 8601 格式（如 1990-06-15T10:30:00）")
    tz: str = Field("Asia/Shanghai", description="时区，如 Asia/Shanghai")
    longitude: float = Field(116.41, ge=-180, le=180, description="出生地经度（东经正数）")
    gender: str = Field("male", description="性别：male / female / 男 / 女")
    liunian_year: int | None = Field(None, description="流年年份（紫微用，不填默认当年）")


class ZiweiCompatDimension(BaseModel):
    name: str = ""
    score: int = 0
    max_score: int = 0
    description: str = ""


class ZiweiCompatSection(BaseModel):
    total_score: int = 0
    max_score: int = 0
    level: str = ""
    summary: str = ""
    dimensions: list[ZiweiCompatDimension] = []
    harmony_points: list[str] = []
    conflict_points: list[str] = []


class CompatFullResponse(BaseModel):
    bazi: CompatResponse | None = None
    ziwei: ZiweiCompatSection | None = None
    combined_score: float = Field(0.0, description="八字与紫微综合加权分（0-100）")
    summary: str = ""


class CompatFullRequest(BaseModel):
    person_a: PersonFullInput
    person_b: PersonFullInput
    include_bazi: bool = Field(True, description="是否计算八字合婚")
    include_ziwei: bool = Field(True, description="是否计算紫微合盘")


@router.post(
    "/full",
    response_model=CompatFullResponse,
    summary="综合合婚——八字 + 紫微双引擎",
)
async def post_compat_full(body: CompatFullRequest) -> CompatFullResponse:
    """
    综合合婚接口，同时调用八字与紫微双引擎，返回合并评分。

    - 八字合婚：四柱生克冲合（最高100分）
    - 紫微合盘：命宫、五行、年支等维度（最高100分）
    - combined_score = 八字×0.5 + 紫微×0.5（若仅启用一项则权重100%）
    """
    req_a, req_b = body.person_a, body.person_b

    def _validate_and_parse(person: PersonFullInput, label: str) -> datetime:
        try:
            ZoneInfo(person.tz)
        except (ZoneInfoNotFoundError, KeyError):
            raise HTTPException(422, f"{label}时区无效: {person.tz!r}")
        try:
            return datetime.fromisoformat(person.birth_datetime).replace(tzinfo=None)
        except ValueError:
            raise HTTPException(422, f"{label}出生时间格式无效: {person.birth_datetime!r}")

    dt_a = _validate_and_parse(req_a, "甲方")
    dt_b = _validate_and_parse(req_b, "乙方")

    bazi_result: CompatResponse | None = None
    ziwei_result: ZiweiCompatSection | None = None

    # ── 八字引擎 ──────────────────────────────────────────────
    if body.include_bazi:
        try:
            raw = compute_compatibility(dt_a, req_a.longitude, req_a.tz, dt_b, req_b.longitude, req_b.tz)
            bazi_result = CompatResponse(**raw)
        except Exception as exc:
            raise HTTPException(500, f"八字合婚计算失败: {exc}") from exc

    # ── 紫微引擎 ──────────────────────────────────────────────
    if body.include_ziwei:
        try:
            from services.ziwei_engine.compatibility import calc_compatibility
            from services.ziwei_engine.main import ziwei_full

            def _gender_cn(g: str) -> str:
                return g if g in ("男", "女") else ("男" if g == "male" else "女")

            def _make_ziwei_args(person: PersonFullInput, dt: datetime):
                return (
                    dt.year,
                    dt.month,
                    dt.day,
                    dt.hour,
                    dt.minute,
                    _gender_cn(person.gender),
                    person.liunian_year,
                    person.longitude,
                )

            chart_a = await asyncio.to_thread(ziwei_full, *_make_ziwei_args(req_a, dt_a))
            chart_b = await asyncio.to_thread(ziwei_full, *_make_ziwei_args(req_b, dt_b))
            zw_res = calc_compatibility(chart_a, chart_b)
            ziwei_result = ZiweiCompatSection(
                total_score=zw_res.total_score,
                max_score=zw_res.max_score,
                level=zw_res.level,
                summary=zw_res.summary,
                dimensions=[
                    ZiweiCompatDimension(name=d.name, score=d.score, max_score=d.max_score, description=d.description)
                    for d in zw_res.dimensions
                ],
                harmony_points=list(zw_res.harmony_points or []),
                conflict_points=list(zw_res.conflict_points or []),
            )
        except Exception as exc:
            raise HTTPException(500, f"紫微合盘计算失败: {exc}") from exc

    # ── 综合评分 ──────────────────────────────────────────────
    scores: list[float] = []
    if bazi_result:
        scores.append(float(bazi_result.score))
    if ziwei_result:
        scores.append(ziwei_result.total_score / max(ziwei_result.max_score, 1) * 100)
    combined = round(sum(scores) / len(scores), 1) if scores else 0.0

    parts: list[str] = []
    if bazi_result:
        parts.append(f"八字合婚 {bazi_result.score} 分（{bazi_result.grade}）")
    if ziwei_result:
        parts.append(f"紫微合盘 {ziwei_result.total_score}/{ziwei_result.max_score} 分（{ziwei_result.level}）")
    summary = "；".join(parts) + f"，综合加权 {combined} 分。" if parts else "无可用结果。"

    return CompatFullResponse(
        bazi=bazi_result,
        ziwei=ziwei_result,
        combined_score=combined,
        summary=summary,
    )
