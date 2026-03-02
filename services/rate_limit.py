"""Rate limiting setup."""
import os
import uuid

from slowapi import Limiter
from slowapi.util import get_remote_address


def _rate_limit_key(request):
    """Key function for rate limiting.

    In AUTH_BYPASS=true (test/dev) mode each request gets a unique UUID key,
    which means every request lands in its own bucket — effectively disabling
    rate limiting without changing the limiter configuration.
    In production each request is keyed by remote IP address as usual.
    """
    if os.environ.get("AUTH_BYPASS", "").lower() == "true":
        return str(uuid.uuid4())  # unique per-request → never grouped → no limit
    return get_remote_address(request)


# Global limiter instance.
# 0.15: default_limits="60/minute" 全局限流
# Per-route limits via @limiter.limit in routers (verify=30/min, bazi/full=20/min).
limiter = Limiter(key_func=_rate_limit_key, default_limits=["60/minute"])
