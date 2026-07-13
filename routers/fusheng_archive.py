"""Archive bundle: bazi + ziwei snapshot in one call (BE-A05 · T077 name/zeri pointers)."""

from __future__ import annotations

import asyncio
import re
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.dependencies import RequiredUser
from app.models import Case
from db import get_session
from services.bazi_full_service import bazi_full
from services.case_chart_requests import case_to_bazi_request, case_to_ziwei_request
from services.quota_service import enforce_quota
from services.rate_limit import limiter
from services.ziwei_engine import ziwei_full

router = APIRouter(prefix="/api/v1/fusheng", tags=["浮生档案"])

_BRANCHES = frozenset("子丑寅卯辰巳午未申酉戌亥")


class ArchiveBundleRequest(BaseModel):
    case_id: str
    include_ziwei: bool = True
    include_name_pointer: bool = Field(
        False,
        description="T077：附带姓名学扩展指针（不执行 analyze，仅路径+stub）",
    )
    include_zeri_pointer: bool = Field(
        False,
        description="T077：附带择日扩展指针（依赖紫微命宫/五行局 stub）",
    )


class ArchiveExtensionPointer(BaseModel):
    """可选扩展入口：FE 可跳转，不把长结果并入 bundle。"""

    kind: Literal["name", "zeri"]
    path: str
    method: Literal["GET", "POST"]
    ready: bool
    label: str
    params: dict[str, Any] = Field(default_factory=dict)
    note: str | None = None


class ArchiveBundleResponse(BaseModel):
    case_id: str
    bazi: dict
    ziwei: dict | None = None
    missing_fields: list[str] = Field(default_factory=list)
    name: ArchiveExtensionPointer | None = Field(
        None,
        description="T077：include_name_pointer 时返回",
    )
    zeri: ArchiveExtensionPointer | None = Field(
        None,
        description="T077：include_zeri_pointer 时返回",
    )


def _split_chinese_name(full: str) -> tuple[str | None, str | None]:
    """Best-effort 姓/名拆分（单姓为主）；失败返回 (None, None)。"""
    text = re.sub(r"\s+", "", (full or "").strip())
    if not text or not re.fullmatch(r"[\u4e00-\u9fff]{2,4}", text):
        return None, None
    compounds = (
        "欧阳",
        "司马",
        "上官",
        "诸葛",
        "司徒",
        "皇甫",
        "夏侯",
        "尉迟",
        "公孙",
        "慕容",
        "东方",
        "赫连",
        "澹台",
        "闾丘",
        "令狐",
    )
    for c in compounds:
        if text.startswith(c) and len(text) > len(c):
            return c, text[len(c) :]
    if len(text) >= 2:
        return text[0], text[1:]
    return None, None


def _build_name_pointer(case: Case) -> ArchiveExtensionPointer:
    surname, given = _split_chinese_name(case.name or "")
    ready = bool(surname and given)
    params: dict[str, Any] = {}
    if ready:
        params = {"surname": surname, "given_name": given}
    return ArchiveExtensionPointer(
        kind="name",
        path="/api/v1/name/analyze",
        method="POST",
        ready=ready,
        label="姓名学",
        params=params,
        note=None if ready else "档案 name 非标准中文姓名时无法预填；请 POST /api/v1/name/analyze 自行传参",
    )


def _life_palace_branch(ziwei: dict[str, Any] | None) -> str | None:
    if not ziwei:
        return None
    gz = str(ziwei.get("life_palace_gz") or "").strip()
    if gz and gz[-1] in _BRANCHES:
        return gz[-1]
    for palace in ziwei.get("palaces") or []:
        if not isinstance(palace, dict):
            continue
        if palace.get("name") in ("命宫", "命") or palace.get("is_life"):
            branch = str(palace.get("branch") or "").strip()
            if branch in _BRANCHES:
                return branch
            pgz = str(palace.get("ganzhi") or palace.get("gz") or "").strip()
            if pgz and pgz[-1] in _BRANCHES:
                return pgz[-1]
    return None


def _natal_year_branch(bazi: dict[str, Any], ziwei: dict[str, Any] | None) -> str:
    year = (bazi.get("pillars_primary") or {}).get("year") or {}
    if isinstance(year, dict):
        br = str(year.get("branch") or "").strip()
        if br in _BRANCHES:
            return br
    if ziwei:
        br = str(ziwei.get("natal_year_branch") or "").strip()
        if br in _BRANCHES:
            return br
    return ""


def _build_zeri_pointer(
    *,
    bazi: dict[str, Any],
    ziwei: dict[str, Any] | None,
) -> ArchiveExtensionPointer:
    branch = _life_palace_branch(ziwei)
    ju = str((ziwei or {}).get("wuxing_ju_name") or "").strip()
    ready = bool(branch and ju)
    params: dict[str, Any] = {
        "purpose": "general",
        "year": 2026,
        "month": 1,
    }
    if branch:
        params["life_palace_branch"] = branch
    if ju:
        params["wuxing_ju_name"] = ju
    natal = _natal_year_branch(bazi, ziwei)
    if natal:
        params["natal_year_branch"] = natal
    return ArchiveExtensionPointer(
        kind="zeri",
        path="/api/v1/zeri/recommend",
        method="GET",
        ready=ready,
        label="择日",
        params=params,
        note=None if ready else "需先成功计算紫微命宫地支与五行局；可设 include_ziwei=true 后重试",
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
    bazi_req = case_to_bazi_request(case, dt)
    bazi_resp = bazi_full(bazi_req, request_id=f"archive-{payload.case_id}")
    bazi_dict = bazi_resp.model_dump(mode="json")

    ziwei_dict = None
    missing: list[str] = list(bazi_dict.get("missing_fields") or [])
    if payload.include_ziwei:
        try:
            zw_req = case_to_ziwei_request(case, dt)
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

    name_ptr = _build_name_pointer(case) if payload.include_name_pointer else None
    zeri_ptr = _build_zeri_pointer(bazi=bazi_dict, ziwei=ziwei_dict) if payload.include_zeri_pointer else None

    return ArchiveBundleResponse(
        case_id=payload.case_id,
        bazi=bazi_dict,
        ziwei=ziwei_dict,
        missing_fields=sorted(set(missing)),
        name=name_ptr,
        zeri=zeri_ptr,
    )
