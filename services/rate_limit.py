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
#
# 生产环境多进程部署时（uvicorn --workers N）必须改用 Redis 后端，否则每进程各自计数导致实际限流上限被成倍放大：
#
#   开启 Redis 的方式：设置环境变量 REDIS_URL，例如：
#     export REDIS_URL=redis://localhost:6379
#   代码自动检测并切换到 Redis 存储，未设置时回退内存模式（单进程开发相容）。
_redis_url = os.environ.get("REDIS_URL", "")
if _redis_url:
    limiter = Limiter(key_func=_rate_limit_key, default_limits=["60/minute"], storage_uri=_redis_url)
else:
    # 单进程开发模式 / Docker 单实例：内存存储即可
    limiter = Limiter(key_func=_rate_limit_key, default_limits=["60/minute"])
