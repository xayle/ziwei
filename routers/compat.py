"""
合婚 API 路由（§5.1 四柱合婚）

GET  /api/v1/compat/bazi  — 无需登录（已弃用，请改用 POST /relation/full）
POST /api/v1/compat/full  — 已弃用，委托 POST /api/v1/relation/full?relation_type=couple
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from services.compatibility import compute_compatibility
from services.relation_engine.composer import compute_relation_full

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
    summary="四柱合婚评分（§5.1）[已弃用，请改用 POST /relation/full]",
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
        return dt.replace(tzinfo=None)

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


class PersonFullInput(BaseModel):
    birth_datetime: str = Field(..., description="本地出生时间，ISO 8601 格式")
    tz: str = Field("Asia/Shanghai", description="时区")
    longitude: float = Field(116.41, ge=-180, le=180, description="出生地经度")
    gender: str = Field("male", description="性别：male / female / 男 / 女")
    liunian_year: int | None = Field(None, description="流年年份（紫微用）")


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
    combined_score: float = Field(0.0, description="综合加权分（0-100）")
    summary: str = ""


class CompatFullRequest(BaseModel):
    person_a: PersonFullInput
    person_b: PersonFullInput
    include_bazi: bool = Field(True, description="是否计算八字")
    include_ziwei: bool = Field(True, description="是否计算紫微")


def _map_relation_to_compat_full(
    relation: dict[str, Any], include_bazi: bool, include_ziwei: bool
) -> CompatFullResponse:
    bazi_result: CompatResponse | None = None
    ziwei_result: ZiweiCompatSection | None = None

    if include_bazi and relation.get("bazi"):
        bz = relation["bazi"]
        pa = relation["person_a"]["pillars_primary"]
        pb = relation["person_b"]["pillars_primary"]
        details = [
            CompatDetail(
                dimension=d["label"],
                score=d["score"],
                max=int(d["max_score"]),
                description=d["description"],
                level="佳" if d["score"] >= d["max_score"] * 0.7 else "中",
            )
            for d in bz.get("dimensions") or []
        ]
        bazi_result = CompatResponse(
            score=int(bz.get("score") or relation["combined_score"]),
            grade=relation.get("grade") or "中",
            summary=relation.get("summary") or "",
            details=details,
            person_a=PersonSummary(
                pillars={k: {"stem": v["stem"], "branch": v["branch"]} for k, v in pa.items()},
                weights={},
                day_stem=pa["day"]["stem"],
                day_elem="",
            ),
            person_b=PersonSummary(
                pillars={k: {"stem": v["stem"], "branch": v["branch"]} for k, v in pb.items()},
                weights={},
                day_stem=pb["day"]["stem"],
                day_elem="",
            ),
        )

    if include_ziwei and relation.get("ziwei"):
        zw = relation["ziwei"]
        ziwei_result = ZiweiCompatSection(
            total_score=int(zw.get("score") or 0),
            max_score=int(zw.get("max_score") or 100),
            level=relation.get("grade") or "中签",
            summary=relation.get("summary") or "",
            dimensions=[
                ZiweiCompatDimension(
                    name=d["label"],
                    score=int(d["score"]),
                    max_score=int(d["max_score"]),
                    description=d["description"],
                )
                for d in zw.get("dimensions") or []
            ],
            harmony_points=list(zw.get("harmony_points") or []),
            conflict_points=list(zw.get("conflict_points") or []),
        )

    return CompatFullResponse(
        bazi=bazi_result,
        ziwei=ziwei_result,
        combined_score=float(relation.get("combined_score") or 0),
        summary=relation.get("summary") or "",
    )


@router.post(
    "/full",
    response_model=CompatFullResponse,
    summary="综合合婚——八字 + 紫微双引擎 [已弃用 → POST /api/v1/relation/full]",
    deprecated=True,
)
async def post_compat_full(body: CompatFullRequest, response: Response) -> CompatFullResponse:
    """Deprecated: delegates to unified relation engine (couple)."""
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</api/v1/relation/full>; rel="successor-version"'

    for person, label in ((body.person_a, "甲方"), (body.person_b, "乙方")):
        try:
            ZoneInfo(person.tz)
        except (ZoneInfoNotFoundError, KeyError):
            raise HTTPException(422, f"{label}时区无效: {person.tz!r}")
        try:
            datetime.fromisoformat(person.birth_datetime)
        except ValueError:
            raise HTTPException(422, f"{label}出生时间格式无效: {person.birth_datetime!r}")

    try:
        relation = compute_relation_full(
            relation_type="couple",
            person_a={
                "birth_datetime": body.person_a.birth_datetime,
                "tz": body.person_a.tz,
                "longitude": body.person_a.longitude,
                "gender": body.person_a.gender,
                "label": "甲方",
            },
            person_b={
                "birth_datetime": body.person_b.birth_datetime,
                "tz": body.person_b.tz,
                "longitude": body.person_b.longitude,
                "gender": body.person_b.gender,
                "label": "乙方",
            },
            options={
                "include_bazi": body.include_bazi,
                "include_ziwei": body.include_ziwei,
                "liunian_year": body.person_a.liunian_year or body.person_b.liunian_year,
            },
        )
    except Exception as exc:
        raise HTTPException(500, f"合婚计算失败: {exc}") from exc

    return _map_relation_to_compat_full(relation, body.include_bazi, body.include_ziwei)
