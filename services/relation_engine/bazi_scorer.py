"""Bazi dimension scoring for relation compatibility."""

from __future__ import annotations

from typing import Any

from services.compatibility import (
    _SIX_CHONG,
    _SIX_HE,
    _STEM_CHONG,
    _STEM_HE,
    _THREE_HE,
    ELEM_CN,
    STEM_ELEM,
    _get_pillars,
    elem_relation,
)
from services.relation_engine.registry import get_day_branch_rules, get_year_branch_same_score

# 六害
_SIX_HAI: set[frozenset] = {
    frozenset({"子", "未"}),
    frozenset({"丑", "午"}),
    frozenset({"寅", "巳"}),
    frozenset({"卯", "辰"}),
    frozenset({"申", "亥"}),
    frozenset({"酉", "戌"}),
}

# 相刑（简化）
_XING: set[frozenset] = {
    frozenset({"子", "卯"}),
    frozenset({"寅", "巳"}),
    frozenset({"巳", "申"}),
    frozenset({"申", "寅"}),
    frozenset({"丑", "戌"}),
    frozenset({"戌", "未"}),
    frozenset({"未", "丑"}),
    frozenset({"辰"}),
    frozenset({"午"}),
    frozenset({"酉"}),
    frozenset({"亥"}),
}


def _branch_relation(a: str, b: str) -> str:
    if a == b:
        return "same"
    pair = frozenset({a, b})
    if pair in _SIX_HE:
        return "liuhe"
    if pair in _SIX_CHONG:
        return "chong"
    if pair in _SIX_HAI:
        return "hai"
    if pair in _XING or frozenset({a, b}) in _XING:
        return "xing"
    if any(pair <= s for s in _THREE_HE):
        return "sanhe"
    return "none"


def _score_branch(a: str, b: str, max_score: int, rules: dict[str, Any]) -> tuple[float, str, bool]:
    rel = _branch_relation(a, b)
    rule = rules.get(rel) or rules.get("none") or {"score": 15, "tag": "无特殊"}
    base = float(rule.get("score", 15))
    scale = max_score / 30.0 if max_score else 1.0
    score = min(float(max_score), base * scale)
    tag = rule.get("tag", rel)
    flag = bool(rule.get("flag_conflict"))
    desc = f"日支{tag}（{a}{b}）" if rel != "none" else f"日支无特殊关系（{a} / {b}）"
    if rel == "chong":
        desc += " ⚠ 需主动调和"
    return score, desc, flag


def score_day_master(ap: dict, bp: dict, max_score: int = 40) -> dict[str, Any]:
    a_elem = STEM_ELEM.get(ap["day"]["stem"], "")
    b_elem = STEM_ELEM.get(bp["day"]["stem"], "")
    rel = elem_relation(a_elem, b_elem) if a_elem and b_elem else "neutral"
    raw = {"same": 30, "produces": 40, "produced_by": 35, "controls": 15, "controlled_by": 15, "neutral": 20}.get(
        rel, 20
    )
    score = min(max_score, raw * max_score / 40.0)
    rel_cn = {
        "same": f"同为{ELEM_CN.get(a_elem, '?')}，比和",
        "produces": f"{ELEM_CN.get(a_elem, '?')}生{ELEM_CN.get(b_elem, '?')}",
        "produced_by": f"{ELEM_CN.get(b_elem, '?')}生{ELEM_CN.get(a_elem, '?')}",
        "controls": f"{ELEM_CN.get(a_elem, '?')}克{ELEM_CN.get(b_elem, '?')}",
        "controlled_by": f"{ELEM_CN.get(b_elem, '?')}克{ELEM_CN.get(a_elem, '?')}",
        "neutral": "五行中性",
    }.get(rel, "")
    return {
        "id": "day_master",
        "label": "日主五行",
        "score": round(score, 1),
        "max_score": max_score,
        "description": (
            f"甲日干 {ap['day']['stem']}（{ELEM_CN.get(a_elem, '?')}）× "
            f"乙日干 {bp['day']['stem']}（{ELEM_CN.get(b_elem, '?')}）— {rel_cn}"
        ),
        "layer": "fact",
        "engine": "bazi",
    }


def score_day_branch(ap: dict, bp: dict, max_score: int = 30) -> dict[str, Any]:
    rules = get_day_branch_rules()
    ay, by = ap["day"]["branch"], bp["day"]["branch"]
    score, desc, _ = _score_branch(ay, by, max_score, rules)
    return {
        "id": "day_branch",
        "label": "日支合冲",
        "score": round(score, 1),
        "max_score": max_score,
        "description": desc,
        "layer": "fact",
        "engine": "bazi",
    }


def score_year_branch(ap: dict, bp: dict, max_score: int = 30) -> dict[str, Any]:
    ay, by = ap["year"]["branch"], bp["year"]["branch"]
    pair = frozenset({ay, by})
    if ay == by:
        score = min(max_score, get_year_branch_same_score() * max_score / 30.0)
        desc = f"年支同支（{ay}年），背景相似"
    elif pair in _SIX_HE:
        score = max_score
        desc = f"年支六合（{ay}{by}合）"
    elif pair in _SIX_CHONG:
        score = 0
        desc = f"年支六冲（{ay}{by}冲）⚠"
    elif any(pair <= s for s in _THREE_HE):
        score = max_score * 22 / 30
        desc = f"年支三合（{ay}{by}）"
    else:
        score = max_score * 15 / 30
        desc = f"年支无特殊关系（{ay} / {by}）"
    return {
        "id": "year_branch",
        "label": "年支合冲",
        "score": round(score, 1),
        "max_score": max_score,
        "description": desc,
        "layer": "fact",
        "engine": "bazi",
    }


def score_wuxing_complement(aw: dict, bw: dict, max_score: int = 20) -> dict[str, Any]:
    elems = ["wood", "fire", "earth", "metal", "water"]
    total_a = sum(aw.values()) or 1
    total_b = sum(bw.values()) or 1
    na = {e: aw[e] / total_a for e in elems}
    nb = {e: bw[e] / total_b for e in elems}
    complement_score = 0.0
    for e in elems:
        gap_a = max(0.0, 0.2 - na[e])
        complement_score += gap_a * nb[e]
        gap_b = max(0.0, 0.2 - nb[e])
        complement_score += gap_b * na[e]
    comp_norm = min(float(max_score), complement_score * 100 * max_score / 20.0)
    weakest_a = min(aw, key=aw.get)
    weakest_b = min(bw, key=bw.get)
    return {
        "id": "wuxing_complement",
        "label": "五行互补",
        "score": round(comp_norm, 1),
        "max_score": max_score,
        "description": (f"甲方最弱：{ELEM_CN[weakest_a]}；乙方最弱：{ELEM_CN[weakest_b]}"),
        "layer": "fact",
        "engine": "bazi",
    }


def score_stem_interaction(ap: dict, bp: dict, max_score: int = 10) -> dict[str, Any]:
    stems_a = {ap[col]["stem"] for col in ("year", "month", "day", "hour")}
    stems_b = {bp[col]["stem"] for col in ("year", "month", "day", "hour")}
    he_pairs = [f"{next(iter(p))}{list(p)[1]}合" for p in _STEM_HE if p & stems_a and p & stems_b]
    chong_pairs = [f"{next(iter(p))}{list(p)[1]}冲" for p in _STEM_CHONG if p & stems_a and p & stems_b]
    stem_score = min(max_score, len(he_pairs) * (max_score / 2) - len(chong_pairs) * (max_score / 3))
    stem_score = max(0.0, stem_score)
    stem_note = (", ".join(he_pairs) if he_pairs else "无天干合") + (
        "；" + ", ".join(chong_pairs) if chong_pairs else ""
    )
    return {
        "id": "stem_interaction",
        "label": "天干合化",
        "score": round(stem_score, 1),
        "max_score": max_score,
        "description": stem_note,
        "layer": "fact",
        "engine": "bazi",
    }


def score_yongshen_cross(
    favor_a: list[str],
    avoid_a: list[str],
    favor_b: list[str],
    avoid_b: list[str],
    max_score: int = 20,
) -> dict[str, Any]:
    score = float(max_score) * 0.5
    notes: list[str] = []
    shared_favor = set(favor_a) & set(favor_b)
    if shared_favor:
        score += max_score * 0.25
        notes.append(f"喜用重叠：{', '.join(shared_favor)}")
    clash = (set(favor_a) & set(avoid_b)) | (set(favor_b) & set(avoid_a))
    if clash:
        score -= max_score * 0.2
        notes.append(f"喜忌对冲：{', '.join(clash)}")
    score = max(0.0, min(float(max_score), score))
    desc = "；".join(notes) if notes else "喜忌交叉中性"
    return {
        "id": "yongshen_cross",
        "label": "喜忌交叉",
        "score": round(score, 1),
        "max_score": max_score,
        "description": desc,
        "layer": "fact",
        "engine": "bazi",
    }


def score_ten_god_cross(max_score: int = 20) -> dict[str, Any]:
    return {
        "id": "ten_god_cross",
        "label": "十神交叉",
        "score": round(max_score * 0.6, 1),
        "max_score": max_score,
        "description": "十神层级互补（heuristic）",
        "layer": "inference",
        "engine": "bazi",
    }


def score_wealth_cross(max_score: int = 25) -> dict[str, Any]:
    return {
        "id": "wealth_cross",
        "label": "财层交叉",
        "score": round(max_score * 0.55, 1),
        "max_score": max_score,
        "description": "财星与合伙资源互补（heuristic）",
        "layer": "inference",
        "engine": "bazi",
    }


def score_official_kill_cross(max_score: int = 25) -> dict[str, Any]:
    return {
        "id": "official_kill_cross",
        "label": "官杀交叉",
        "score": round(max_score * 0.58, 1),
        "max_score": max_score,
        "description": "上下级权责气场（heuristic）",
        "layer": "inference",
        "engine": "bazi",
    }


_BAZI_SCORERS = {
    "day_master": lambda ctx, spec: score_day_master(ctx["ap"], ctx["bp"], spec["max"]),
    "day_branch": lambda ctx, spec: score_day_branch(ctx["ap"], ctx["bp"], spec["max"]),
    "year_branch": lambda ctx, spec: score_year_branch(ctx["ap"], ctx["bp"], spec["max"]),
    "wuxing_complement": lambda ctx, spec: score_wuxing_complement(ctx["aw"], ctx["bw"], spec["max"]),
    "stem_interaction": lambda ctx, spec: score_stem_interaction(ctx["ap"], ctx["bp"], spec["max"]),
    "yongshen_cross": lambda ctx, spec: score_yongshen_cross(
        ctx.get("favor_a", []),
        ctx.get("avoid_a", []),
        ctx.get("favor_b", []),
        ctx.get("avoid_b", []),
        spec["max"],
    ),
    "ten_god_cross": lambda ctx, spec: score_ten_god_cross(spec["max"]),
    "wealth_cross": lambda ctx, spec: score_wealth_cross(spec["max"]),
    "official_kill_cross": lambda ctx, spec: score_official_kill_cross(spec["max"]),
}


def score_bazi_dimensions(
    a_data: dict[str, Any],
    b_data: dict[str, Any],
    bazi_specs: list[dict[str, Any]],
    *,
    favor_a: list[str] | None = None,
    avoid_a: list[str] | None = None,
    favor_b: list[str] | None = None,
    avoid_b: list[str] | None = None,
) -> list[dict[str, Any]]:
    ap = a_data["pillars"]
    bp = b_data["pillars"]
    ctx = {
        "ap": ap,
        "bp": bp,
        "aw": a_data["weights"],
        "bw": b_data["weights"],
        "favor_a": favor_a or [],
        "avoid_a": avoid_a or [],
        "favor_b": favor_b or [],
        "avoid_b": avoid_b or [],
    }
    dims: list[dict[str, Any]] = []
    for spec in bazi_specs:
        if spec.get("engine") == "ziwei":
            continue
        dim_id = spec["id"]
        scorer = _BAZI_SCORERS.get(dim_id)
        if scorer is None:
            continue
        dim = scorer(ctx, spec)
        dim["weight"] = spec.get("weight", 0.1)
        dims.append(dim)
    return dims


def load_pillar_data(dt_local, lon: float, tz: str) -> dict[str, Any]:
    return _get_pillars(dt_local, lon, tz)
