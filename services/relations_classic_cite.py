"""关系卷 verified cite 选取：优先已核验篇章，不用未 spotcheck 的引擎复述冒充 cite。"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from services.bazi_engine.classic_refs import relations_signal_tags
from services.content_policy import is_verified_classic

ROOT = Path(__file__).resolve().parent.parent
CLASSICS_PATH = ROOT / "data" / "classics.json"

# 刑冲会合总论（已 verified）—— 冲/合/刑 主宿主
RELATIONS_HOST_ID = "daizhige.ziping.论刑冲会合解法"

# 信号 → 优先句锚 + 可选专用 verified 条（子集升格后）
SIGNAL_ANCHORS: dict[str, tuple[list[str], list[str]]] = {
    "六冲": (["冲者", "六冲", "解冲"], [RELATIONS_HOST_ID, "engine_ref.dizhi_ext01"]),
    "六合": (["合者", "六合", "会合"], [RELATIONS_HOST_ID, "engine_ref.dizhi_ext02"]),
    "三合": (["会者", "三会", "三合"], [RELATIONS_HOST_ID, "engine_ref.dizhi_ext03"]),
    "刑": (["刑者", "三刑", "解刑"], [RELATIONS_HOST_ID, "engine_ref.dizhi_ext04"]),
    "害": (["害者", "六害", "害"], ["engine_ref.dizhi_ext05", RELATIONS_HOST_ID]),
}


@lru_cache(maxsize=1)
def _classics_by_id() -> dict[str, dict[str, Any]]:
    if not CLASSICS_PATH.exists():
        return {}
    raw = json.loads(CLASSICS_PATH.read_text(encoding="utf-8"))
    return {str(i["id"]): i for i in raw if isinstance(i, dict) and i.get("id")}


def _extract_around_anchor(passage: str, anchors: list[str], *, limit: int = 180) -> str:
    text = (passage or "").strip()
    if not text:
        return ""
    best_idx = -1
    for a in anchors:
        idx = text.find(a)
        if idx >= 0 and (best_idx < 0 or idx < best_idx):
            best_idx = idx
    if best_idx < 0:
        return text[:limit]
    start = max(0, best_idx - 4)
    chunk = text[start : start + limit]
    # 尽量落到句末
    for sep in ("。", "；", "！", "？"):
        pos = chunk.rfind(sep)
        if pos >= 40:
            return chunk[: pos + 1]
    return chunk


def pick_relations_verified_cites(
    relations_summary: dict[str, Any] | None,
    *,
    limit: int = 2,
) -> list[dict[str, str]]:
    """
    返回 [{id, title, passage}]，均已 is_verified_classic。
    """
    tags = relations_signal_tags(relations_summary)
    if not tags:
        tags = ["六冲", "六合"]
    by_id = _classics_by_id()
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for tag in tags:
        anchors, preferred_ids = SIGNAL_ANCHORS.get(tag, ([], [RELATIONS_HOST_ID]))
        for cid in preferred_ids:
            if cid in seen or not is_verified_classic(cid):
                continue
            item = by_id.get(cid)
            if not item:
                continue
            passage = _extract_around_anchor(str(item.get("passage") or ""), anchors)
            if len(passage.strip()) < 24:
                continue
            seen.add(cid)
            out.append(
                {
                    "id": cid,
                    "title": str(item.get("title") or cid),
                    "passage": passage.strip(),
                }
            )
            if len(out) >= limit:
                return out
    return out


def clear_relations_cite_caches() -> None:
    from services.content_policy import clear_verified_ids_cache

    _classics_by_id.cache_clear()
    clear_verified_ids_cache()
