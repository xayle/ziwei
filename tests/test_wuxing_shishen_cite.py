"""五行 / 十神 verified cite + FE 对齐用 BE 选型。"""

from __future__ import annotations

from services.bazi_engine.classic_refs import shishen_candidates, wuxing_candidates
from services.content_policy import clear_verified_ids_cache, is_verified_classic
from services.life_volume_service import build_life_volumes_from_charts


def setup_function() -> None:
    clear_verified_ids_cache()


def test_wuxing_shishen_candidates_verified():
    for fn in (wuxing_candidates, shishen_candidates):
        refs = fn(limit=2)
        assert refs
        assert all(r.get("hint_type") == "verified" for r in refs)
        assert all(is_verified_classic(r["id"]) for r in refs)


def test_vol1_mounts_wuxing_and_shishen_cite():
    doc = build_life_volumes_from_charts(
        case_id="wx-ss",
        chart_hash="hw",
        bazi={"pillars_primary": {"day": {"stem": "甲", "branch": "子"}}},
        ziwei=None,
        explain_bazi={},
        explain_ziwei={},
        entitlement="full_book",
    )
    vol1 = next(v for v in doc.volumes if v.id == "vol1")
    ids = {s.id for s in vol1.sections}
    assert "wuxing-cite" in ids
    assert "shishen-cite" in ids
    for sid in ("wuxing-cite", "shishen-cite"):
        sec = next(s for s in vol1.sections if s.id == sid)
        assert sec.blocks[0].layer == "cite"
        assert is_verified_classic(sec.blocks[0].classic_id)
