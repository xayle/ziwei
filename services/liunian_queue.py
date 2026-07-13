"""T075 · P3-03 — liunian report Redis 队列（多实例安全）。

默认：无 REDIS_URL / LIUNIAN_REDIS_URL 时回退 asyncio.create_task（单进程开发）。
生产：设置 Redis URL + 运行 ``python scripts/run_liunian_worker.py``。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

LIUNIAN_QUEUE_KEY = os.environ.get("LIUNIAN_REDIS_QUEUE_KEY", "fusheng:liunian:jobs")
LIUNIAN_METRICS_KEY = os.environ.get("LIUNIAN_REDIS_METRICS_KEY", "fusheng:liunian:metrics")


def redis_queue_enabled() -> bool:
    return bool((os.environ.get("LIUNIAN_REDIS_URL") or os.environ.get("REDIS_URL") or "").strip())


def _redis_client():
    url = (os.environ.get("LIUNIAN_REDIS_URL") or os.environ.get("REDIS_URL") or "").strip()
    if not url:
        return None
    try:
        import redis  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("redis package missing; liunian falls back to in-process task")
        return None
    try:
        client = redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        return client
    except Exception:
        logger.exception("liunian Redis unavailable at %s; fallback to in-process", url)
        return None


def enqueue_liunian_job(
    *,
    task_id: str,
    case_id: str,
    year: int,
    include_months: bool,
) -> bool:
    """RPUSH job JSON. Returns True if enqueued to Redis."""
    client = _redis_client()
    if client is None:
        return False
    payload = {
        "task_id": task_id,
        "case_id": case_id,
        "year": int(year),
        "include_months": bool(include_months),
        "enqueued_at": time.time(),
    }
    client.rpush(LIUNIAN_QUEUE_KEY, json.dumps(payload, ensure_ascii=False))
    client.hincrby(LIUNIAN_METRICS_KEY, "enqueued", 1)
    depth = int(client.llen(LIUNIAN_QUEUE_KEY) or 0)
    logger.info(
        "liunian_queue_enqueued task_id=%s case_id=%s depth=%s",
        task_id,
        case_id,
        depth,
    )
    return True


def queue_depth() -> int | None:
    client = _redis_client()
    if client is None:
        return None
    try:
        return int(client.llen(LIUNIAN_QUEUE_KEY) or 0)
    except Exception:
        return None


def read_metrics() -> dict[str, int]:
    client = _redis_client()
    if client is None:
        return {}
    try:
        raw = client.hgetall(LIUNIAN_METRICS_KEY) or {}
        return {str(k): int(v) for k, v in raw.items()}
    except Exception:
        return {}


def dequeue_liunian_job(*, timeout_sec: int = 5) -> dict[str, Any] | None:
    """BLPOP one job. Returns None on timeout / no Redis."""
    client = _redis_client()
    if client is None:
        return None
    item = client.blpop(LIUNIAN_QUEUE_KEY, timeout=max(1, int(timeout_sec)))
    if not item:
        return None
    _key, raw = item
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("liunian poison message (invalid json): %s", raw[:200])
        client.hincrby(LIUNIAN_METRICS_KEY, "poison", 1)
        return None
    if not isinstance(data, dict) or not data.get("task_id"):
        logger.error("liunian poison message (shape): %s", raw[:200])
        client.hincrby(LIUNIAN_METRICS_KEY, "poison", 1)
        return None
    return data


def mark_job_done(*, ok: bool) -> None:
    client = _redis_client()
    if client is None:
        return
    field = "done" if ok else "failed"
    try:
        client.hincrby(LIUNIAN_METRICS_KEY, field, 1)
    except Exception:
        pass


def dispatch_liunian_job(
    *,
    task_id: str,
    case_id: str,
    year: int,
    include_months: bool,
    runner,
) -> str:
    """Enqueue to Redis when available; else asyncio.create_task(runner(...)).

    Returns backend label: ``redis`` | ``asyncio``.
    ``runner`` must be async callable(task_id, case_id, year, include_months).
    """
    if enqueue_liunian_job(
        task_id=task_id,
        case_id=case_id,
        year=year,
        include_months=include_months,
    ):
        return "redis"

    async def _wrap() -> None:
        await runner(task_id, case_id, year, include_months)

    asyncio.create_task(_wrap())
    logger.info("liunian_queue_fallback_asyncio task_id=%s case_id=%s", task_id, case_id)
    return "asyncio"
