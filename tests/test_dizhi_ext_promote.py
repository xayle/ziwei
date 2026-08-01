"""inv-1.46：dizhi_ext01/02/03 改为宿主真子集并 verified。"""

from __future__ import annotations

import json
from pathlib import Path

from services.content_policy import clear_verified_ids_cache, is_verified_classic

ROOT = Path(__file__).resolve().parent.parent
HOST = "daizhige.ziping.论刑冲会合解法"
PROMOTED = [
    "engine_ref.dizhi_ext01",
    "engine_ref.dizhi_ext02",
    "engine_ref.dizhi_ext03",
]


def setup_function() -> None:
    clear_verified_ids_cache()


def test_dizhi_ext01_03_subset_of_host():
    raw = json.loads((ROOT / "data" / "classics.json").read_text(encoding="utf-8"))
    by = {i["id"]: i for i in raw}
    host_pass = (by[HOST].get("passage") or "")
    for cid in PROMOTED:
        item = by[cid]
        assert item.get("verification_status") == "verified"
        assert item.get("verified_by") == "transitive-subset"
        p = (item.get("passage") or "").strip()
        assert p and p in host_pass
        assert is_verified_classic(cid)
