#!/usr/bin/env python3
"""T075 · liunian Redis worker — 消费 ``fusheng:liunian:jobs``。

用法::

    set REDIS_URL=redis://localhost:6379
    python scripts/run_liunian_worker.py

环境变量：
  LIUNIAN_REDIS_URL / REDIS_URL — Redis 连接
  LIUNIAN_WORKER_BLPOP_TIMEOUT — BLPOP 秒数（默认 5）
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=os.environ.get("LIUNIAN_WORKER_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [liunian-worker] %(message)s",
)
logger = logging.getLogger("liunian-worker")


async def _process_one(job: dict) -> bool:
    from services.liunian_queue import mark_job_done
    from services.liunian_report_service import build_liunian_report

    task_id = str(job["task_id"])
    case_id = str(job["case_id"])
    year = int(job["year"])
    include_months = bool(job.get("include_months", False))
    started = time.time()
    try:
        await build_liunian_report(task_id, case_id, year, include_months)
        mark_job_done(ok=True)
        logger.info(
            "job_done task_id=%s case_id=%s elapsed_ms=%d",
            task_id,
            case_id,
            int((time.time() - started) * 1000),
        )
        return True
    except Exception:
        mark_job_done(ok=False)
        logger.exception("job_failed task_id=%s case_id=%s", task_id, case_id)
        return False


async def main() -> None:
    from services.liunian_queue import (
        dequeue_liunian_job,
        queue_depth,
        read_metrics,
        redis_queue_enabled,
    )

    if not redis_queue_enabled():
        logger.error("REDIS_URL / LIUNIAN_REDIS_URL not set; worker exiting")
        sys.exit(2)

    timeout = int(os.environ.get("LIUNIAN_WORKER_BLPOP_TIMEOUT", "5"))
    logger.info("liunian worker started blpop_timeout=%s", timeout)
    idle_ticks = 0
    while True:
        job = await asyncio.to_thread(dequeue_liunian_job, timeout_sec=timeout)
        if job is None:
            idle_ticks += 1
            if idle_ticks % 12 == 0:
                depth = queue_depth()
                metrics = read_metrics()
                logger.info("liunian_worker_idle depth=%s metrics=%s", depth, metrics)
            continue
        idle_ticks = 0
        depth = queue_depth()
        logger.info(
            "job_dequeued task_id=%s case_id=%s depth_after=%s",
            job.get("task_id"),
            job.get("case_id"),
            depth,
        )
        await _process_one(job)


if __name__ == "__main__":
    asyncio.run(main())
