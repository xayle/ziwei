"""关系 verified cite 选取与地支子集升格。"""

from __future__ import annotations

import json
from pathlib import Path

from services.content_policy import clear_verified_ids_cache, is_verified_classic
from services.relations_classic_cite import (
    RELATIONS_HOST_ID,
    clear_relations_cite_caches,
    pick_relations_verified_cites,
)

ROOT = Path(__file__).resolve().parent.parent


def setup_function() -> None:
    clear_relations_cite_caches()


def test_dizhi_ext_subset_promoted_verified():
    clear_verified_ids_cache()
    assert is_verified_classic("engine_ref.dizhi_ext04")
    assert is_verified_classic("engine_ref.dizhi_ext05")
    assert is_verified_classic("engine_ref.dizhi_ext06")
    # 冲合专条仍须底本 spotcheck，不得误升
    assert not is_verified_classic("engine_ref.dizhi_ext01")
    assert not is_verified_classic("engine_ref.dizhi_ext02")


def test_pick_relations_verified_cites_prefers_host_for_clash():
    cites = pick_relations_verified_cites(
        {"clash_summary": "冲：子午", "combine_summary": "", "items": []},
        limit=2,
    )
    assert cites
    assert cites[0]["id"] == RELATIONS_HOST_ID
    assert "冲" in cites[0]["passage"]
    assert is_verified_classic(cites[0]["id"])


def test_pick_relations_verified_cites_harm_can_use_dizhi_ext05():
    cites = pick_relations_verified_cites(
        {"harm_summary": "害：子未", "items": []},
        limit=2,
    )
    assert cites
    ids = {c["id"] for c in cites}
    assert "engine_ref.dizhi_ext05" in ids or RELATIONS_HOST_ID in ids
    for c in cites:
        assert is_verified_classic(c["id"])


def test_promoted_passages_still_subset_of_hosts():
    raw = json.loads((ROOT / "data" / "classics.json").read_text(encoding="utf-8"))
    by = {i["id"]: i for i in raw}
    pairs = {
        "engine_ref.dizhi_ext04": "chapter_agg.滴天髓",
        "engine_ref.dizhi_ext05": "chapter_agg.三命通会",
        "engine_ref.dizhi_ext06": "chapter_agg.渊海子平",
    }
    for cid, host in pairs.items():
        assert (by[cid].get("passage") or "") in (by[host].get("passage") or "")
