"""Archive bundle: bazi + ziwei snapshot in one call (BE-A05)."""

from __future__ import annotations

import asyncio
from datetime import datetime

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


def _case_to_ziwei_request(case: Case) -> ZiweiRequest:
    dt = datetime.fromisoformat(case.birth_dt_local)
    return ZiweiRequest(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        gender=case.gender or "male",
        year_divide=getattr(case, "year_divide", "lichun") or "lichun",
        day_divide=getattr(case, "day_divide", "solar_next") or "solar_next",
        template_version=getattr(case, "ziwei_template_version", "standard") or "standard",
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

    dt = _normalize_birth_dt_text(case.birth_dt_local, case.tz or "Asia/Shanghai")
    bazi_req = BaziFullRequest(
        dt=dt,
        lon=float(case.lon),
        tz=case.tz or "Asia/Shanghai",
        gender=case.gender or "male",
        solar_time_enabled=bool(case.solar_time_enabled),
    )
    bazi_resp = bazi_full(bazi_req, request_id=f"archive-{payload.case_id}")
    bazi_dict = bazi_resp.model_dump(mode="json")

    ziwei_dict = None
    missing: list[str] = list(bazi_dict.get("missing_fields") or [])
    if payload.include_ziwei:
        try:
            zw_req = _case_to_ziwei_request(case)
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
