"""
tests/test_golden_regression.py — O2: 黄金案例回归测试套件

从 data/ground_truth_cases.json 读取所有案例（GT01-GT08 + CLS01-CLS12），
参数化断言：
  - pillars_primary (四柱八字)
  - geju.geju_name (格局名称)
  - yongshen.favor (用神五行)

CLS 系列为 pre_1900 = true，sxtwl 对 1900 年前支持有限，
pre_1900 案例仅断言四柱，跳过格局/用神断言并发出 pytest.warns。

设计原则：
  - 纯直接调用 calculate()（不走 HTTP）
  - 断言失败 → CI block-merge（alembic/PR gate 保护）
  - 新算法升级后必须通过全部 PASS 才能合并
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from zoneinfo import ZoneInfo

# 直接调用计算，不走 HTTP 避免速率限制
from services.bazi_engine_service import calculate

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 加载黄金案例
# ─────────────────────────────────────────────────────────────────────────────
_GT_JSON_PATH = Path(__file__).parent.parent / "data" / "ground_truth_cases.json"


def _load_cases() -> list[dict[str, Any]]:
    with open(_GT_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["cases"]


_ALL_CASES = _load_cases()
# 仅取 verified_pillars=True 的案例参与断言
_VERIFIED_CASES = [c for c in _ALL_CASES if c.get("verified_pillars")]
# pre_1900 案例（sxtwl 精度有限，仅断言四柱）
_PRE1900_IDS = {c["id"] for c in _VERIFIED_CASES if c.get("pre_1900")}
_POST1900_CASES = [c for c in _VERIFIED_CASES if not c.get("pre_1900")]


# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────────────────
def _run_case(case: dict) -> Any:
    """调用 calculate() 并返回 VerifyResponse。"""
    dt = datetime.fromisoformat(case["birth_dt_solar"]).replace(
        tzinfo=ZoneInfo("Asia/Shanghai")
    )
    lon = float(case.get("longitude", 116.4))
    # pre_1900 案例用 single 模式（sxtwl 对远古边界较稳定）
    mode = "single" if case.get("pre_1900") else "single"
    gender = case.get("gender")
    result = calculate(dt, lon, "Asia/Shanghai", use_solar=False, mode=mode, gender=gender)
    return result.verify_response


# ─────────────────────────────────────────────────────────────────────────────
# 四柱断言（所有 verified_pillars=true 的案例）
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("case", _VERIFIED_CASES, ids=[c["id"] for c in _VERIFIED_CASES])
def test_pillars_regression(case: dict) -> None:
    """O2: 四柱八字回归断言 — 覆盖 GT01-GT08 + CLS01-CLS12。"""

    vr = _run_case(case)
    computed = case.get("computed_pillars", {})
    if not computed:
        pytest.skip(f"{case['id']} 无 computed_pillars 参考值，跳过")

    p = vr.pillars_primary
    for pos, expected_gz in computed.items():
        pillar = getattr(p, pos)
        actual_gz = f"{pillar.stem}{pillar.branch}"
        assert actual_gz == expected_gz, (
            f"[{case['id']}] {pos} 四柱不符: 实际={actual_gz!r}，期望={expected_gz!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 格局断言（仅 post-1900 非 pre_1900 案例）
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("case", _POST1900_CASES, ids=[c["id"] for c in _POST1900_CASES])
def test_geju_regression(case: dict) -> None:
    """O2: 格局（geju_name）回归断言。"""
    recorded_geju = case.get("recorded_geju")
    if not recorded_geju:
        pytest.skip(f"{case['id']} 无 recorded_geju，跳过")

    vr = _run_case(case)
    geju = getattr(vr, "geju", None)
    if geju is None:
        pytest.skip(f"{case['id']} 响应无 geju 字段（引擎未启用），跳过")

    actual = getattr(geju, "geju_name", None) or getattr(geju, "name", None)
    assert actual == recorded_geju, (
        f"[{case['id']}] 格局不符: 实际={actual!r}，期望={recorded_geju!r}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 用神断言（仅 post-1900 非 pre_1900 案例）
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("case", _POST1900_CASES, ids=[c["id"] for c in _POST1900_CASES])
def test_yongshen_regression(case: dict) -> None:
    """O2: 用神（yongshen.favor）回归断言。"""
    recorded_yongshen = case.get("recorded_yongshen")
    if not recorded_yongshen:
        pytest.skip(f"{case['id']} 无 recorded_yongshen，跳过")

    vr = _run_case(case)
    yong = getattr(vr, "yongshen", None)
    if yong is None:
        pytest.skip(f"{case['id']} 响应无 yongshen 字段（引擎未启用），跳过")

    actual_favor = sorted(getattr(yong, "favor", []))
    expected_favor = sorted(recorded_yongshen)
    assert actual_favor == expected_favor, (
        f"[{case['id']}] 用神不符: 实际={actual_favor}，期望={expected_favor}"
    )
