"""GET /life/volumes — life-volume@1.0 authority draft (R096)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session

from app.dependencies import RequiredUser
from app.exceptions import AuthenticationException
from app.models import Case
from app.schemas.life_snippets import LifeSnippetsResponseModel
from app.schemas.life_volume import LifeVolumeResponseModel
from app.schemas.relation_compat import RelationTypeEnum
from db import get_session
from services.auth_service import verify_h5_preview_token
from services.life_snippets_service import build_life_snippets_for_case
from services.life_volume_service import build_life_volumes_for_case, project_h5_vol1_preview
from services.quota_service import enforce_quota, resolve_entitlement
from services.rate_limit import limiter
from services.relation_appendix_service import build_relation_appendix_for_cases

router = APIRouter(prefix="/api/v1/life", tags=["人生六卷"])


@router.get(
    "/preview/{case_id}",
    response_model=LifeVolumeResponseModel,
    summary="H5 试读：免登录卷一摘要（短 token）",
)
@limiter.limit("30/minute")
async def get_life_vol1_preview(
    request: Request,
    case_id: str,
    session: Session = Depends(get_session),
    token: str | None = Query(None, description="H5 试读短 token（亦可 Authorization: Bearer）"),
) -> LifeVolumeResponseModel:
    """
    T095 / BE-GTM-07：落地页携带短 token，无需登录即可读卷首+卷一摘要。

    Token 由 `POST /auth/h5-preview-token` 签发，绑定 case_id，不可当登录 access。
    """
    raw = token
    if not raw:
        auth_header = request.headers.get("Authorization") or ""
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            raw = parts[1]
    if not raw:
        raise HTTPException(status_code=401, detail="缺少 H5 试读 token")
    try:
        claims = verify_h5_preview_token(raw)
    except AuthenticationException as exc:
        raise HTTPException(status_code=401, detail=exc.message) from exc
    if claims.case_id != case_id:
        raise HTTPException(status_code=403, detail="token 与案例不匹配")

    case = session.get(Case, case_id)
    if case is None or case.deleted_at is not None:
        raise HTTPException(status_code=404, detail="案例不存在")
    # 试读不计入完整 structured_text 配额；轻量读模型即可
    full = await build_life_volumes_for_case(
        case,
        request_id=f"life-preview-{case_id}",
        entitlement="free",
    )
    return project_h5_vol1_preview(full)


@router.get(
    "/snippets/{case_id}",
    response_model=LifeSnippetsResponseModel,
    summary="人生钩子句 snippets（BOOK-GTM §5.3 草案）",
)
@limiter.limit("30/minute")
async def get_life_snippets(
    request: Request,
    case_id: str,
    user: RequiredUser,
    session: Session = Depends(get_session),
    limit: int = Query(5, ge=3, le=5, description="返回钩子条数 3–5"),
) -> LifeSnippetsResponseModel:
    """
    T076 / P3-02：抖音竖屏用短句（3–5 条），优先 engine 事实 + 至多一条典籍。
    形状对齐 BOOK-GTM §5.3；叙事长文仍走 explain / life/volumes。
    """
    enforce_quota(request, "structured_text")
    case = session.get(Case, case_id)
    if case is None or case.deleted_at is not None or case.owner_id != user.id:
        raise HTTPException(status_code=404, detail="案例不存在")
    return build_life_snippets_for_case(
        case,
        limit=limit,
        request_id=f"life-snip-{case_id}",
    )


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
    response = await build_life_volumes_for_case(
        case,
        request_id=f"life-vol-{case_id}",
        entitlement=resolve_entitlement(user=user),
    )
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
