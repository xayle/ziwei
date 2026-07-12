"""Notification subscription stub (BE-P3-07)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import RequiredUser

router = APIRouter(prefix="/api/v1/notifications", tags=["通知"])


class NotificationSubscribeRequest(BaseModel):
    channel: Literal["email", "webpush"] = "email"
    event_type: Literal["dayun_transition", "liunian_digest"] = "dayun_transition"
    case_id: str | None = None


class NotificationSubscriptionResponse(BaseModel):
    subscription_id: str
    channel: str
    event_type: str
    case_id: str | None
    status: str = "stub_active"
    created_at: str


@router.post(
    "/subscribe",
    response_model=NotificationSubscriptionResponse,
    summary="订阅通知（stub：记录订阅意图，不发真实推送）",
    status_code=201,
)
def subscribe_notifications(
    payload: NotificationSubscribeRequest,
    _user: RequiredUser,
) -> NotificationSubscriptionResponse:
    return NotificationSubscriptionResponse(
        subscription_id=str(uuid4()),
        channel=payload.channel,
        event_type=payload.event_type,
        case_id=payload.case_id,
        status="stub_active",
        created_at=datetime.now(UTC).isoformat(),
    )


@router.get("/health", summary="通知模块健康检查")
def notifications_health() -> dict:
    return {"status": "stub", "delivery": "mock", "channels": ["email", "webpush"]}
