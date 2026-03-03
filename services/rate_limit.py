"""Rate limiting setup."""
import os
import uuid

from slowapi import Limiter
from slowapi.util import get_remote_address


def _rate_limit_key(request):
    """Key function for rate limiting.

    Priority:
      1. AUTH_BYPASS=true (dev/test) → unique UUID → 关闭限制
      2. 已认证用户 (request.state.user) → 按 user_id 限速
      3. 未认证 → 按 remote IP 限速
    """
    if os.environ.get("AUTH_BYPASS", "").lower() == "true":
        return str(uuid.uuid4())  # unique per-request → never grouped → no limit

    # 已认证用户：使用 user_id 作为限限 key（防止同一用户多 IP 绕过限制）
    user = getattr(request.state, "user", None)
    if user is not None:
        user_id = getattr(user, "id", None) or getattr(user, "user_id", None)
        if user_id:
            return f"user:{user_id}"

    return get_remote_address(request)


# Global limiter instance.
# Per-route limits via @limiter.limit in routers (verify=30/min, bazi/full=20/min).
limiter = Limiter(key_func=_rate_limit_key, default_limits=["60/minute"])
