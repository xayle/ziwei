"""ZW18 trust_level regression (1998-1-28 female)."""

from __future__ import annotations

from services.ziwei_engine import ziwei_full
from services.ziwei_trust import compute_ziwei_trust_level


def test_zw18_chart_computes():
    chart = ziwei_full(1998, 1, 28, 8, 0, "女")
    assert chart.life_palace_gz
    assert len(chart.palaces) == 12
    assert all((p.ten_god or "").strip() for p in chart.palaces)
    assert "palace_ten_gods" not in (chart.missing_fields or [])


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


def test_trust_level_full_with_youbi_month_colophon():
    """右弼按月仅作校勘脚注，不再压为 advisory。"""
    level = compute_ziwei_trust_level(
        missing_fields=[],
        engine_warnings=["右弼依生月安星（按月）；与开源对照轨默认口径可能差一宫，属流派差异，非引擎错误。"],
        iztro_crosscheck=None,
    )
    assert level == "full"


def test_trust_level_advisory_on_palace_ten_gods_missing():
    """若宫位十神仍缺失，则 advisory。"""
    level = compute_ziwei_trust_level(
        missing_fields=["palace_ten_gods"],
        engine_warnings=[],
        iztro_crosscheck=None,
    )
    assert level == "advisory"


def test_default_month_youbi_chart_trust_full():
    chart = ziwei_full(1990, 1, 15, 8, 30, "男", youbi_method="month")
    assert any("右弼" in w for w in (chart.engine_warnings or []))
    assert "youbi_month_vs_iztro_hour" not in (chart.missing_fields or [])
    assert "palace_ten_gods" not in (chart.missing_fields or [])
    level = compute_ziwei_trust_level(
        missing_fields=chart.missing_fields,
        engine_warnings=chart.engine_warnings,
        iztro_crosscheck=None,
    )
    assert level == "full"
