"""日主 / 婚恋 / 健康 verified cite。"""

from __future__ import annotations

from services.bazi_engine.classic_refs import (
    daymaster_candidates,
    health_candidates,
    marriage_candidates,
)
from services.content_policy import clear_verified_ids_cache, is_verified_classic
from services.life_volume_service import build_life_volumes_from_charts


def setup_function() -> None:
    clear_verified_ids_cache()


def test_category_candidates_verified():
    for fn in (daymaster_candidates, marriage_candidates, health_candidates):
        refs = fn(limit=2)
        assert refs
        assert all(r.get("hint_type") == "verified" for r in refs)
        assert all(is_verified_classic(r["id"]) for r in refs)


def test_vol1_daymaster_cite_and_vol5_domain_cites():
    doc = build_life_volumes_from_charts(
        case_id="dm-domain",
        chart_hash="hd",
        bazi={
            "day_master_strength": {"tier": "中和", "score": 50},
            "career": {"interpretation_text": "事业宜稳中求进，先立根基再谈扩张。"},
        },
        ziwei=None,
        explain_bazi={},
        explain_ziwei={},
        entitlement="full_book",
    )
    vol1 = next(v for v in doc.volumes if v.id == "vol1")
    vol5 = next(v for v in doc.volumes if v.id == "vol5")
    dm = next(s for s in vol1.sections if s.id == "daymaster-cite")
    assert dm.blocks[0].classic_id.startswith("engine_ref.daymaster_")
    ids = {s.id for s in vol5.sections}
    assert "marriage-cite" in ids
    assert "health-cite" in ids
    for sid in ("marriage-cite", "health-cite"):
        sec = next(s for s in vol5.sections if s.id == sid)
        assert sec.collapsed_default is True
        assert sec.blocks[0].layer == "cite"
        assert is_verified_classic(sec.blocks[0].classic_id)
