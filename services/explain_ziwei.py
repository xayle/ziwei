"""Ziwei explain section builders."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from app.schemas.explain import ExplainBlockModel, ExplainSectionResultModel
from services.chart_snapshot_service import ZiweiChartSnapshot
from services.content_policy import sanitize_explain_block
from services.ziwei_engine import PalaceInfo

ROOT = Path(__file__).resolve().parent.parent
ZIWEI_SECTIONS = frozenset({"palaces", "patterns", "fortune", "reading"})
MIN_PALACE_EXPLAIN_CHARS = 40


@lru_cache(maxsize=1)
def _star_profiles() -> dict[str, dict]:
    path = ROOT / "data" / "ziwei" / "star_profiles.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["key"]: item for item in data.get("stars", []) if item.get("key")}


def _clip(text: str, limit: int = 280) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    return f"{t[: limit - 1]}…"


def _block(text: str, layer: str = "fact", classic_id: str | None = None) -> ExplainBlockModel:
    raw = {"text": _clip(text), "layer": layer, "classic_id": classic_id}
    cleaned = sanitize_explain_block(raw)
    return ExplainBlockModel(**cleaned)


def _aux_star_names(palace: PalaceInfo) -> str:
    names: list[str] = []
    for star in palace.aux_stars:
        if isinstance(star, str):
            names.append(star)
        elif isinstance(star, dict):
            name = str(star.get("name") or "").strip()
            if name:
                names.append(name)
    return "、".join(names)


def _palace_explain_text(palace: PalaceInfo, profiles: dict[str, dict]) -> str:
    stars = "、".join(s["name"] for s in palace.main_stars) or "无主星"
    head = f"{palace.name} {palace.stem}{palace.branch}：主星 {stars}"
    narrative = (palace.conclusion or palace.analysis or palace.explanation or "").strip()
    if len(narrative) >= MIN_PALACE_EXPLAIN_CHARS:
        return _clip(f"{head}。{narrative}")

    parts = [head]
    aux = _aux_star_names(palace)
    if aux:
        parts.append(f"辅煞 {aux}")
    tags = "、".join(palace.analysis_tags[:3])
    if tags:
        parts.append(f"要点 {tags}")
    if palace.is_body_palace:
        parts.append("身宫所在")
    if not palace.main_stars:
        parts.append(f"对宫 {palace.opposition_name or '照命'}")

    for star in palace.main_stars[:2]:
        profile = profiles.get(star["name"])
        if profile and profile.get("key_points"):
            parts.append(profile["key_points"][0])
            break

    if narrative:
        parts.append(narrative)

    text = "；".join(parts)
    if len(text) < MIN_PALACE_EXPLAIN_CHARS and palace.suggestion:
        text = f"{text}；{palace.suggestion.strip()}"
    return _clip(text)


def _fortune_dayun_text(item: object, chart) -> str:
    branch_idx = getattr(item, "branch_idx", None)
    palace = next((p.name for p in chart.palaces if p.branch_idx == branch_idx), None)
    ganzhi = getattr(item, "ganzhi", "—")
    start_age = getattr(item, "start_age", None)
    end_age = getattr(item, "end_age", None)
    start_year = getattr(item, "start_year", None)
    index = getattr(item, "index", None)
    sihua = "、".join(f"{star}{trans}" for star, trans in (getattr(item, "sihua", None) or {}).items())

    parts = [
        f"第{index}限 {ganzhi}" if index is not None else f"大限 {ganzhi}",
        f"{start_age}–{end_age}岁" if start_age is not None and end_age is not None else "",
        (
            f"{start_year}–{int(start_year) + max(0, int(end_age) - int(start_age))}年"
            if start_year is not None and start_age is not None and end_age is not None
            else ""
        ),
        f"大限走{palace}" if palace else "",
        f"四化 {sihua}" if sihua else "",
    ]
    if palace:
        palace_info = next((p for p in chart.palaces if p.name == palace), None)
        if palace_info:
            snippet = (palace_info.conclusion or palace_info.analysis or "").strip()
            if snippet:
                parts.append(snippet[:100])
    return _clip(" · ".join(part for part in parts if part))


def build_ziwei_section(snapshot: ZiweiChartSnapshot, section_id: str) -> ExplainSectionResultModel:
    chart = snapshot.chart
    blocks: list[ExplainBlockModel] = []
    profiles = _star_profiles()

    if section_id == "palaces":
        for palace in chart.palaces:
            blocks.append(_block(_palace_explain_text(palace, profiles), "fact"))

    elif section_id == "patterns":
        for pat in (chart.patterns or [])[:4]:
            blocks.append(_block(f"{pat.name}（{pat.level or '—'}）", "fact"))
            if pat.description:
                blocks.append(_block(pat.description, "inference"))

    elif section_id == "fortune":
        if chart.dayun and chart.dayun.items:
            for item in chart.dayun.items[:6]:
                blocks.append(_block(_fortune_dayun_text(item, chart), "fact"))
        ln = chart.liunian
        if ln is not None:
            year = getattr(ln, "year", None)
            ganzhi = getattr(ln, "year_gz", None) or getattr(ln, "ganzhi", None)
            if year and ganzhi:
                blocks.append(_block(f"流年 {year} {ganzhi}，宜先核对卷三运限 fact 再读推断。", "fact"))
            items = getattr(ln, "items", None)
            if items:
                for item in items[:3]:
                    blocks.append(
                        _block(
                            f"流年 {getattr(item, 'year', '—')} {getattr(item, 'ganzhi', '—')}",
                            "fact",
                        )
                    )

    elif section_id == "reading":
        blocks.append(_block("先读卷四宫图 fact，运限见卷三；reference 星曜要点不标典籍。", "fact"))

    if not blocks:
        blocks.append(_block("本节暂无讲解内容。", "fact"))

    return ExplainSectionResultModel(section_id=section_id, blocks=blocks, verified=False)
