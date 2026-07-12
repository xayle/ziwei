"""
tests/test_golden_regression.py — O2: 黄金案例回归测试套件

从 data/ground_truth_cases.json 读取所有案例（GT01-GT08 + CLS01-CLS12），
参数化断言：
  - pillars_primary (四柱八字)
  - geju.geju_name (格局名称)
  - yongshen.favor (用神五行)

CLS 系列为 pre_1900 = true：
  - 四柱：引擎直测（calculate，不走 HTTP）
  - 格局/用神：对 engine_geju / engine_yongshen_favor 引擎基线断言
  - recorded_geju / recorded_yongshen 保留为古籍对照（见 test_cls_classical_drift）

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
from services.bazi_engine.geju import compute_geju
from services.bazi_engine.strength import compute_strength
from services.bazi_engine.wuxing import compute_wuxing
from services.bazi_engine.yongshen import compute_yongshen
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
_DATETIME_CASES = [c for c in _VERIFIED_CASES if not c.get("pillar_direct")]
_PILLAR_DIRECT_CASES = [c for c in _VERIFIED_CASES if c.get("pillar_direct")]
_PRE1900_CASES = [c for c in _VERIFIED_CASES if c.get("pre_1900")]


# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────────────────
class _PillarDirectResult:
    """pillar_direct 案例的轻量分析结果（无 VerifyResponse 包装）。"""

    def __init__(self, geju_name: str, yongshen_favor: list[str]) -> None:
        self.geju = type("Geju", (), {"geju_name": geju_name, "name": geju_name})()
        self.yongshen = type("Yongshen", (), {"favor": yongshen_favor})()
        self.missing_fields: list[str] = []


def _run_pillar_direct(case: dict) -> _PillarDirectResult:
    """四柱直测：古籍仅载干支、无公历生日（如千里命稿 pillar_input）。"""
    computed = case.get("computed_pillars") or {}
    pillars = [computed.get(k) for k in ("year", "month", "day", "hour")]
    if not all(pillars):
        raise ValueError(f"{case['id']} pillar_direct 缺少 computed_pillars")

    y, m, d, h = pillars
    ys, ms, ds, hs = y[0], m[0], d[0], h[0]
    yb, mb, db, hb = y[1], m[1], d[1], h[1]
    wx = compute_wuxing(ys, yb, ms, mb, ds, db, hs, hb)
    geju_name = compute_geju(ys, ms, mb, ds, hs, wx.scores_weighted, yb, db, hb)["name"]
    strength = compute_strength(ds, mb, ys, ms, hs, yb, db, hb, wx)
    favor = sorted(compute_yongshen(ds, mb, strength, wx, geju_name).favor or [])
    return _PillarDirectResult(geju_name, favor)


def _run_case(case: dict) -> Any:
    """调用 calculate() 或 pillar_direct 分析并返回结果对象。"""
    if case.get("pillar_direct"):
        return _run_pillar_direct(case)

    dt = datetime.fromisoformat(case["birth_dt_solar"]).replace(
        tzinfo=ZoneInfo("Asia/Shanghai")
    )
    lon = float(case.get("longitude", 116.4))
    mode = "single"
    gender = case.get("gender")
    result = calculate(dt, lon, "Asia/Shanghai", use_solar=False, mode=mode, gender=gender)
    return result.verify_response


def _geju_expected(case: dict) -> str | None:
    if case.get("engine_geju"):
        return case["engine_geju"]
    return case.get("recorded_geju")


def _yongshen_expected(case: dict) -> list[str] | None:
    if case.get("engine_yongshen_favor") is not None:
        return sorted(case["engine_yongshen_favor"])
    recorded = case.get("recorded_yongshen")
    return sorted(recorded) if recorded else None


_GEJU_CASES = [
    c
    for c in _VERIFIED_CASES
    if c.get("verified_geju") or (c.get("recorded_geju") and not c.get("pre_1900"))
]
_YONGSHEN_CASES = [
    c
    for c in _VERIFIED_CASES
    if c.get("verified_yongshen") or (c.get("recorded_yongshen") and not c.get("pre_1900"))
]


# ─────────────────────────────────────────────────────────────────────────────
# 四柱断言（所有 verified_pillars=true 的案例）
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("case", _DATETIME_CASES, ids=[c["id"] for c in _DATETIME_CASES])
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


@pytest.mark.parametrize("case", _PILLAR_DIRECT_CASES, ids=[c["id"] for c in _PILLAR_DIRECT_CASES])
def test_pillar_direct_static_pillars(case: dict) -> None:
    """pillar_direct 案例：校验 computed_pillars 四柱格式完整。"""
    computed = case.get("computed_pillars") or {}
    for pos in ("year", "month", "day", "hour"):
        gz = computed.get(pos)
        assert gz and len(gz) == 2, f"[{case['id']}] {pos} 四柱缺失或格式错误: {gz!r}"


# ─────────────────────────────────────────────────────────────────────────────
# 格局断言（GT + CLS 引擎基线）
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("case", _GEJU_CASES, ids=[c["id"] for c in _GEJU_CASES])
def test_geju_regression(case: dict) -> None:
    """O2: 格局（geju_name）回归断言。"""
    expected_geju = _geju_expected(case)
    if not expected_geju:
        pytest.skip(f"{case['id']} 无格局期望值，跳过")

    vr = _run_case(case)
    geju = getattr(vr, "geju", None)
    if geju is None:
        pytest.fail(f"{case['id']} 响应无 geju 字段")

    actual = getattr(geju, "geju_name", None) or getattr(geju, "name", None)
    assert actual == expected_geju, (
        f"[{case['id']}] 格局不符: 实际={actual!r}，期望={expected_geju!r}"
    )
    assert "geju" not in (vr.missing_fields or []), f"[{case['id']}] geju 在 missing_fields 中"


# ─────────────────────────────────────────────────────────────────────────────
# 用神断言（GT + CLS 引擎基线）
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("case", _YONGSHEN_CASES, ids=[c["id"] for c in _YONGSHEN_CASES])
def test_yongshen_regression(case: dict) -> None:
    """O2: 用神（yongshen.favor）回归断言。"""
    expected_favor = _yongshen_expected(case)
    if not expected_favor:
        pytest.skip(f"{case['id']} 无用神期望值，跳过")

    vr = _run_case(case)
    yong = getattr(vr, "yongshen", None)
    if yong is None:
        pytest.fail(f"{case['id']} 响应无 yongshen 字段")

    actual_favor = sorted(getattr(yong, "favor", []) or [])
    assert actual_favor == expected_favor, (
        f"[{case['id']}] 用神不符: 实际={actual_favor}，期望={expected_favor}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLS pre_1900：分析模块可计算性
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("case", _PRE1900_CASES, ids=[c["id"] for c in _PRE1900_CASES])
def test_pre1900_analysis_modules_present(case: dict) -> None:
    """pre_1900 案例：格局/用神模块应成功产出（非 missing_fields）。"""
    vr = _run_case(case)
    assert vr.geju is not None, f"[{case['id']}] geju 为空"
    assert vr.yongshen is not None and vr.yongshen.favor, f"[{case['id']}] yongshen.favor 为空"
    missing = set(vr.missing_fields or [])
    assert "geju" not in missing, f"[{case['id']}] geju 标记缺失"
    assert "yongshen" not in missing, f"[{case['id']}] yongshen 标记缺失"


# ─────────────────────────────────────────────────────────────────────────────
# CLS 古籍对照漂移（非阻塞，跟踪 engine vs 袁树珊 recorded）
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("case", _PRE1900_CASES, ids=[c["id"] for c in _PRE1900_CASES])
def test_cls_classical_geju_drift(case: dict) -> None:
    """古籍格局与引擎差异：已登记双轨说明则 PASS，否则 fail。"""
    recorded = case.get("recorded_geju")
    engine = case.get("engine_geju")
    if not recorded or not engine:
        pytest.skip(f"{case['id']} 缺少对照字段")
    if recorded == engine:
        return
    note = (
        (case.get("recorded_geju_classical_note") or "")
        + (case.get("recorded_yongshen_classical_note") or "")
        + (case.get("notes") or "")
    )
    if any(k in note for k in ("双轨", "漂移", "引擎取", "古籍注", "衍生")):
        return
    pytest.fail(
        f"[{case['id']}] 古籍={recorded!r} vs 引擎={engine!r} — 未登记双轨说明"
    )


@pytest.mark.parametrize("case", _PRE1900_CASES, ids=[c["id"] for c in _PRE1900_CASES])
def test_cls_classical_yongshen_drift(case: dict) -> None:
    """古籍用神与引擎差异：已登记说明则 PASS。"""
    recorded = sorted(case.get("recorded_yongshen") or [])
    engine = sorted(case.get("engine_yongshen_favor") or [])
    if not recorded or not engine:
        pytest.skip(f"{case['id']} 缺少对照字段")
    if recorded == engine:
        return
    note = (
        (case.get("recorded_geju_classical_note") or "")
        + (case.get("recorded_yongshen_classical_note") or "")
        + (case.get("notes") or "")
    )
    if any(k in note for k in ("双轨", "漂移", "引擎取", "古籍注", "衍生")):
        return
    pytest.fail(
        f"[{case['id']}] 古籍={recorded} vs 引擎={engine} — 未登记双轨说明"
    )
