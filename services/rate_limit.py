"""Rate limiting setup."""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Global limiter instance.
# 0.15: default_limits="60/minute" 全局限流
# Per-route limits via @limiter.limit in routers (verify=30/min, bazi/full=20/min).
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
