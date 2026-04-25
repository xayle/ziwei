"""
W8 SLO 基线中间件
─────────────────
对每个 API 端点维护一个简单的滑动窗口延迟样本（最近 100 次请求），
计算近似 p95 延迟；超过 SLO_WARN_MS / SLO_CRIT_MS 阈值时输出结构化日志告警。

设计原则：
  - 纯内存，进程内统计；不依赖外部存储，不影响请求延迟
  - 线程安全：使用 collections.deque（固定长度）+ 原生 append（GIL 保护）
  - 仅对 /api/v1/ 路径统计，跳过 /metrics /health /docs 等辅助路径
"""
from __future__ import annotations

import collections
import logging
import statistics
import time
from typing import Callable, Deque, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from constants import SLO_WARN_MS, SLO_CRIT_MS

logger = logging.getLogger(__name__)

# 每个端点保留最近 N 个样本
_WINDOW_SIZE = 100

# 端点延迟样本桶：path → deque of milliseconds
_latency_buckets: Dict[str, Deque[float]] = collections.defaultdict(
    lambda: collections.deque(maxlen=_WINDOW_SIZE)
)


def get_endpoint_p95(path: str) -> float | None:
    """返回指定端点的近似 p95 延迟（ms），样本不足 20 条时返回 None。"""
    samples = list(_latency_buckets.get(path, []))
    if len(samples) < 20:
        return None
    samples.sort()
    idx = int(len(samples) * 0.95)
    return samples[min(idx, len(samples) - 1)]


def get_all_slo_stats() -> Dict[str, float]:
    """返回所有端点的当前 p95 延迟（ms），供 /health/detail 调用。"""
    result: Dict[str, float] = {}
    for path, bucket in _latency_buckets.items():
        p95 = get_endpoint_p95(path)
        if p95 is not None:
            result[path] = round(p95, 1)
    return result


class SLOMiddleware(BaseHTTPMiddleware):
    """W8 SLO 基线中间件：记录延迟样本并在 p95 超阈值时告警。"""

    _SKIP_PREFIXES = ("/metrics", "/health", "/docs", "/redoc", "/openapi.json", "/static")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # 跳过辅助路径
        if any(path.startswith(p) for p in self._SKIP_PREFIXES):
            return await call_next(request)

        # 只统计 /api/v1/ 路径
        if not path.startswith("/api/v1/"):
            return await call_next(request)

        t0 = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # 规范化路径（将 UUID / 数字路径段替换为 {id}，避免桶爆炸）
        norm_path = _normalize_path(path)
        _latency_buckets[norm_path].append(elapsed_ms)

        # 计算当前 p95 并告警
        p95 = get_endpoint_p95(norm_path)
        if p95 is not None:
            if p95 >= SLO_CRIT_MS:
                logger.critical(
                    "SLO CRITICAL: p95 latency %.0f ms on %s (threshold=%d ms)",
                    p95, norm_path, SLO_CRIT_MS,
                    extra={"slo_path": norm_path, "p95_ms": p95, "slo_level": "critical"},
                )
            elif p95 >= SLO_WARN_MS:
                logger.warning(
                    "SLO WARNING: p95 latency %.0f ms on %s (threshold=%d ms)",
                    p95, norm_path, SLO_WARN_MS,
                    extra={"slo_path": norm_path, "p95_ms": p95, "slo_level": "warning"},
                )

        return response


def _normalize_path(path: str) -> str:
    """将路径中的动态段（UUID/整数）替换为 {id}，减少桶数量。"""
    import re
    # UUID
    path = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "{id}", path)
    # 纯数字段
    path = re.sub(r"/\d+(/|$)", r"/{id}\1", path)
    return path
