"""
tests/test_concurrency.py — O3: 线程安全验证

200 线程并发调用 calculate()，将每个线程的结果与单线程参考值做 Hash 对比。
任何线程数据污染（竞态、跨请求结果混淆）都会导致 Hash 不一致而失败。

设计说明：
  - 使用固定种子集合（4 个不同入参）确保测试可复现
  - 每组入参先单线程预计算参考 Hash
  - 200 线程并发运行，校验每个结果 Hash == 参考 Hash
  - 使用 pytest-timeout 控制最大运行时间（默认 30s）
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from services.bazi_engine_service import calculate

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 测试入参（固定，确保可复现）
# ─────────────────────────────────────────────────────────────────────────────
_TEST_PARAMS = [
    {"dt_str": "1990-07-17T12:20:00", "lon": 116.4, "gender": "female"},
    {"dt_str": "1993-03-06T08:00:00", "lon": 116.4, "gender": "female"},
    {"dt_str": "1985-11-15T06:00:00", "lon": 121.5, "gender": "male"},
    {"dt_str": "1988-03-20T14:00:00", "lon": 120.2, "gender": "male"},
]

_TZ = ZoneInfo("Asia/Shanghai")
_ERRORS: list[str] = []
_ERRORS_LOCK = threading.Lock()


def _pillars_to_str(vr) -> str:
    """将四柱序列化为稳定字符串，用于 hash 比对。"""
    p = vr.pillars_primary
    return "|".join(
        f"{getattr(p, pos).stem}{getattr(p, pos).branch}"
        for pos in ("year", "month", "day", "hour")
    )


def _make_reference_hashes() -> dict[str, str]:
    """单线程预计算各入参的参考 Hash。"""
    refs = {}
    for params in _TEST_PARAMS:
        dt = datetime.fromisoformat(params["dt_str"]).replace(tzinfo=_TZ)
        result = calculate(dt, params["lon"], "Asia/Shanghai", use_solar=False, mode="single", gender=params["gender"])
        pillars_str = _pillars_to_str(result.verify_response)
        key = params["dt_str"]
        refs[key] = hashlib.sha256(pillars_str.encode()).hexdigest()
        logger.debug("参考 Hash [%s]: %s -> %s", key, pillars_str, refs[key][:16])
    return refs


def _worker(params: dict, ref_hash: str, results: list, idx: int) -> None:
    """单个并发工作线程。"""
    try:
        dt = datetime.fromisoformat(params["dt_str"]).replace(tzinfo=_TZ)
        result = calculate(dt, params["lon"], "Asia/Shanghai", use_solar=False, mode="single", gender=params["gender"])
        pillars_str = _pillars_to_str(result.verify_response)
        actual_hash = hashlib.sha256(pillars_str.encode()).hexdigest()
        results[idx] = (True, actual_hash)
        if actual_hash != ref_hash:
            with _ERRORS_LOCK:
                _ERRORS.append(
                    f"线程 {idx}: [{params['dt_str']}] 结果不一致 "
                    f"expect={ref_hash[:16]}... actual={actual_hash[:16]}... "
                    f"pillars={pillars_str}"
                )
    except Exception as exc:
        results[idx] = (False, str(exc))
        with _ERRORS_LOCK:
            _ERRORS.append(f"线程 {idx}: 异常={exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 主测试
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.timeout(30)
def test_concurrent_calculate_thread_safe() -> None:
    """O3: 200 线程并发 calculate()，结果必须与单线程参考 Hash 完全一致。"""
    _ERRORS.clear()

    # 单线程预计算参考
    ref_hashes = _make_reference_hashes()

    # 构造 200 个任务（4 种入参循环）
    n_threads = 200
    task_params = [_TEST_PARAMS[i % len(_TEST_PARAMS)] for i in range(n_threads)]
    results: list[tuple[bool, str] | None] = [None] * n_threads

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {
            executor.submit(
                _worker,
                task_params[i],
                ref_hashes[task_params[i]["dt_str"]],
                results,
                i,
            ): i
            for i in range(n_threads)
        }
        for f in as_completed(futures):
            f.result()  # 重新抛出未捕获异常

    # 统计结果
    success = sum(1 for r in results if r and r[0] and len(_ERRORS) == 0)
    hash_mismatches = [err for err in _ERRORS if "不一致" in err]
    exceptions = [err for err in _ERRORS if "异常" in err]

    assert not exceptions, f"O3 并发测试出现异常:\n" + "\n".join(exceptions[:5])
    assert not hash_mismatches, (
        f"O3 并发测试结果不一致 ({len(hash_mismatches)} 处):\n"
        + "\n".join(hash_mismatches[:5])
    )
    logger.info("O3 并发测试通过：%d 线程全部 Hash 一致", n_threads)
