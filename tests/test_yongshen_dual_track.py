"""Yongshen dual-track payload tests."""

from services.bazi_engine.yongshen_payload import build_yongshen_model


def test_zip01_yongshen_dual_track():
    model = build_yongshen_model(
        ["water", "wood"],
        ["metal"],
        "引擎扶身",
        year="己亥",
        month="丁卯",
        day="乙未",
        hour="己卯",
    )
    assert model.dual_track_id == "ZIP01"
    assert model.recorded_favor == ["earth", "fire"]
    assert model.engine_favor == ["water", "wood"]
    assert model.dual_track_note and "双轨" in model.dual_track_note


def test_non_dual_track_pillars():
    model = build_yongshen_model(["water"], [], None, year="甲子", month="丙寅", day="庚午", hour="丙辰")
    assert model.dual_track_id is None
    assert model.recorded_favor == []
