"""神煞引擎条 transitive 升格 → candidates hint_type=verified → vol2 cite。"""

from __future__ import annotations

import json
from pathlib import Path

from services.bazi_engine.classic_refs import shensha_candidates
from services.content_policy import clear_verified_ids_cache, is_verified_classic
from services.life_volume_service import _shensha_classic_quote_blocks

ROOT = Path(__file__).resolve().parent.parent

PROMOTED = [
    "engine_ref.shensha_002",
    "engine_ref.shensha_003",
    "engine_ref.shensha_004",
    "engine_ref.shensha_005",
    "engine_ref.shensha_006",
    "engine_ref.shensha_008",
]


def setup_function() -> None:
    clear_verified_ids_cache()


def test_shensha_subset_promoted_and_blocked_pairs():
    for cid in PROMOTED:
        assert is_verified_classic(cid)
    # 冲合专条已改为宿主真子集
    assert is_verified_classic("engine_ref.dizhi_ext01")
    assert is_verified_classic("engine_ref.dizhi_ext02")
    assert is_verified_classic("engine_ref.dizhi_ext03")
    assert not is_verified_classic("engine_ref.shensha_001")
    assert not is_verified_classic("engine_ref.shensha_007")


def test_shensha_candidates_mark_verified():
    refs = shensha_candidates("驿马", limit=2)
    assert refs
    verified = [r for r in refs if r.get("hint_type") == "verified"]
    assert verified
    assert verified[0]["id"].startswith("engine_ref.")
    assert is_verified_classic(verified[0]["id"])


def test_shensha_quote_blocks_emit_cite_layer():
    bazi = {
        "shensha": [
            {
                "name": "驿马",
                "classic_refs": shensha_candidates("驿马", limit=1),
            }
        ]
    }
    blocks = _shensha_classic_quote_blocks(bazi)
    assert blocks
    assert blocks[0].layer == "cite"
    assert blocks[0].classic_id
    assert is_verified_classic(blocks[0].classic_id)


def test_promoted_still_subset_of_hosts():
    raw = json.loads((ROOT / "data" / "classics.json").read_text(encoding="utf-8"))
    by = {i["id"]: i for i in raw}
    pairs = {
        "engine_ref.shensha_002": "chapter_agg.三命通会",
        "engine_ref.shensha_004": "chapter_agg.渊海子平",
        "engine_ref.dayun_012": "chapter_agg.三命通会",
        "engine_ref.general_006": "chapter_agg.滴天髓",
    }
    for cid, host in pairs.items():
        assert (by[cid].get("passage") or "") in (by[host].get("passage") or "")
