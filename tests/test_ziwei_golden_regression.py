"""Parametric golden regression for ZW01–ZW20 (10.0 target plan / BE-P1-04)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from services.ziwei_engine import ziwei_full

ROOT = Path(__file__).resolve().parents[1]
GT_PATH = ROOT / "data" / "ziwei_ground_truth.json"
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
MAIN_STARS = [
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府", "太阴",
    "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
]
AUX_STARS = ["文昌", "文曲", "左辅", "右弼", "擎羊", "陀罗"]
EXTENDED_AUX = ["天魁", "天钺", "火星", "铃星"]
# 收紧后不应出现的误报格局（全 ZW 盘负向控制）
FORBIDDEN_LOOSE_PATTERNS = frozenset({"天同守命"})  # 若庙旺/煞星条件不满足则不应出现


def _extended_aux_positions(chart) -> dict[str, str]:
    aux_pos: dict[str, str] = {}
    for p in chart.palaces:
        br = BRANCHES[p.branch_idx]
        for s in p.aux_stars:
            name = s["name"] if isinstance(s, dict) else s.name
            if name in EXTENDED_AUX:
                aux_pos[name] = br
    return aux_pos


def _load_cases() -> list[dict]:
    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    return data.get("cases", [])


def _case_engine_kwargs(case: dict) -> dict:
    keys = (
        "youbi_method",
        "leap_month_method",
        "year_divide",
        "day_divide",
        "late_zishi",
        "brightness_method",
        "kuiyue_method",
        "tianma_method",
    )
    return {k: case[k] for k in keys if k in case}


def _chart_for_case(case: dict):
    b = case["birth"]
    return ziwei_full(
        b["year"], b["month"], b["day"], b["hour"], b["minute"], b["gender"],
        **_case_engine_kwargs(case),
    )


def _chart_positions(chart) -> tuple[dict[str, str], dict[str, str]]:
    main_pos: dict[str, str] = {}
    aux_pos: dict[str, str] = {}
    for p in chart.palaces:
        br = BRANCHES[p.branch_idx]
        for s in p.main_stars:
            name = s["name"] if isinstance(s, dict) else s.name
            if name in MAIN_STARS:
                main_pos[name] = br
        for s in p.aux_stars:
            name = s["name"] if isinstance(s, dict) else s.name
            if name in AUX_STARS:
                aux_pos[name] = br
    return main_pos, aux_pos


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_zw_main_stars(case: dict):
    chart = _chart_for_case(case)
    main_pos, _ = _chart_positions(chart)
    expected = case.get("main_stars", {})
    for star, branch in expected.items():
        assert star in main_pos, f"{case['id']} missing {star}"
        assert main_pos[star] == branch, (
            f"{case['id']} {star}: expected {branch}, got {main_pos[star]}"
        )


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_zw_aux_stars(case: dict):
    chart = _chart_for_case(case)
    _, aux_pos = _chart_positions(chart)
    expected = case.get("aux_stars", {})
    for star, branch in expected.items():
        assert star in aux_pos, f"{case['id']} missing aux {star}"
        assert aux_pos[star] == branch, (
            f"{case['id']} aux {star}: expected {branch}, got {aux_pos[star]}"
        )


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_zw_life_palace(case: dict):
    chart = _chart_for_case(case)
    assert chart.life_palace_gz == case["life_palace_gz"]
    assert chart.wuxing_ju_name == case["wuxing_ju_name"]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_zw_extended_aux(case: dict):
    chart = _chart_for_case(case)
    aux_pos = _extended_aux_positions(chart)
    expected = case.get("extended_aux", {})
    for star, branch in expected.items():
        assert star in aux_pos, f"{case['id']} missing extended {star}"
        assert aux_pos[star] == branch, (
            f"{case['id']} {star}: expected {branch}, got {aux_pos[star]}"
        )


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_zw_patterns_not_inflated(case: dict):
    from services.ziwei_engine.patterns import detect_patterns

    chart = _chart_for_case(case)
    names = {p.name for p in detect_patterns(chart.palaces)}
    assert len(names) <= 12, f"{case['id']} too many patterns: {sorted(names)}"
    for bad in FORBIDDEN_LOOSE_PATTERNS:
        if bad in names:
            pytest.fail(f"{case['id']} false positive pattern: {bad}")


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_zw_expected_patterns_subset(case: dict):
    expected = case.get("expected_patterns") or []
    if not expected:
        return
    from services.ziwei_engine.patterns import detect_patterns

    chart = _chart_for_case(case)
    names = {p.name for p in detect_patterns(chart.palaces)}
    for pat in expected:
        assert pat in names, f"{case['id']} missing expected pattern {pat}"


def test_zw_dataset_has_twenty():
    assert len(_load_cases()) >= 20


def test_zw_patterns_zrule_registry():
    """Patterns module exposes ZRULE_043–050 for golden false-positive guard."""
    from services.ziwei_engine import patterns

    src = Path(patterns.__file__).read_text(encoding="utf-8")
    assert "ZRULE_043" in src
    assert "ZRULE_050" in src
    assert "brightness_val" in src
