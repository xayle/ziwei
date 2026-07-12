"""ZW18 trust_level regression (1998-1-28 female)."""

from __future__ import annotations

from services.ziwei_engine import ziwei_full
from services.ziwei_trust import compute_ziwei_trust_level


def test_zw18_chart_computes():
    chart = ziwei_full(1998, 1, 28, 8, 0, "女")
    assert chart.life_palace_gz
    assert len(chart.palaces) == 12


def test_trust_level_full_when_no_issues():
    level = compute_ziwei_trust_level(
        missing_fields=[],
        engine_warnings=[],
        iztro_crosscheck=None,
    )
    assert level == "full"


def test_trust_level_degraded_on_life_palace_mismatch():
    from app.schemas.ziwei import IztroCrosscheckResponse

    level = compute_ziwei_trust_level(
        missing_fields=[],
        engine_warnings=[],
        iztro_crosscheck=IztroCrosscheckResponse(
            status="mismatch",
            main_match=10,
            main_total=14,
            life_palace_match=False,
            iztro_life_palace_gz="甲子",
            engine_life_palace_gz="乙丑",
        ),
    )
    assert level == "degraded"


def test_trust_level_advisory_on_youbi_month_warning():
    """R038: default month youbi drift → advisory, not degraded."""
    level = compute_ziwei_trust_level(
        missing_fields=["youbi_month_vs_iztro_hour"],
        engine_warnings=["右弼依生月安星（youbi_method=month）；与 iztro 默认口径可能差一宫，属流派差异，非引擎错误。"],
        iztro_crosscheck=None,
    )
    assert level == "advisory"


def test_trust_level_advisory_on_palace_ten_gods_missing():
    """R039: palace ten-gods not yet modeled → advisory via missing_fields."""
    level = compute_ziwei_trust_level(
        missing_fields=["palace_ten_gods"],
        engine_warnings=[],
        iztro_crosscheck=None,
    )
    assert level == "advisory"
