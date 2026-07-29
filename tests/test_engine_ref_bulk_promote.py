"""inv-1.41：剩余 engine_ref transitive 升格 + 格局 cite E-01。"""

from __future__ import annotations

import json
from pathlib import Path

from services.bazi_engine.classic_refs import geju_candidates
from services.content_policy import clear_verified_ids_cache, is_verified_classic
from services.life_volume_service import build_life_volumes_from_charts

ROOT = Path(__file__).resolve().parent.parent

SAMPLE_PROMOTED = [
    "engine_ref.geju_002",
    "engine_ref.geju_e01",
    "engine_ref.yongshen_001",
    "engine_ref.dayun_001",
    "engine_ref.daymaster_001",
    "engine_ref.liunian_e02",
]


def setup_function() -> None:
    clear_verified_ids_cache()


def test_bulk_promoted_still_subset():
    raw = json.loads((ROOT / "data" / "classics.json").read_text(encoding="utf-8"))
    by = {i["id"]: i for i in raw}
    verified = {i["id"]: i for i in raw if i.get("verification_status") == "verified"}
    for cid in SAMPLE_PROMOTED:
        item = by[cid]
        assert item.get("verification_status") == "verified"
        assert item.get("verified_by") == "transitive-subset"
        p = (item.get("passage") or "").strip()
        assert any(p in (h.get("passage") or "") for h in verified.values() if h["id"] != cid)


def test_geju_candidates_verified_after_promote():
    refs = geju_candidates("正官格", limit=3)
    assert refs
    verified = [r for r in refs if r.get("hint_type") == "verified"]
    assert verified
    assert all(is_verified_classic(r["id"]) for r in verified)


def test_vol1_geju_cite_has_classic_id_not_raw_blob():
    """有 verified 格局条时，geju-cite 必须带 classic_id，不得把软拼文当 cite。"""
    doc = build_life_volumes_from_charts(
        case_id="bulk-geju",
        chart_hash="hash-bulk-geju",
        bazi={
            "geju": {
                "geju_name": "正官格",
                "geju_detail": "月令正官透干，清纯可用。",
                "classic_ref": "【软提示拼文】不得单独作典籍依据。",
            },
            "pillars_primary": {"day": {"stem": "甲", "branch": "子"}},
        },
        ziwei=None,
        explain_bazi={},
        explain_ziwei={},
        entitlement="full_book",
    )
    vol1 = next(v for v in doc.volumes if v.id == "vol1")
    cite = next((s for s in vol1.sections if s.id == "geju-cite"), None)
    soft = next((s for s in vol1.sections if s.id == "geju-classic-soft"), None)
    assert cite is not None
    assert cite.blocks
    assert cite.blocks[0].layer == "cite"
    assert cite.blocks[0].classic_id
    assert is_verified_classic(cite.blocks[0].classic_id)
    assert soft is None
