"""routers/v2/batch.py — 批量排盘端点（N5.03 / R39）.

设计要点：
- POST /api/v2/batch/verify
- 最多 50 条（满足 R39）；ENGINE_V2=false 时返回 501（满足 R40）
- 整体硬上限 60s（time.monotonic + as_completed timeout）
- 单条软超时 5s（future.result timeout）
- BATCH_WORKERS 从环境变量读取，默认 4
- 速率限制 10/min（per user，通过 services/rate_limit.py）
- 超时降级：返回已完成的部分结果 + failed 列表，不返回 502/504
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FuturesTimeoutError
import logging
import os
import time
from time import monotonic as _mono

from fastapi import APIRouter, HTTPException
from starlette.requests import Request

from app.schemas.bazi import BatchVerifyRequest, BatchVerifyResponse
import services.bazi_engine_service as _bazi_engine_service
from services.quota_service import enforce_quota
from services.rate_limit import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

_OVERALL_DEADLINE = 60.0  # 硬上限 60s
_PER_ITEM_TIMEOUT = 5.0  # 单条软超时 5s
_DEFAULT_WORKERS = 4


def _calc_single(item, idx: int) -> dict:
    """在线程池中执行单条排盘，统一返回 model_dump dict。"""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    tz_name = getattr(item, "tz", "Asia/Shanghai")
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError):
        raise ValueError(f"Invalid timezone: {tz_name!r}")

    dt = item.dt
    if dt.tzinfo is None or dt.utcoffset() is None:
        dt = dt.replace(tzinfo=tz)

    lon = getattr(item, "lon", 120.0)

    _t0 = _mono()
    calc = _bazi_engine_service.calculate(
        dt=dt,
        lon=lon,
        tz=tz_name,
        use_solar=getattr(item, "solar_time_enabled", False),
        mode=getattr(item, "mode", "dual"),
        gender=getattr(item, "gender", None),
        request_id=f"batch-{idx}",
        extra_warnings=[],
        city_tier=getattr(item, "city_tier", None),
        industry=getattr(item, "industry", None),
    )
    # R38: 注入实际计算耗时
    calc.verify_response.calc_ms = round((_mono() - _t0) * 1000, 1)
    return calc.verify_response.model_dump(mode="json")


@router.post(
    "/batch/verify",
    summary="批量八字排盘 v2",
    description=(
        "批量排盘端点（N5.03）。\n\n"
        "- 最多 **50 条**请求（满足 R39）\n"
        "- 整体 60s / 单条 5s 超时，超时后返回已完成的部分结果\n"
        "- `ENGINE_V2=false` 时返回 **501**（满足 R40）\n"
        "- 速率限制：**10次/分钟/用户**"
    ),
    response_model=BatchVerifyResponse,
    tags=["v2"],
)
@limiter.limit("10/minute")
def v2_batch_verify(
    request: Request,
    body: BatchVerifyRequest,
) -> BatchVerifyResponse:
    enforce_quota(request, "batch")
    # ── R40: ENGINE_V2 检查 ─────────────────────────────────────────────────
    if not _bazi_engine_service._engine_v2_enabled():
        raise HTTPException(
            status_code=501,
            detail="v2 engine not enabled (set ENGINE_V2=true to activate)",
        )

    items = body.items
    n_workers = int(os.getenv("BATCH_WORKERS", str(_DEFAULT_WORKERS)))

    results: dict[int, dict] = {}
    failed: list[dict] = []

    start = time.monotonic()

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(_calc_single, item, i): i for i, item in enumerate(items)}
        remaining = max(0.0, _OVERALL_DEADLINE - (time.monotonic() - start))

        try:
            for future in as_completed(futures, timeout=remaining):
                i = futures[future]
                try:
                    results[i] = future.result(timeout=_PER_ITEM_TIMEOUT)
                except FuturesTimeoutError:
                    failed.append({"index": i, "error": "per-item timeout (5s)"})
                except Exception as exc:
                    logger.debug("[batch item %d error] %s", i, exc)
                    failed.append({"index": i, "error": str(exc)})
        except FuturesTimeoutError:
            # 整体 60s 到达：将未完成的条目计入 failed
            failed_indices = {f["index"] for f in failed}
            for _f, i in futures.items():
                if i not in results and i not in failed_indices:
                    failed.append({"index": i, "error": "overall timeout (60s)"})

    # 结果按原始 index 顺序重建有序列表
    ordered = [results[i] for i in sorted(results.keys())]
    return BatchVerifyResponse(results=ordered, failed=failed)
