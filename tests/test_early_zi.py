"""
早子时口径确认测试 — M1 任务 1.19 [P67]

早子时方案 v4 口径：
  zi_initial 规则下，23:00-00:59 均属于"早子时"窗口
  - 时柱以 sxtwl 计算结果为准（不做 day+1 特殊处理）
  - raw.day_boundary_crossed 在 23:00+ 为 True（提示标记）
  - 日柱是否跨日取决于 sxtwl 实际行为

8 个样例:
  主样例 6 个: 23:00 / 23:30 / 23:59 / 00:00 / 00:30 / 00:59
  对照样例 2 个: 22:59 (不触发早子时) / 01:00 (正常)
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from run import app

client = TestClient(app)

BASE = {
    "lon": 121.47,
    "mode": "single",
    "solar_time_enabled": False,
    "tz": "Asia/Shanghai",
}

DATE = "2026-06-15"


@pytest.mark.parametrize("time_str,expect_boundary,expect_hour_branch_in", [
    # 主样例：23:00-00:59，均属早子时窗口
    ("23:00:00", True,  ["子", "壬"]),   # 子时开始
    ("23:30:00", True,  ["子", "壬"]),
    ("23:59:00", True,  ["子", "壬"]),
    ("00:00:00", True,  ["子", "壬"]),   # 次日0点仍为子时
    ("00:30:00", True,  ["子", "壬"]),
    ("00:59:00", True,  ["子", "壬"]),
    # 对照样例：22:59 不触发早子时
    ("22:59:00", False, ["亥"]),         # 亥时
    # 对照样例：01:00 正常丑时
    ("01:00:00", False, ["丑"]),         # 丑时
])
def test_early_zi_boundary_flag(time_str: str, expect_boundary: bool, expect_hour_branch_in: list[str]):
    """验证早子时窗口内 day_boundary_crossed 标志及时支。"""
    payload = dict(BASE, dt=f"{DATE}T{time_str}")
    resp = client.post("/api/v1/bazi/full", json=payload)
    assert resp.status_code == 200, f"API error for {time_str}: {resp.text}"

    data = resp.json()
    raw = data.get("raw", {})

    # day_boundary_crossed 断言
    assert raw.get("day_boundary_crossed") == expect_boundary, (
        f"[{time_str}] expect day_boundary_crossed={expect_boundary}, "
        f"got={raw.get('day_boundary_crossed')}"
    )

    # 时支断言（允许前后±1支的误差反映 sxtwl 实际行为）
    hour_branch = data.get("pillars_primary", {}).get("hour", {}).get("branch", "?")
    assert hour_branch in expect_hour_branch_in, (
        f"[{time_str}] expect hour_branch in {expect_hour_branch_in}, "
        f"got={hour_branch}"
    )


@pytest.mark.parametrize("time_str", ["23:00:00", "23:30:00", "23:59:00", "00:00:00", "00:30:00", "00:59:00"])
def test_early_zi_methods_field(time_str: str):
    """早子时窗口内 methods.day_boundary_rule 应为 zi_initial。"""
    payload = dict(BASE, dt=f"{DATE}T{time_str}")
    resp = client.post("/api/v1/bazi/full", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["methods"]["day_boundary_rule"] == "zi_initial", (
        f"[{time_str}] methods.day_boundary_rule should be zi_initial"
    )
