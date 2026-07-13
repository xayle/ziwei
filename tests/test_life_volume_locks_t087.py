"""T087 · Q2 volume locked rules (life-volume generation)."""

from __future__ import annotations

from services.life_volume_service import _apply_volume_locks, build_life_volumes_from_charts
from app.schemas.life_volume import LIFE_VOLUME_LABELS, LifeVolumeModel


def _empty_vols() -> list[LifeVolumeModel]:
    return [
        LifeVolumeModel(id=vid, title=LIFE_VOLUME_LABELS[vid], sections=[])  # type: ignore[arg-type]
        for vid in ("preface", "vol1", "vol2", "vol3", "vol4", "vol5", "vol6", "colophon")
    ]


def test_apply_locks_free_tier_q2():
    locked_map = {v.id: v.locked for v in _apply_volume_locks(_empty_vols(), "free")}
    assert locked_map["preface"] is False
    assert locked_map["vol1"] is False
    assert locked_map["vol2"] is True
    assert locked_map["vol3"] is True
    assert locked_map["vol4"] is True
    assert locked_map["vol5"] is True
    assert locked_map["vol6"] is True
    assert locked_map["colophon"] is False


def test_apply_locks_volume_pass():
    locked_map = {v.id: v.locked for v in _apply_volume_locks(_empty_vols(), "volume_pass")}
    assert locked_map["vol2"] is False
    assert locked_map["vol4"] is False
    assert locked_map["vol5"] is True
    assert locked_map["vol6"] is True


def test_apply_locks_full_book():
    assert all(not v.locked for v in _apply_volume_locks(_empty_vols(), "full_book"))


def test_build_life_volumes_respects_free_entitlement():
    resp = build_life_volumes_from_charts(
        case_id="c-lock",
        chart_hash="h",
        bazi={
            "pillars_primary": {
                "day": {"stem": "甲", "branch": "子"},
            },
            "geju": {"geju_name": "正官格"},
            "missing_fields": [],
        },
        ziwei=None,
        explain_bazi={"disclaimer_block": {"text": "免责", "version": "t", "jurisdiction": "CN"}},
        explain_ziwei={},
        entitlement="free",
    )
    by_id = {v.id: v for v in resp.volumes}
    assert by_id["vol1"].locked is False
    assert by_id["vol3"].locked is True
    assert by_id["vol3"].sections[0].id == "locked"
    assert "Pass" in by_id["vol3"].sections[0].blocks[0].text
    assert by_id["vol5"].locked is True
    assert "全书" in by_id["vol5"].sections[0].blocks[0].text
