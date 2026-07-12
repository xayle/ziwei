"""Unified relation compatibility API — POST /api/v1/relation/full."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.dependencies import CurrentUser
from app.models import Case, Snapshot
from app.schemas.relation_compat import RelationFullRequest, RelationFullResponse
from constants import API_VERSION, RULE_VERSION
from db import get_session
from services.relation_engine.case_resolver import resolve_person_input
from services.relation_engine.composer import compute_relation_full

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
    try:
        person_a = resolve_person_input(
            body.person_a.model_dump(),
            user=user,
            session=session,
            default_label="甲方",
        )
        person_b = resolve_person_input(
            body.person_b.model_dump(),
            user=user,
            session=session,
            default_label="乙方",
        )
        result = await asyncio.to_thread(
            compute_relation_full,
            relation_type=body.relation_type,
            person_a=person_a,
            person_b=person_b,
            options=body.options.model_dump(),
            supervisor_id=body.supervisor_id,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"关系合盘计算失败: {exc}") from exc

    case_a_id = person_a.get("case_id")
    case_b_id = person_b.get("case_id")
    if user and session and case_a_id and case_b_id:
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

    return RelationFullResponse(**result)
