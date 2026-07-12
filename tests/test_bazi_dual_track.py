"""格局/用神双轨登记（services/bazi_engine/dual_track.py）。"""

from __future__ import annotations

from services.bazi_engine.dual_track import (
    lookup_dual_track,
    lookup_yongshen_dual_track,
    pillars_key,
    registered_geju_dual_track_ids,
    registered_yongshen_dual_track_ids,
)


def test_pillars_key_format():
    assert pillars_key("甲", "子", "乙", "丑") == "甲|子|乙|丑"


def test_zip09_geju_dual_track():
    row = lookup_dual_track("辛巳", "辛丑", "乙酉", "乙酉")
    assert row is not None
    assert row["id"] == "ZIP09"
    assert row["recorded_geju"] == "从官杀格"


def test_zip01_yongshen_dual_track():
    row = lookup_yongshen_dual_track("己亥", "丁卯", "乙未", "己卯")
    assert row is not None
    assert row["id"] == "ZIP01"
    assert row["recorded_favor"] == ["earth", "fire"]


def test_registry_ids_complete():
    assert registered_geju_dual_track_ids() == ["ZIP09", "ZIP21", "ZIP22"]
    assert registered_yongshen_dual_track_ids() == ["ZIP01", "ZIP04", "ZIP05"]
