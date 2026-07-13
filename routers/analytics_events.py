"""POST /api/v1/analytics/events — GTM batch product analytics (BE-GTM-01 / T089)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.dependencies import CurrentUser
from app.schemas.analytics_events import (
    AnalyticsEventsBatchRequest,
    AnalyticsEventsBatchResponse,
)
from db import get_session
from services.analytics_events_service import ingest_analytics_events
from services.rate_limit import limiter

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.post(
    "/events",
    response_model=AnalyticsEventsBatchResponse,
    summary="批量产品埋点（卷目阅读 / 术语点击等）",
    description="禁姓名/生日等 PII 键；命中键会被剥离并记入 scrubbed_pii_keys。可匿名或登录。",
)
@limiter.limit("60/minute")
def post_analytics_events(
    request: Request,
    body: AnalyticsEventsBatchRequest,
    user: CurrentUser,
    session: Session = Depends(get_session),
) -> AnalyticsEventsBatchResponse:
    user_id = user.id if user is not None and isinstance(user.id, int) and user.id > 0 else None
    return ingest_analytics_events(session, body.events, user_id=user_id)
