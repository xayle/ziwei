"""GET /life/volumes — life-volume@1.0 authority draft (R096)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session

from app.dependencies import RequiredUser
from app.models import Case
from app.schemas.life_volume import LifeVolumeResponseModel
from app.schemas.relation_compat import RelationTypeEnum
from db import get_session
from services.life_volume_service import build_life_volumes_for_case
from services.quota_service import enforce_quota
from services.rate_limit import limiter
from services.relation_appendix_service import build_relation_appendix_for_cases

router = APIRouter(prefix="/api/v1/life", tags=["人生六卷"])


@router.get(
    "/volumes/{case_id}",
    response_model=LifeVolumeResponseModel,
    summary="人生六卷+跋（life-volume@1.0 草案）",
)
@limiter.limit("20/minute")
async def get_life_volumes(
    request: Request,
    case_id: str,
    user: RequiredUser,
    session: Session = Depends(get_session),
    partner_case_id: str | None = Query(None, description="T113：挂载合盘附录卷"),
    relation_type: RelationTypeEnum = Query("couple"),
    supervisor_id: str | None = Query(None, description="supervisor_subordinate 时 a|b"),
) -> LifeVolumeResponseModel:
    """
    W16 权威读模型草案：聚合八字/紫微/explain，返回与 `life-volume.schema.json` 对齐的响应。

    打磨期 FE 仍可用 `buildLifeVolumes` Adapter；本端点供契约联调与 U5 起步。
    传 `partner_case_id` 时附加 `relation_appendix`（不进六卷 IA）。
    """
    enforce_quota(request, "structured_text")
    case = session.get(Case, case_id)
    if case is None or case.deleted_at is not None or case.owner_id != user.id:
        raise HTTPException(status_code=404, detail="案例不存在")
    if (
        relation_type == "supervisor_subordinate"
        and partner_case_id
        and supervisor_id
        not in (
            "a",
            "b",
        )
    ):
        raise HTTPException(status_code=422, detail="supervisor_subordinate 需 supervisor_id=a|b")
    response = await build_life_volumes_for_case(case, request_id=f"life-vol-{case_id}")
    if partner_case_id:
        appendix = build_relation_appendix_for_cases(
            session,
            user,
            case_id=case_id,
            partner_case_id=partner_case_id,
            relation_type=relation_type,
            supervisor_id=supervisor_id,
        )
        response = response.model_copy(update={"relation_appendix": appendix})
    return response
