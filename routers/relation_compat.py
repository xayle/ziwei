"""Unified relation compatibility API — POST /api/v1/relation/full."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlmodel import Session

from app.dependencies import CurrentUser, RequiredUser
from app.models import Case, Snapshot
from app.schemas.explain import RelationExplainBatchRequest
from app.schemas.life_volume import RelationAppendixResponse
from app.schemas.relation_compat import (
    RelationFullRequest,
    RelationFullResponse,
    RelationSnapshotDetail,
    RelationSnapshotSummary,
    RelationTypeEnum,
)
from constants import API_VERSION, RULE_VERSION
from db import get_session
from services.explain_service import explain_relation_batch
from services.pdf_exporter import generate_relation_share_card, render_html_to_pdf
from services.relation_appendix_service import build_relation_appendix_for_cases
from services.relation_compat_flow import compute_relation_full_with_persons
from services.relation_pdf_service import render_relation_compat_html
from services.relation_snapshot_service import get_relation_snapshot_detail, list_relation_snapshots

router = APIRouter(prefix="/api/v1/relation", tags=["relation"])


def _store_relation_snapshot(
    session: Session,
    case: Case,
    relation_type: str,
    output: dict[str, Any],
    *,
    case_a_id: str,
    case_b_id: str,
) -> str:
    snap = Snapshot(
        case_id=case.id,
        kind="relation_v1",
        compute_flags={
            "relation_type": relation_type,
            "case_a_id": case_a_id,
            "case_b_id": case_b_id,
            "schema_version": "relation-compat@1.0",
        },
        input_json={"case_a_id": case_a_id, "case_b_id": case_b_id},
        output_json=output,
        api_version=API_VERSION,
        rule_version=RULE_VERSION,
    )
    session.add(snap)
    session.commit()
    session.refresh(snap)
    case.last_snapshot_at = datetime.now(UTC)
    case.updated_at = datetime.now(UTC)
    session.add(case)
    session.commit()
    return str(snap.id)


def _maybe_store_snapshots(
    body: RelationFullRequest,
    result: dict[str, Any],
    user: CurrentUser,
    session: Session,
    person_a: dict[str, Any],
    person_b: dict[str, Any],
) -> None:
    case_a_id = person_a.get("case_id")
    case_b_id = person_b.get("case_id")
    if not (user and session and case_a_id and case_b_id):
        return
    snap_ids: list[str] = []
    for cid in (case_a_id, case_b_id):
        case = session.get(Case, cid)
        if case and (case.owner_id is None or case.owner_id == user.id):
            snap_ids.append(
                _store_relation_snapshot(
                    session,
                    case,
                    body.relation_type,
                    result,
                    case_a_id=case_a_id,
                    case_b_id=case_b_id,
                )
            )
    if snap_ids:
        result.setdefault("meta", {})["snapshots_created"] = snap_ids


def _safe_pdf_filename(label_a: str, label_b: str) -> str:
    raw = f"合盘-{label_a}-{label_b}.pdf"
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in raw)


def _safe_png_filename(label_a: str, label_b: str) -> str:
    raw = f"合盘-{label_a}-{label_b}.png"
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in raw)


@router.post(
    "/full",
    response_model=RelationFullResponse,
    summary="双人关系合盘（6 类关系 · 八字+紫微）",
)
async def post_relation_full(
    body: RelationFullRequest,
    user: CurrentUser,
    session: Session = Depends(get_session),
) -> RelationFullResponse:
    """
    权威合盘端点。按 `relation_type` 切换评分维度与宫位对。
    `person_*.case_id` 需登录；否则传 `birth_datetime`。
    """
    result, person_a, person_b = await compute_relation_full_with_persons(body, user=user, session=session)
    _maybe_store_snapshots(body, result, user, session, person_a, person_b)
    return RelationFullResponse(**result)


@router.get(
    "/appendix",
    response_model=RelationAppendixResponse,
    summary="合盘附录卷（T113 · 不进六卷 IA）",
)
async def get_relation_appendix(
    user: RequiredUser,
    session: Session = Depends(get_session),
    case_id: str = Query(..., description="主档案 case UUID"),
    partner_case_id: str = Query(..., description="对方档案 case UUID"),
    relation_type: RelationTypeEnum = Query("couple"),
    supervisor_id: str | None = Query(None, description="supervisor_subordinate 时 a 或 b"),
) -> RelationAppendixResponse:
    """T113：返回 relation-appendix@1.0，供报告页可选挂载（默认折叠）。"""
    if relation_type == "supervisor_subordinate" and supervisor_id not in ("a", "b"):
        raise HTTPException(422, "supervisor_subordinate 需 supervisor_id=a|b")
    return build_relation_appendix_for_cases(
        session,
        user,
        case_id=case_id,
        partner_case_id=partner_case_id,
        relation_type=relation_type,
        supervisor_id=supervisor_id,
    )


@router.get(
    "/snapshots",
    response_model=list[RelationSnapshotSummary],
    summary="合盘快照列表（kind=relation_v1 · BE-R16）",
)
def get_relation_snapshots(
    user: RequiredUser,
    session: Session = Depends(get_session),
    case_id: str = Query(..., description="档案 case UUID"),
    partner_case_id: str | None = Query(None, description="可选：筛选特定对方"),
    limit: int = Query(20, ge=1, le=100),
) -> list[RelationSnapshotSummary]:
    """列出某档案下的关系合盘快照（含双方 case_id 模式 /full 写入）。"""
    return list_relation_snapshots(
        session,
        user,
        case_id=case_id,
        partner_case_id=partner_case_id,
        limit=limit,
    )


@router.get(
    "/snapshots/{snapshot_id}",
    response_model=RelationSnapshotDetail,
    summary="合盘快照详情（恢复 relation-compat@1.0）",
)
def get_relation_snapshot(
    snapshot_id: str,
    user: RequiredUser,
    session: Session = Depends(get_session),
) -> RelationSnapshotDetail:
    """BE-R16：从 snapshot output_json 恢复完整合盘响应。"""
    return get_relation_snapshot_detail(session, user, snapshot_id)


@router.post(
    "/explain/batch",
    summary="关系合盘讲解 batch（relation_reading · cite 层）",
)
async def post_relation_explain_batch(
    body: RelationExplainBatchRequest,
    user: CurrentUser,
    session: Session = Depends(get_session),
):
    """BE-R15：一次请求 1–4 个 section；当前支持 `relation_reading`。"""
    return explain_relation_batch(body, user=user, session=session)


@router.post(
    "/export/pdf",
    summary="关系合盘 PDF 导出（relation-compat@1.0 · 与 /full 同口径）",
    response_class=Response,
)
async def export_relation_pdf(
    body: RelationFullRequest,
    user: CurrentUser,
    session: Session = Depends(get_session),
) -> Response:
    """R086 P0：正式 PDF 管线 — 与 UI 相同 API 响应渲染 HTML → PDF。"""
    result, person_a, person_b = await compute_relation_full_with_persons(body, user=user, session=session)
    _maybe_store_snapshots(body, result, user, session, person_a, person_b)

    html = render_relation_compat_html(result)
    try:
        pdf_bytes = await render_html_to_pdf(html)
    except Exception as exc:
        raise HTTPException(500, f"PDF 渲染失败: {exc}") from exc

    label_a = (result.get("person_a") or {}).get("label") or "甲方"
    label_b = (result.get("person_b") or {}).get("label") or "乙方"
    filename = _safe_pdf_filename(str(label_a), str(label_b))
    encoded = quote(filename)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )


@router.post(
    "/export/png",
    summary="关系合盘分享卡片 PNG（relation-compat@1.0 · 与 /full 同口径）",
    response_class=Response,
)
async def export_relation_png(
    body: RelationFullRequest,
    user: CurrentUser,
    session: Session = Depends(get_session),
) -> Response:
    """R086 P2：合盘分享卡 — 与 PDF 相同计算口径，输出 400×280 PNG。"""
    result, person_a, person_b = await compute_relation_full_with_persons(body, user=user, session=session)
    _maybe_store_snapshots(body, result, user, session, person_a, person_b)

    try:
        png_bytes = await generate_relation_share_card(result)
    except Exception as exc:
        raise HTTPException(500, f"PNG 渲染失败: {exc}") from exc

    label_a = (result.get("person_a") or {}).get("label") or "甲方"
    label_b = (result.get("person_b") or {}).get("label") or "乙方"
    filename = _safe_png_filename(str(label_a), str(label_b))
    encoded = quote(filename)
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )
