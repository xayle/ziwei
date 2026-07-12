from __future__ import annotations

import pytest

from app.schemas.bazi import BaziFullRequest
from app.schemas.case import CaseCreate, CasePatch
from services.bazi_provenance import build_bazi_provenance, day_boundary_crossed


def test_day_boundary_crossed_rules():
    assert day_boundary_crossed("sxtwl", 23) is True
    assert day_boundary_crossed("sxtwl", 0) is True
    assert day_boundary_crossed("sxtwl", 12) is False
    assert day_boundary_crossed("early_zi_prev_day", 23) is True
    assert day_boundary_crossed("early_zi_prev_day", 0) is False
    assert day_boundary_crossed("early_zi_same_day", 23) is False


def test_build_bazi_provenance_includes_zi_day_rule():
    class _Geju:
        geju_name = "正官格"
        recorded_geju = "从官杀格"
        engine_geju = "七杀格"
        dual_track_note = "双轨说明"

    class _Resp:
        pillars_primary = object()
        geju = _Geju()
        yongshen = type("Y", (), {"favor": ["wood"]})()
        dayun = type("D", (), {"items": [1]})()
        bazi_summary = "摘要"
        yearly_fortune = []

    req = BaziFullRequest(
        dt="1990-01-15T23:30:00",
        lon=116.4,
        zi_day_rule="early_zi_prev_day",
    )
    prov = build_bazi_provenance(_Resp(), req, missing_fields=["forecast"])
    assert prov.pillars.layer == "engine"
    assert prov.geju.note and "early_zi_prev_day" in prov.geju.note
    assert prov.geju.note and "双轨说明" in prov.geju.note
    assert prov.analysis.note and "forecast" in prov.analysis.note


def test_case_create_validates_algo_fields():
    with pytest.raises(ValueError, match="year_divide"):
        CaseCreate(
            name="测试",
            birth_dt_local="1990-01-15T08:30:00",
            tz="Asia/Shanghai",
            lon=116.4,
            year_divide="bad",
        )
    case = CaseCreate(
        name="测试",
        birth_dt_local="1990-01-15T08:30:00",
        tz="Asia/Shanghai",
        lon=116.4,
        year_divide="normal",
        day_divide="forward",
        zi_day_rule="sxtwl",
    )
    assert case.year_divide == "normal"
    assert case.day_divide == "forward"


def test_case_patch_validates_algo_fields():
    with pytest.raises(ValueError, match="zi_day_rule"):
        CasePatch(zi_day_rule="invalid")
