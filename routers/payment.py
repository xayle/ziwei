"""Payment webhook → entitlement (BE-GTM-06 / T093).

沙箱：不验签；生产接入微信/Stripe 验签前须设 PAYMENT_WEBHOOK_REQUIRE_SIGNATURE=true（预留）。
"""

from __future__ import annotations

from datetime import UTC, datetime
import os
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.schemas.entitlement import EntitlementTier
from db import get_session
from services.payment_entitlement_service import apply_entitlement_from_payment

router = APIRouter(prefix="/api/v1/payment", tags=["支付"])

_SUCCESS_EVENTS = frozenset({"checkout.completed", "subscription.updated", "payment.success"})

PlanLiteral = Literal["free", "volume_pass", "full_book", "pro", "pass", "book"]


class PaymentWebhookPayload(BaseModel):
    provider: Literal["stripe", "wechat"] = "stripe"
    event_type: str = Field(..., description="checkout.completed | subscription.updated | payment.success")
    user_id: int | None = Field(None, description="目标用户 id（沙箱必填以写 entitlement）")
    plan: PlanLiteral = Field(
        "volume_pass",
        description="free | volume_pass | full_book；pro/pass/book 为别名",
    )
    raw: dict[str, Any] = Field(default_factory=dict)


class PaymentWebhookResponse(BaseModel):
    accepted: bool
    plan_applied: str
    entitlement_applied: EntitlementTier | None = None
    user_id: int | None = None
    processed_at: str
    note: str
    sandbox: bool = True


def _sandbox_mode() -> bool:
    """Default sandbox until signature verification is implemented."""
    require_sig = os.environ.get("PAYMENT_WEBHOOK_REQUIRE_SIGNATURE", "").lower() == "true"
    return not require_sig


@router.post(
    "/webhook",
    response_model=PaymentWebhookResponse,
    summary="支付 webhook（沙箱写入 entitlement；验签未实现）",
)
def payment_webhook(
    payload: PaymentWebhookPayload,
    session: Session = Depends(get_session),
) -> PaymentWebhookResponse:
    if payload.event_type not in _SUCCESS_EVENTS:
        raise HTTPException(status_code=400, detail=f"不支持的 event_type: {payload.event_type}")

    sandbox = _sandbox_mode()
    if not sandbox:
        # 预留：真实验签未接好时拒绝，避免误写生产权益
        raise HTTPException(
            status_code=501,
            detail="PAYMENT_WEBHOOK_REQUIRE_SIGNATURE=true 但验签尚未实现；保持沙箱或关闭该开关",
        )

    if payload.user_id is None:
        raise HTTPException(status_code=400, detail="user_id 必填（沙箱回调需指定用户以写 entitlement）")

    try:
        user, applied = apply_entitlement_from_payment(
            session,
            user_id=payload.user_id,
            plan=payload.plan,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return PaymentWebhookResponse(
        accepted=True,
        plan_applied=payload.plan,
        entitlement_applied=applied,
        user_id=user.id,
        processed_at=datetime.now(UTC).isoformat(),
        note=f"sandbox: 已写入 users.entitlement={applied}",
        sandbox=True,
    )
