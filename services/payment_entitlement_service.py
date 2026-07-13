"""Map payment plans → User.entitlement (BE-GTM-06 / T093)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session

from app.models import User
from app.schemas.entitlement import EntitlementTier

# Stripe/wechat plan aliases → entitlement tier
_PLAN_TO_ENTITLEMENT: dict[str, EntitlementTier] = {
    "free": "free",
    "volume_pass": "volume_pass",
    "pass": "volume_pass",
    "full_book": "full_book",
    "pro": "full_book",
    "book": "full_book",
}


def plan_to_entitlement(plan: str) -> EntitlementTier:
    key = (plan or "").strip().lower()
    if key not in _PLAN_TO_ENTITLEMENT:
        raise ValueError(f"不支持的 plan: {plan}")
    return _PLAN_TO_ENTITLEMENT[key]


def apply_entitlement_from_payment(
    session: Session,
    *,
    user_id: int,
    plan: str,
) -> tuple[User, EntitlementTier]:
    """Persist entitlement on user; raise LookupError if user missing."""
    tier = plan_to_entitlement(plan)
    user = session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise LookupError(f"user_id={user_id} not found")
    user.entitlement = tier
    user.updated_at = datetime.now(UTC)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user, tier
