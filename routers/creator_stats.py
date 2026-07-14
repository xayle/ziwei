"""GET /api/v1/creator/stats — GTM 创作者统计（BE-GTM-08 / T099）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from app.dependencies import RequiredUser
from app.models import User
from app.schemas.creator_stats import CreatorStatsResponse
from db import get_session
from services.creator_stats_service import build_creator_stats
from services.rate_limit import limiter

router = APIRouter(prefix="/api/v1/creator", tags=["创作者统计"])


def _require_admin(user: User) -> User:
    if not getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可访问创作者统计",
        )
    return user


@router.get(
    "/stats",
    response_model=CreatorStatsResponse,
    summary="创作者统计：topic→注册 cohort + 漏斗",
    description="按 utm_source / utm_campaign / content_id 聚合注册与付费转化；仅管理员。",
)
@limiter.limit("30/minute")
def get_creator_stats(
    request: Request,
    user: RequiredUser,
    session: Session = Depends(get_session),
    window_days: int = Query(30, ge=1, le=365, description="统计窗口（天）"),
) -> CreatorStatsResponse:
    _require_admin(user)
    return build_creator_stats(session, window_days=window_days)
