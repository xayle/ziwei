"""vol3 大运/流年 verified cite。"""

from __future__ import annotations

from services.bazi_engine.classic_refs import dayun_candidates, liunian_candidates
from services.content_policy import clear_verified_ids_cache, is_verified_classic
from services.life_volume_service import build_life_volumes_from_charts


def setup_function() -> None:
    clear_verified_ids_cache()


def test_dayun_liunian_candidates_prefer_verified():
    dayun = dayun_candidates(limit=2)
    liunian = liunian_candidates(limit=2)
    assert dayun and all(r.get("hint_type") == "verified" for r in dayun)
    assert liunian and all(r.get("hint_type") == "verified" for r in liunian)
    assert all(is_verified_classic(r["id"]) for r in dayun + liunian)


def test_vol3_mounts_dayun_and_liunian_cite():
    doc = build_life_volumes_from_charts(
        case_id="vol3-cite",
        chart_hash="h3",
        bazi={
            "dayun": {
                "items": [
                    {"ganzhi": "甲子", "start_age": 8, "end_age": 17},
                    {"ganzhi": "乙丑", "start_age": 18, "end_age": 27},
                ]
            },
            "liunian": {
                "items": [
                    {"year": 2025, "stem": "乙", "branch": "巳", "ten_god": "食神"},
                    {"year": 2026, "stem": "丙", "branch": "午", "ten_god": "伤官"},
                ]
            },
        },
        ziwei=None,
        explain_bazi={},
        explain_ziwei={},
        entitlement="full_book",
    )
    vol3 = next(v for v in doc.volumes if v.id == "vol3")
    ids = [s.id for s in vol3.sections]
    assert "dayun-cite" in ids
    assert "liunian-cite" in ids
    for sid in ("dayun-cite", "liunian-cite"):
        sec = next(s for s in vol3.sections if s.id == sid)
        assert sec.blocks
        assert sec.blocks[0].layer == "cite"
        assert sec.blocks[0].classic_id
        assert is_verified_classic(sec.blocks[0].classic_id)
        assert "典籍依据" in sec.blocks[0].text
