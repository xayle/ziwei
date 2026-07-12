"""Archive bundle: bazi + ziwei snapshot in one call (BE-A05)."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.dependencies import RequiredUser
from app.models import Case
from app.schemas import BaziFullRequest
from app.schemas.ziwei import ZiweiRequest
from db import get_session
from services.bazi_full_service import bazi_full
from services.quota_service import enforce_quota
from services.rate_limit import limiter
from services.relation_engine.composer import _normalize_gender
from services.ziwei_engine import ziwei_full

router = APIRouter(prefix="/api/v1/fusheng", tags=["浮生档案"])


class ArchiveBundleRequest(BaseModel):
    case_id: str
    include_ziwei: bool = True


class ArchiveBundleResponse(BaseModel):
    case_id: str
    bazi: dict
    ziwei: dict | None = None
    missing_fields: list[str] = Field(default_factory=list)


def _bazi_gender(case: Case) -> Literal["male", "female"]:
    raw = (case.gender or "male").lower()
    if raw in ("female", "f", "女"):
        return "female"
    return "male"


def _case_to_bazi_request(case: Case, dt: datetime) -> BaziFullRequest:
    precision = case.birth_time_precision or "exact"
    if precision not in ("exact", "hour", "approximate", "unknown"):
        precision = "exact"
    return BaziFullRequest(
        dt=dt,
        lon=float(case.lon),
        tz=case.tz or "Asia/Shanghai",
        gender=_bazi_gender(case),
        solar_time_enabled=bool(case.solar_time_enabled),
        zi_day_rule=case.zi_day_rule or "sxtwl",
        birth_time_precision=precision,  # type: ignore[arg-type]
        include_liuri=True,
    )


def _case_to_ziwei_request(case: Case, dt: datetime) -> ZiweiRequest:
    sihua_stem_indices = None
    if (case.ziwei_sihua_method or "quanshu") == "zhongzhou":
        sihua_stem_indices = {"庚": 1, "辛": 1}

    return ZiweiRequest(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        gender=_normalize_gender(case.gender or "male"),
        longitude=float(case.lon) if case.solar_time_enabled else None,
        template_version=case.ziwei_template_version or "standard",
        leap_month_method="same" if case.is_leap_month else "mid",
        year_divide=case.year_divide or "lichun",
        day_divide=case.day_divide or "solar_next",
        late_zishi=getattr(case, "late_zishi", True),
        brightness_method=case.ziwei_brightness_method or "standard",
        youbi_method=case.ziwei_youbi_method or "month",
        liunian_sihua_method=case.ziwei_liunian_sihua_method or "year_stem",
        kuiyue_method=case.ziwei_kuiyue_method or "standard",
        tianma_method=case.ziwei_tianma_method or "year",
        sihua_stem_indices=sihua_stem_indices,
        include_flow_liuri=True,
    )


@router.post(
    "/archive-bundle",
    response_model=ArchiveBundleResponse,
    summary="八字+紫微一屏编排快照",
)
@limiter.limit("15/minute")
async def archive_bundle(
    request: Request,
    payload: ArchiveBundleRequest,
    user: RequiredUser,
    session: Session = Depends(get_session),
) -> ArchiveBundleResponse:
    enforce_quota(request, "structured_text")
    case = session.get(Case, payload.case_id)
    if case is None or case.deleted_at is not None or case.owner_id != user.id:
        raise HTTPException(status_code=404, detail="案例不存在")

    from routers.bazi import _normalize_birth_dt_text
    from routers.ziwei import _chart_to_response, _ziwei_full_args

    dt = _normalize_birth_dt_text(
        case.birth_dt_local,
        case.tz or "Asia/Shanghai",
        precision=case.birth_time_precision or "exact",
        unknown_time_fallback=case.unknown_time_fallback or "midday",
    )
    bazi_req = _case_to_bazi_request(case, dt)
    bazi_resp = bazi_full(bazi_req, request_id=f"archive-{payload.case_id}")
    bazi_dict = bazi_resp.model_dump(mode="json")

    ziwei_dict = None
    missing: list[str] = list(bazi_dict.get("missing_fields") or [])
    if payload.include_ziwei:
        try:
            zw_req = _case_to_ziwei_request(case, dt)
            chart = await asyncio.to_thread(ziwei_full, *_ziwei_full_args(zw_req))
            zw_resp = _chart_to_response(
                chart,
                template=zw_req.template_version,
                req=zw_req,
                birth={
                    "year": zw_req.year,
                    "month": zw_req.month,
                    "day": zw_req.day,
                    "hour": zw_req.hour,
                    "minute": zw_req.minute or 0,
                    "gender": zw_req.gender,
                    "year_divide": zw_req.year_divide,
                    "day_divide": zw_req.day_divide,
                },
            )
            ziwei_dict = zw_resp.model_dump(mode="json")
            missing.extend(ziwei_dict.get("missing_fields") or [])
        except Exception as exc:
            missing.append(f"ziwei_bundle:{exc}")

    return ArchiveBundleResponse(
        case_id=payload.case_id,
        bazi=bazi_dict,
        ziwei=ziwei_dict,
        missing_fields=sorted(set(missing)),
    )
