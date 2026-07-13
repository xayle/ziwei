"""Freemium quota + GTM entitlement (BE-P2-04 / BE-GTM-05)."""

from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import HTTPException, Request

from app.schemas.entitlement import (
    VOLUME_MIN_ENTITLEMENT,
    EntitlementInfo,
    EntitlementTier,
)
from app.schemas.life_volume import LifeVolumeId

QuotaTier = Literal["anonymous", "free", "pro"]
QuotaEndpoint = Literal["batch", "llm", "export", "structured_text", "similarity"]

# per-minute limits by tier × endpoint
_LIMITS: dict[QuotaTier, dict[QuotaEndpoint, int]] = {
    "anonymous": {"batch": 0, "llm": 0, "export": 5, "structured_text": 5, "similarity": 3},
    "free": {"batch": 10, "llm": 10, "export": 20, "structured_text": 30, "similarity": 10},
    "pro": {"batch": 50, "llm": 60, "export": 100, "structured_text": 120, "similarity": 40},
}

_ENTITLEMENT_RANK: dict[EntitlementTier, int] = {
    "free": 0,
    "volume_pass": 1,
    "full_book": 2,
}

_VALID_ENTITLEMENTS = frozenset(_ENTITLEMENT_RANK)

_COUNTERS: dict[str, int] = {}


def resolve_quota_tier(request: Request) -> QuotaTier:
    if os.environ.get("AUTH_BYPASS", "").lower() == "true":
        return "pro"
    user = getattr(request.state, "user", None)
    if user is None:
        return "anonymous"
    if getattr(user, "is_admin", False) or getattr(user, "role", "") in {"owner", "admin", "pro"}:
        return "pro"
    return "free"


def quota_limit_for(request: Request, endpoint: QuotaEndpoint) -> int:
    tier = resolve_quota_tier(request)
    return _LIMITS[tier][endpoint]


def _counter_key(request: Request, endpoint: QuotaEndpoint) -> str:
    tier = resolve_quota_tier(request)
    user = getattr(request.state, "user", None)
    if user is not None and getattr(user, "id", None):
        return f"{tier}:user:{user.id}:{endpoint}"
    from slowapi.util import get_remote_address

    return f"{tier}:ip:{get_remote_address(request)}:{endpoint}"


def enforce_quota(request: Request, endpoint: QuotaEndpoint) -> None:
    """Raise 429 when per-minute quota exceeded (in-memory; Redis optional later)."""
    limit = quota_limit_for(request, endpoint)
    if limit <= 0:
        raise HTTPException(status_code=401, detail=f"端点 {endpoint} 需要登录")
    key = _counter_key(request, endpoint)
    count = _COUNTERS.get(key, 0) + 1
    _COUNTERS[key] = count
    if count > limit:
        raise HTTPException(
            status_code=429,
            detail=f"配额已用尽：{endpoint} 每分钟最多 {limit} 次（tier={resolve_quota_tier(request)}）",
        )


def reset_quota_counters() -> None:
    """Test helper."""
    _COUNTERS.clear()


def _normalize_entitlement(raw: Any) -> EntitlementTier | None:
    if raw is None:
        return None
    value = str(raw).strip().lower()
    if value in _VALID_ENTITLEMENTS:
        return value  # type: ignore[return-value]
    return None


def resolve_entitlement(*, request: Request | None = None, user: Any = None) -> EntitlementTier:
    """Resolve GTM entitlement: free | volume_pass | full_book.

    Priority: AUTH_BYPASS → admin/owner/pro role → user.entitlement → free.
    """
    if os.environ.get("AUTH_BYPASS", "").lower() == "true":
        return "full_book"

    resolved_user = user
    if resolved_user is None and request is not None:
        resolved_user = getattr(request.state, "user", None)

    if resolved_user is None:
        return "free"

    if getattr(resolved_user, "is_admin", False) or getattr(resolved_user, "role", "") in {
        "owner",
        "admin",
        "pro",
    }:
        return "full_book"

    stored = _normalize_entitlement(getattr(resolved_user, "entitlement", None))
    return stored or "free"


def entitlement_satisfies(actual: EntitlementTier, required: EntitlementTier) -> bool:
    return _ENTITLEMENT_RANK[actual] >= _ENTITLEMENT_RANK[required]


def is_volume_unlocked(tier: EntitlementTier, volume_id: LifeVolumeId | str) -> bool:
    """Q2 unlock map — used by T087 locked rules / middleware checks."""
    required = VOLUME_MIN_ENTITLEMENT.get(volume_id)  # type: ignore[arg-type]
    if required is None:
        return False
    return entitlement_satisfies(tier, required)


def unlocked_volume_ids(tier: EntitlementTier) -> list[LifeVolumeId]:
    return [vid for vid, need in VOLUME_MIN_ENTITLEMENT.items() if entitlement_satisfies(tier, need)]


def build_entitlement_info(*, request: Request | None = None, user: Any = None) -> EntitlementInfo:
    tier = resolve_entitlement(request=request, user=user)
    return EntitlementInfo(tier=tier, unlocked_volume_ids=unlocked_volume_ids(tier))


def enforce_entitlement(
    request: Request,
    required: EntitlementTier,
    *,
    user: Any = None,
) -> EntitlementTier:
    """Middleware-style gate: raise 403 when entitlement below required tier."""
    if user is not None:
        request.state.user = user
    actual = resolve_entitlement(request=request, user=user)
    if not entitlement_satisfies(actual, required):
        raise HTTPException(
            status_code=403,
            detail=f"权益不足：需要 {required}，当前为 {actual}",
        )
    return actual


def require_entitlement_dependency(required: EntitlementTier):
    """FastAPI Depends factory — 中间件风格校验（T086）。

    用法::

        @router.get("/premium")
        def premium(request: Request, _: EntitlementTier = require_entitlement_dependency("volume_pass")):
            ...
    """
    from fastapi import Depends

    from app.dependencies.auth import require_user
    from app.models import User

    def _check(request: Request, user: User = Depends(require_user)) -> EntitlementTier:
        return enforce_entitlement(request, required, user=user)

    return Depends(_check)
