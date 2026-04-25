"""
C2: Sandbox 模式服务层中间件

当 settings.sandbox_enabled=True 且请求头携带 X-Sandbox: true 时，
拦截 /api/v1/verify 和 /api/v1/bazi/* 请求，返回预设的黄金案例响应，
并在响应头中添加 X-LLM-Fallback: sandbox。

配置：
  环境变量 SANDBOX_ENABLED=true 启用 sandbox 模式
  请求头 X-Sandbox: true 触发沙箱拦截

用途：
  - 前端开发时使用固定样本数据，不依赖后端计算
  - CI 测试中使用确定性响应
  - 演示环境隔离真实计算

注意：
  此中间件仅在 settings.sandbox_enabled=True 时生效；
  生产环境默认 SANDBOX_ENABLED=false。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from functools import lru_cache

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# 触发沙箱拦截的路径前缀
_SANDBOX_PATH_PREFIXES = (
    "/api/v1/verify",
    "/api/v1/bazi/",
)


@lru_cache(maxsize=1)
def _load_sandbox_sample() -> dict:
    """加载黄金案例中第一条作为沙箱固定响应样本"""
    path = _DATA_DIR / "ground_truth_cases.json"
    if not path.exists():
        logger.warning("[Sandbox] ground_truth_cases.json not found, using empty sample")
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        cases = raw.get("cases", [])
        if cases:
            sample = cases[0]
            logger.info("[Sandbox] Loaded sandbox sample: %s", sample.get("id"))
            return sample
    except Exception as exc:
        logger.error("[Sandbox] Failed to load sandbox sample: %s", exc)
    return {}


class SandboxMiddleware(BaseHTTPMiddleware):
    """
    C2: Sandbox 模式中间件。
    当 settings.sandbox_enabled=True 且请求头 X-Sandbox: true 时，
    对 /api/v1/verify 和 /api/v1/bazi/* 路径返回固定的沙箱响应。
    """

    def __init__(self, app, sandbox_enabled: bool = False):
        super().__init__(app)
        self._sandbox_enabled = sandbox_enabled

    async def dispatch(self, request: Request, call_next) -> Response:
        # 仅在 sandbox_enabled=True 时检查请求头
        if not self._sandbox_enabled:
            return await call_next(request)

        path = request.url.path
        x_sandbox = request.headers.get("X-Sandbox", "").lower()

        if x_sandbox == "true" and any(path.startswith(p) for p in _SANDBOX_PATH_PREFIXES):
            sample = _load_sandbox_sample()
            logger.info("[Sandbox] Intercepted %s %s → returning fixed sample", request.method, path)
            resp_body = {
                "sandbox": True,
                "note": "沙箱模式：返回固定黄金案例样本，非真实计算结果",
                "sample_id": sample.get("id", "unknown"),
                "data": sample,
            }
            return JSONResponse(
                content=resp_body,
                status_code=200,
                headers={
                    "X-LLM-Fallback": "sandbox",
                    "X-Sandbox-Mode": "true",
                },
            )

        return await call_next(request)
