"""Payment webhook stub for Freemium (BE-P4-01 / BE-I05)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/payment", tags=["支付"])


class PaymentWebhookPayload(BaseModel):
    provider: Literal["stripe", "wechat"] = "stripe"
    event_type: str = Field(..., description="checkout.completed | subscription.updated 等")
    user_id: int | None = None
    plan: Literal["free", "pro"] = "pro"
    raw: dict[str, Any] = Field(default_factory=dict)


class PaymentWebhookResponse(BaseModel):
    accepted: bool
    plan_applied: str
    processed_at: str
    note: str


@router.post(
    "/webhook",
    response_model=PaymentWebhookResponse,
    summary="支付 webhook stub（验签未实现，仅记录事件）",
)
def payment_webhook(payload: PaymentWebhookPayload) -> PaymentWebhookResponse:
    if payload.event_type not in {"checkout.completed", "subscription.updated", "payment.success"}:
        raise HTTPException(status_code=400, detail=f"不支持的 event_type: {payload.event_type}")
    return PaymentWebhookResponse(
        accepted=True,
        plan_applied=payload.plan,
        processed_at=datetime.now(UTC).isoformat(),
        note="stub: 未写入用户权益表；请配合 quota tier 配置使用",
    )
