"""
M0 任务 0.22: L 级别判定 8 组参数化测试
=========================================
规格 (开发5.0.txt §0.22):
  L0 = dual + 双库完全一致（boundary_risk 不改变 L）
  L1 = single 模式 OR 仅时柱差异
  L2 = 含月柱差异（{month} 或 {hour, month}），不含日/年柱
  L3 = 含日柱或年柱差异
  ★ boundary_risk 不改变 L，仅写入 reasons
  ★ 红线#35: L0 必须满足 mode=dual
"""
from __future__ import annotations

import pytest
from boundary import (
    Pillar,
    Pillars,
    RiskFlags,
    compute_validation,
)

# ── 固定的测试用四柱 ────────────────────────────────────────────────────────────
_P_JIAZI = Pillars(
    year=Pillar("甲", "子", "甲子"),
    month=Pillar("丙", "寅", "丙寅"),
    day=Pillar("戊", "午", "戊午"),
    hour=Pillar("庚", "申", "庚申"),
)

_P_YIHAI = Pillars(
    year=Pillar("甲", "子", "甲子"),
    month=Pillar("丙", "寅", "丙寅"),
    day=Pillar("戊", "午", "戊午"),
    hour=Pillar("辛", "酉", "辛酉"),          # 时柱不同
)

_P_DIFF_MONTH = Pillars(
    year=Pillar("甲", "子", "甲子"),
    month=Pillar("丁", "卯", "丁卯"),          # 月柱不同
    day=Pillar("戊", "午", "戊午"),
    hour=Pillar("庚", "申", "庚申"),
)

_P_DIFF_HOUR_MONTH = Pillars(
    year=Pillar("甲", "子", "甲子"),
    month=Pillar("丁", "卯", "丁卯"),          # 月柱不同
    day=Pillar("戊", "午", "戊午"),
    hour=Pillar("辛", "酉", "辛酉"),           # 时柱也不同
)

_P_DIFF_DAY = Pillars(
    year=Pillar("甲", "子", "甲子"),
    month=Pillar("丙", "寅", "丙寅"),
    day=Pillar("己", "未", "己未"),            # 日柱不同
    hour=Pillar("庚", "申", "庚申"),
)

_P_DIFF_YEAR = Pillars(
    year=Pillar("乙", "丑", "乙丑"),           # 年柱不同
    month=Pillar("丙", "寅", "丙寅"),
    day=Pillar("戊", "午", "戊午"),
    hour=Pillar("庚", "申", "庚申"),
)

def _no_risk() -> RiskFlags:
    return RiskFlags(
        near_shichen_boundary=False,
        near_jieqi_boundary=False,
        jieqi_boundary_status="ok",
        minutes_to_shichen_boundary=60.0,
        minutes_to_jieqi_boundary=60.0,
    )

def _near_shichen_risk() -> RiskFlags:
    """近时辰边界 — 应写入 reasons 但不改变 L"""
    return RiskFlags(
        near_shichen_boundary=True,
        near_jieqi_boundary=False,
        jieqi_boundary_status="ok",
        minutes_to_shichen_boundary=3.0,
        minutes_to_jieqi_boundary=60.0,
    )


# ── 8 组参数化测试 ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "case_name, primary, secondary, risk_flags, mode, expected_level",
    [
        # 1. dual + 完全一致 + 无边界风险 → L0
        (
            "dual_identical_no_risk",
            _P_JIAZI, _P_JIAZI, _no_risk(), "dual", "L0",
        ),
        # 2. dual + 完全一致 + 近时辰边界 → 仍然 L0（boundary_risk 不改变 L）
        (
            "dual_identical_with_shichen_risk",
            _P_JIAZI, _P_JIAZI, _near_shichen_risk(), "dual", "L0",
        ),
        # 3. single 模式 → L1（无论差异）
        (
            "single_mode",
            _P_JIAZI, None, _no_risk(), "single", "L1",
        ),
        # 4. dual + 仅时柱差异 → L1
        (
            "dual_diff_hour_only",
            _P_JIAZI, _P_YIHAI, _no_risk(), "dual", "L1",
        ),
        # 5. dual + 仅月柱差异 → L2
        (
            "dual_diff_month_only",
            _P_JIAZI, _P_DIFF_MONTH, _no_risk(), "dual", "L2",
        ),
        # 6. dual + 时柱+月柱双差异 → L2
        (
            "dual_diff_hour_and_month",
            _P_JIAZI, _P_DIFF_HOUR_MONTH, _no_risk(), "dual", "L2",
        ),
        # 7. dual + 日柱差异 → L3
        (
            "dual_diff_day",
            _P_JIAZI, _P_DIFF_DAY, _no_risk(), "dual", "L3",
        ),
        # 8. dual + 年柱差异 → L3
        (
            "dual_diff_year",
            _P_JIAZI, _P_DIFF_YEAR, _no_risk(), "dual", "L3",
        ),
    ],
    ids=[
        "TC1_dual_identical_no_risk",
        "TC2_dual_identical_with_shichen_risk",
        "TC3_single_mode",
        "TC4_dual_diff_hour_only",
        "TC5_dual_diff_month_only",
        "TC6_dual_diff_hour_and_month",
        "TC7_dual_diff_day",
        "TC8_dual_diff_year",
    ],
)
def test_boundary_level(
    case_name: str,
    primary: Pillars,
    secondary,
    risk_flags: RiskFlags,
    mode: str,
    expected_level: str,
):
    """验证 8 组 L 级别判定，覆盖所有分支。"""
    result = compute_validation(
        pillars_primary=primary,
        pillars_secondary=secondary,
        risk_flags=risk_flags,
        mode=mode,  # type: ignore[arg-type]
    )
    assert result.level == expected_level, (
        f"[{case_name}] 期望 level={expected_level}, 实际={result.level} "
        f"(diff_fields={result.diff_fields}, mode={mode})"
    )


def test_boundary_risk_does_not_change_level():
    """红线验证: near_shichen_boundary=True 不改变 L0 → 仍为 L0，但写入 reasons。"""
    risk = _near_shichen_risk()
    result_with_risk = compute_validation(_P_JIAZI, _P_JIAZI, risk, "dual")
    result_no_risk   = compute_validation(_P_JIAZI, _P_JIAZI, _no_risk(), "dual")

    assert result_with_risk.level == result_no_risk.level == "L0", (
        "boundary_risk 不应改变 level"
    )
    assert "near_shichen_boundary" in result_with_risk.reasons, (
        "near_shichen_boundary 应写入 reasons"
    )


def test_l0_requires_dual_mode():
    """红线#35: L0 必须满足 mode=dual；single 模式不得返回 L0。"""
    result = compute_validation(_P_JIAZI, None, _no_risk(), "single")
    assert result.level != "L0", "single 模式严禁返回 L0"
    assert result.level == "L1"
