"""Shared relation full compute for API + PDF export."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session

from app.dependencies import CurrentUser
from app.schemas.relation_compat import RelationFullRequest
from services.relation_engine.case_resolver import resolve_person_input
from services.relation_engine.composer import compute_relation_full


async def compute_relation_full_with_persons(
    body: RelationFullRequest,
    *,
    user: CurrentUser,
    session: Session | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Resolve persons once, compute relation full, return (result, person_a, person_b)."""
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
        return result, person_a, person_b
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"关系合盘计算失败: {exc}") from exc


async def compute_relation_full_from_request(
    body: RelationFullRequest,
    *,
    user: CurrentUser,
    session: Session | None,
) -> dict[str, Any]:
    result, _, _ = await compute_relation_full_with_persons(body, user=user, session=session)
    return result
