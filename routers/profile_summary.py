"""Profile summary API — GET /api/v1/profile/{case_id}/summary."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.dependencies import RequiredUser
from app.models import Case
from app.schemas.relation_compat import ProfileSummaryResponse
from db import get_session
from services.case_chart_requests import case_to_bazi_request, case_to_ziwei_request
from services.chart_snapshot_service import build_bazi_snapshot, build_ziwei_snapshot
from services.content_policy import default_disclaimer_block
from services.relation_engine.timeline import _liunian_branch, _tai_sui_tag

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get(
    "/{case_id}/summary",
    response_model=ProfileSummaryResponse,
    summary="个人档案首屏摘要",
)
def get_profile_summary(
    case_id: str,
    user: RequiredUser,
    session: Session = Depends(get_session),
) -> ProfileSummaryResponse:
    case = session.exec(select(Case).where(Case.id == case_id)).first()
    if case is None:
        raise HTTPException(404, "Case not found")
    if case.owner_id != user.id:
        raise HTTPException(403, "Forbidden")

    from routers.bazi import _normalize_birth_dt_text

    dt = _normalize_birth_dt_text(
        case.birth_dt_local,
        case.tz or "Asia/Shanghai",
        precision=case.birth_time_precision or "exact",
        unknown_time_fallback=case.unknown_time_fallback or "midday",
    )

    bazi_req = case_to_bazi_request(case, dt)
    bazi_snap = build_bazi_snapshot(bazi_req)
    resp = bazi_snap.response
    pillars = resp.pillars_primary
    pillars_dict = {
        "year": f"{pillars.year.stem}{pillars.year.branch}",
        "month": f"{pillars.month.stem}{pillars.month.branch}",
        "day": f"{pillars.day.stem}{pillars.day.branch}",
        "hour": f"{pillars.hour.stem}{pillars.hour.branch}",
    }

    geju = ""
    if resp.geju:
        geju = resp.geju.geju_name or ""
        if resp.geju.inference_tags:
            geju = f"{geju}·{'/'.join(resp.geju.inference_tags[:2])}"

    favor: list[str] = []
    strength = None
    if resp.yongshen:
        favor = list(resp.yongshen.favor or resp.yongshen.engine_favor or [])
    if resp.day_master_strength:
        strength = resp.day_master_strength.tier

    dayun_label = None
    if resp.dayun and resp.dayun.items:
        now_year = datetime.now().year
        for item in resp.dayun.items:
            sy = item.start_year
            if sy and sy <= now_year:
                dayun_label = f"{item.stem or ''}{item.branch or ''}"
        if not dayun_label and resp.dayun.items:
            first = resp.dayun.items[0]
            dayun_label = f"{first.stem or ''}{first.branch or ''}"

    ziwei_ming = None
    year_branch = pillars.year.branch
    liunian_tag = None
    gz2026 = _liunian_branch(2026)
    ts = _tai_sui_tag(year_branch, gz2026)
    if ts:
        liunian_tag = ts

    try:
        zw_req = case_to_ziwei_request(case, dt)
        zw = build_ziwei_snapshot(zw_req).chart
        ziwei_ming = f"{zw.life_palace_gz}"
        life_p = next((p for p in zw.palaces if p.name == "命宫"), None)
        if life_p and life_p.main_stars:
            stars = "/".join(s["name"] for s in life_p.main_stars[:2])
            ziwei_ming = f"{zw.life_palace_gz}·{stars}"
    except Exception:
        pass

    return ProfileSummaryResponse(
        case_id=case_id,
        pillars_primary=pillars_dict,
        geju_one_liner=geju or None,
        yongshen_favor=favor,
        strength_tier=strength,
        ziwei_ming_one_liner=ziwei_ming,
        current_dayun=dayun_label,
        liunian_2026_tag=liunian_tag,
        disclaimer_block=default_disclaimer_block(),
    )
