"""Bazi explain section builders."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.explain import ExplainBlockModel, ExplainSectionResultModel
from services.chart_snapshot_service import BaziChartSnapshot
from services.classics_search import tfidf_score
from services.content_policy import is_verified_classic, sanitize_explain_block

ROOT = Path(__file__).resolve().parent.parent
MAX_SECTION_TEXT = 320

BAZI_SECTIONS = frozenset(
    {
        "geju",
        "yongshen",
        "relations",
        "dayun",
        "fortune",
        "domains",
        "summary",
        "reading",
    }
)

DOMAIN_KEYS = (
    ("wealth", "wealth_analysis", "财运"),
    ("career", "career", "事业"),
    ("marriage", "marriage_analysis", "婚恋"),
    ("health", "health", "健康"),
    ("personality", "personality", "性格"),
    ("relationship", "relationship", "人际"),
)


def _clip(text: str, limit: int = MAX_SECTION_TEXT) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    return f"{t[: limit - 1]}…"


def _block(text: str, layer: str = "fact", classic_id: str | None = None) -> ExplainBlockModel:
    raw = {"text": _clip(text), "layer": layer, "classic_id": classic_id}
    cleaned = sanitize_explain_block(raw)
    return ExplainBlockModel(**cleaned)


def _verified_classic_for_query(query: str, tags: list[str] | None = None) -> tuple[str | None, str | None]:
    path = ROOT / "data" / "classics.json"
    if not path.exists():
        return None, None
    raw_items = json.loads(path.read_text(encoding="utf-8"))
    verified_raw = [item for item in raw_items if item.get("verification_status") == "verified"]
    if not verified_raw:
        return None, None
    if tags:
        tagged = [item for item in verified_raw if any(t in (item.get("tags") or []) for t in tags)]
        pool = tagged or verified_raw
    else:
        pool = verified_raw
    docs = [(f"{item.get('title', '')} {item.get('passage', '')}", item) for item in pool[:120]]
    scored = tfidf_score(query, docs)
    if not scored or scored[0][0] <= 0:
        item = pool[0]
        cid = item["id"]
        return (cid, item["passage"]) if is_verified_classic(cid) else (None, None)
    best = scored[0][1]
    cid = best["id"]
    if not is_verified_classic(cid):
        return None, None
    return cid, best["passage"]


def _round_age(age: object) -> int | None:
    if age is None:
        return None
    try:
        return round(float(age))
    except (TypeError, ValueError):
        return None


def _dayun_end_age(items: list[object], index: int) -> int | None:
    if index >= len(items):
        return None
    current = items[index]
    start = _round_age(getattr(current, "start_age", None))
    if start is None:
        return None
    if index + 1 < len(items):
        nxt = _round_age(getattr(items[index + 1], "start_age", None))
        if nxt is not None:
            return nxt - 1
    return start + 9


def _format_dayun_age_range(start: object, end: object | None = None) -> str:
    start_num = _round_age(start)
    if start_num is None:
        return ""
    if end is not None:
        end_num = _round_age(end)
        if end_num is not None:
            return f"{start_num}–{end_num}岁"
    return f"{start_num}岁起"


def _bazi_dayun_explain_text(item: object, index: int, items: list[object]) -> str:
    gz = f"{getattr(item, 'stem', '')}{getattr(item, 'branch', '')}".strip() or "—"
    end_age = _dayun_end_age(items, index)
    start_age = getattr(item, "start_age", None)
    age_range = (
        _format_dayun_age_range(start_age, end_age)
        if start_age is not None and end_age is not None
        else _format_dayun_age_range(start_age)
    )
    start_year = getattr(item, "start_year", None)
    year_range = f"{start_year}–{int(start_year) + 9}年" if start_year is not None else ""
    ten_god = str(getattr(item, "ten_god", "") or "").strip()
    narrative = str(getattr(item, "narrative", "") or "").strip()
    hints = [
        str(getattr(item, key, "") or "").strip() for key in ("geju_impact", "wealth_hint", "health_hint", "love_hint")
    ]
    hints = [hint for hint in hints if hint]

    head = " · ".join(
        part
        for part in (
            f"{index + 1}. {gz}",
            age_range,
            year_range,
            f"十神 {ten_god}" if ten_god else "",
            f"纳音 {getattr(item, 'nayin', '')}" if getattr(item, "nayin", None) else "",
        )
        if part
    )
    if narrative and len(narrative) >= 20:
        return _clip(f"{head}。{narrative}")
    if hints:
        return _clip(f"{head}。{'；'.join(hints)}")
    if narrative:
        return _clip(f"{head}。{narrative}")
    return _clip(head)


def build_bazi_section(snapshot: BaziChartSnapshot, section_id: str) -> ExplainSectionResultModel:
    resp = snapshot.response
    blocks: list[ExplainBlockModel] = []

    if section_id == "geju":
        geju = resp.geju
        if geju:
            name = geju.geju_name or "待分析"
            blocks.append(_block(f"格局：{name}", "fact"))
            detail = geju.geju_detail or geju.interpretation_text or ""
            if detail:
                blocks.append(_block(detail, "fact"))
            classic_ref = (geju.classic_ref or "").strip()
            if classic_ref:
                cid, passage = _verified_classic_for_query(name, tags=["foundation", "overall"])
                if cid and passage:
                    blocks.append(_block(passage, "cite", classic_id=cid))
                elif classic_ref:
                    blocks.append(_block(classic_ref, "inference"))

    elif section_id == "yongshen":
        y = resp.yongshen
        if y:
            blocks.append(
                _block(
                    f"喜用：{'、'.join(y.favor or []) or '—'}；忌：{'、'.join(y.avoid or []) or '—'}",
                    "fact",
                )
            )

    elif section_id == "relations":
        rs = resp.relations_summary
        parts: list[str] = []
        if rs:
            for field in (rs.clash_summary, rs.combine_summary, rs.harm_summary, rs.interaction_summary):
                text = str(field or "").strip()
                if text:
                    parts.append(text)
            if rs.items:
                for item in rs.items[:6]:
                    summary = str(getattr(item, "summary", "") or "").strip()
                    if summary:
                        parts.append(summary)
                    else:
                        detail = str(getattr(item, "detail", "") or "").strip()
                        if detail:
                            parts.append(detail)
        if parts:
            body = "；".join(parts)
            if len(body) < 40:
                body = f"卷二干支关系摘要：{body}；合冲刑害以排盘事实为准，下接神煞与典籍讲解。"
            blocks.append(_block(body, "fact"))
        else:
            blocks.append(
                _block(
                    "卷二干支关系：暂无结构化摘要；请核对排盘事实层地支关系与天干冲合，再读推断层讲解。",
                    "fact",
                )
            )

    elif section_id == "dayun":
        items = (resp.dayun.items if resp.dayun else None) or (resp.dayun.cycles if resp.dayun else None) or []
        for index, item in enumerate(items[:6]):
            blocks.append(_block(_bazi_dayun_explain_text(item, index, items), "fact"))

    elif section_id == "fortune":
        ln = resp.liunian
        if ln and ln.items:
            for item in ln.items[:4]:
                blocks.append(_block(f"{item.year}年 {item.ganzhi or ''}".strip(), "fact"))
        else:
            blocks.append(_block("流年窗口见卷三事实层。", "fact"))

    elif section_id == "domains":
        for _key, attr, label in DOMAIN_KEYS:
            obj = getattr(resp, attr, None)
            if not obj:
                continue
            text = (
                getattr(obj, "development_advice", None)
                or getattr(obj, "strategy", None)
                or getattr(obj, "interpretation_text", None)
                or getattr(obj, "growth_advice", None)
                or ""
            )
            if text:
                blocks.append(_block(f"{label}：{_clip(str(text), 120)}", "inference"))

    elif section_id == "summary":
        if resp.bazi_summary:
            blocks.append(_block(resp.bazi_summary, "inference"))
        elif resp.geju and resp.geju.geju_name:
            blocks.append(_block(f"综合：{resp.geju.geju_name}。", "inference"))

    elif section_id == "reading":
        blocks.append(_block("先读卷一 fact（四柱格局），再读卷二关系，卷五推断默认折叠。", "fact"))
        cid, passage = _verified_classic_for_query("看命入式", tags=["foundation"])
        if cid and passage:
            blocks.append(_block(passage, "cite", classic_id=cid))

    if not blocks:
        blocks.append(_block("本节暂无讲解内容。", "fact"))

    has_verified_cite = any(b.layer == "cite" and b.classic_id for b in blocks)
    return ExplainSectionResultModel(
        section_id=section_id,
        blocks=blocks,
        verified=has_verified_cite,
    )
