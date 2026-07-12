"""Ziwei explain section builders."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from app.schemas.explain import ExplainBlockModel, ExplainSectionResultModel
from services.chart_snapshot_service import ZiweiChartSnapshot
from services.content_policy import sanitize_explain_block

ROOT = Path(__file__).resolve().parent.parent
ZIWEI_SECTIONS = frozenset({"palaces", "patterns", "fortune", "reading"})


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


def build_ziwei_section(snapshot: ZiweiChartSnapshot, section_id: str) -> ExplainSectionResultModel:
    chart = snapshot.chart
    blocks: list[ExplainBlockModel] = []
    profiles = _star_profiles()

    if section_id == "palaces":
        life = next((p for p in chart.palaces if p.name == "命宫"), None)
        if life:
            stars = "、".join(s["name"] for s in life.main_stars) or "无主星"
            blocks.append(_block(f"命宫 {life.branch}：{stars}", "fact"))
            for s in life.main_stars[:2]:
                prof = profiles.get(s["name"])
                if prof and prof.get("key_points"):
                    blocks.append(_block(prof["key_points"][0], "inference"))
        for p in chart.palaces[:4]:
            if p.name == "命宫":
                continue
            stars = "、".join(s["name"] for s in p.main_stars) or "无主星"
            blocks.append(_block(f"{p.name}：{stars}", "fact"))

    elif section_id == "patterns":
        for pat in (chart.patterns or [])[:4]:
            blocks.append(_block(f"{pat.name}（{pat.level or '—'}）", "fact"))
            if pat.description:
                blocks.append(_block(pat.description, "inference"))

    elif section_id == "fortune":
        if chart.dayun and chart.dayun.items:
            for item in chart.dayun.items[:5]:
                label = getattr(item, "palace_name", None) or getattr(item, "ganzhi", "—")
                blocks.append(_block(f"大限 {item.start_age}–{item.end_age}岁 {label}", "fact"))
        ln = chart.liunian
        if ln is not None:
            year = getattr(ln, "year", None)
            ganzhi = getattr(ln, "year_gz", None) or getattr(ln, "ganzhi", None)
            if year and ganzhi:
                blocks.append(_block(f"流年 {year} {ganzhi}", "fact"))
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
