"""Geju API payload: is_broken, dual-track, shun_ni wiring."""
from __future__ import annotations

from services.bazi_engine.classical_narrative import shun_ni
from services.bazi_engine.geju import compute_geju
from services.bazi_engine.geju_payload import build_geju_model


def test_is_broken_from_po_geju_not_confident():
    """破格应读 po_geju.broken，而非 confident 字段。"""
    raw = compute_geju(
        "甲", "丙", "寅", "庚", "丙",
        wuxing_scores={"wood": 10, "fire": 30, "earth": 15, "metal": 35, "water": 10},
        year_branch="子", day_branch="午", hour_branch="辰",
    )
    model = build_geju_model(raw, year="甲子", month="丙寅", day="庚午", hour="丙辰")
    po = raw.get("po_geju") or {}
    assert model.is_broken == bool(po.get("broken"))


def test_zip09_dual_track_exposed():
    """辛巳辛丑乙酉乙酉 应暴露古籍从官杀 vs 引擎七杀双轨。"""
    raw = compute_geju(
        "辛", "辛", "丑", "乙", "乙",
        year_branch="巳", day_branch="酉", hour_branch="酉",
    )
    model = build_geju_model(
        raw,
        year="辛巳", month="辛丑", day="乙酉", hour="乙酉",
    )
    assert model.geju_name == "七杀格"
    assert model.recorded_geju == "从官杀格"
    assert model.dual_track_id == "ZIP09"
    assert model.dual_track_note
    assert isinstance(model.geju_candidates, list)


def test_zip21_dual_track_exposed():
    raw = compute_geju(
        "癸", "丁", "酉", "乙", "丁",
        year_branch="酉", day_branch="卯", hour_branch="亥",
    )
    model = build_geju_model(
        raw,
        year="癸酉", month="丁酉", day="乙卯", hour="丁亥",
    )
    assert model.geju_name == "七杀格"
    assert model.recorded_geju == "食神制杀格"
    assert model.dual_track_id == "ZIP21"
    assert model.derived_geju == raw.get("derived_geju")


def test_zip22_dual_track_exposed():
    raw = compute_geju(
        "庚", "壬", "午", "甲", "丙",
        year_branch="午", day_branch="寅", hour_branch="寅",
    )
    model = build_geju_model(
        raw,
        year="庚午", month="壬午", day="甲寅", hour="丙寅",
    )
    assert model.geju_name == "伤官格"
    assert model.recorded_geju == "伤官佩印格"
    assert model.dual_track_id == "ZIP22"


def test_shun_ni_signature():
    out = shun_ni("forward", "forward", tier="偏旺")
    assert out["tone"] == "顺"
    assert "偏旺" in out["summary"]
