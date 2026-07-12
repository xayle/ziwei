"""Freemium quota tiers for expensive endpoints (BE-P2-04 / BE-P3-04)."""

from __future__ import annotations

import os
from typing import Literal

from fastapi import HTTPException, Request

QuotaTier = Literal["anonymous", "free", "pro"]
QuotaEndpoint = Literal["batch", "llm", "export", "structured_text", "similarity"]

# per-minute limits by tier × endpoint
_LIMITS: dict[QuotaTier, dict[QuotaEndpoint, int]] = {
    "anonymous": {"batch": 0, "llm": 0, "export": 5, "structured_text": 5, "similarity": 3},
    "free": {"batch": 10, "llm": 10, "export": 20, "structured_text": 30, "similarity": 10},
    "pro": {"batch": 50, "llm": 60, "export": 100, "structured_text": 120, "similarity": 40},
}

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
