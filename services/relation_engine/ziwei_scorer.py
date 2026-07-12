"""Ziwei palace-pair scoring by relation_type."""

from __future__ import annotations

from typing import Any

from services.ziwei_engine.compatibility import (
    _JU_TO_WX,
    _collect_conflicts,
    _collect_harmony,
    _is_chong,
    _is_liuhe,
    _is_sanhe,
    _wx_relation,
)
from services.ziwei_engine.tables import BRANCHES


def _palace_by_name(chart, name: str):
    for p in chart.palaces:
        if p.name == name:
            return p
    return None


def _branch_relation_tag(ai: int, bi: int) -> str:
    if _is_liuhe(ai, bi):
        return "六合"
    if _is_sanhe(ai, bi):
        return "三合"
    if ai == bi:
        return "同支"
    if _is_chong(ai, bi):
        return "相冲"
    return ""


def score_palace_pair(
    chart_a,
    chart_b,
    pair_spec: dict[str, Any],
    *,
    swap: bool = False,
) -> dict[str, Any]:
    ca, cb = (chart_b, chart_a) if swap else (chart_a, chart_b)
    a_name = pair_spec["a"]
    b_name = pair_spec["b"]
    pa = _palace_by_name(ca, a_name)
    pb = _palace_by_name(cb, b_name)
    pair_id = pair_spec.get("pair_id", f"{a_name}_{b_name}")
    if not pa or not pb:
        return {
            "pair_id": pair_id,
            "a_palace": a_name,
            "b_palace": b_name,
            "relation_tag": "缺失",
            "summary": f"宫位数据缺失（{a_name}↔{b_name}）",
            "layer": "fact",
            "score": 0,
            "max_score": 25,
        }
    rel = _branch_relation_tag(pa.branch_idx, pb.branch_idx)
    score_map = {"六合": 25, "三合": 20, "同支": 16, "相冲": 3, "": 12}
    score = score_map.get(rel, 12)
    stars_a = "/".join(s["name"] for s in pa.main_stars) or "空"
    stars_b = "/".join(s["name"] for s in pb.main_stars) or "空"
    summary = (
        f"{a_name}（{pa.stem}{pa.branch}·{stars_a}）↔"
        f"{b_name}（{pb.stem}{pb.branch}·{stars_b}）"
        f"{('·' + rel) if rel else ''}"
    )
    return {
        "pair_id": pair_id,
        "a_palace": a_name,
        "b_palace": b_name,
        "relation_tag": rel or "无特殊",
        "summary": summary[:300],
        "layer": "fact",
        "score": score,
        "max_score": 25,
    }


def score_life_palace(chart_a, chart_b, max_score: int = 25) -> dict[str, Any]:
    lb_a = chart_a.life_palace_branch
    lb_b = chart_b.life_palace_branch
    if _is_liuhe(lb_a, lb_b):
        s, d = max_score, f"命宫六合（{BRANCHES[lb_a]}、{BRANCHES[lb_b]}）"
    elif _is_sanhe(lb_a, lb_b):
        s, d = max_score * 0.8, f"命宫三合（{BRANCHES[lb_a]}、{BRANCHES[lb_b]}）"
    elif lb_a == lb_b:
        s, d = max_score * 0.64, f"命宫同支（{BRANCHES[lb_a]}）"
    elif _is_chong(lb_a, lb_b):
        s, d = max_score * 0.2, f"命宫相冲（{BRANCHES[lb_a]}冲{BRANCHES[lb_b]}）"
    else:
        s, d = max_score * 0.48, f"命宫无特殊合冲（{BRANCHES[lb_a]}、{BRANCHES[lb_b]}）"
    return {
        "id": "life_palace",
        "label": "命宫相合",
        "score": round(s, 1),
        "max_score": max_score,
        "description": d,
        "layer": "fact",
        "engine": "ziwei",
    }


def score_wuxing_ju(chart_a, chart_b, max_score: int = 20) -> dict[str, Any]:
    wx_a = _JU_TO_WX.get(chart_a.wuxing_ju, "土")
    wx_b = _JU_TO_WX.get(chart_b.wuxing_ju, "土")
    rel = _wx_relation(wx_a, wx_b)
    if rel == "相生":
        s = max_score
        d = f"{wx_a}与{wx_b}相生，互有助益"
    elif rel == "同":
        s = max_score * 0.65
        d = f"五行局同为{wx_a}，气场相近"
    elif rel == "相克":
        s = max_score * 0.4
        d = f"{wx_a}克{wx_b}或反之，需注意能量疏导"
    else:
        s = max_score * 0.65
        d = f"{wx_a}与{wx_b}无直接生克"
    return {
        "id": "wuxing_ju",
        "label": "五行局",
        "score": round(s, 1),
        "max_score": max_score,
        "description": d,
        "layer": "fact",
        "engine": "ziwei",
    }


def score_yin_yang(chart_a, chart_b, max_score: int = 15) -> dict[str, Any]:
    yy_a = chart_a.life_palace_stem_idx % 2
    yy_b = chart_b.life_palace_stem_idx % 2
    stem_a = chart_a.life_palace_gz[0]
    stem_b = chart_b.life_palace_gz[0]
    if yy_a != yy_b:
        s = max_score
        d = f"命宫天干阴阳互补（{stem_a}/{stem_b}）"
    else:
        s = max_score * 0.53
        label = "阳" if yy_a == 0 else "阴"
        d = f"命宫天干同为{label}（{stem_a}、{stem_b}）"
    return {
        "id": "yin_yang",
        "label": "阴阳互补",
        "score": round(s, 1),
        "max_score": max_score,
        "description": d,
        "layer": "fact",
        "engine": "ziwei",
    }


_ZIWEI_DIM_IDS = {
    "spouse_palace_hint",
    "peer_palace",
    "family_palace",
    "career_palace",
    "risk_palace",
    "hierarchy_palace",
}


def score_ziwei_dimensions(
    chart_a,
    chart_b,
    bazi_specs: list[dict[str, Any]],
    palace_pairs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ziwei_specs = [s for s in bazi_specs if s.get("engine") == "ziwei"]
    palace_cross: list[dict[str, Any]] = []
    for pspec in palace_pairs:
        if pspec.get("swap_roles"):
            cross = score_palace_pair(chart_a, chart_b, pspec, swap=True)
        else:
            cross = score_palace_pair(chart_a, chart_b, pspec)
        palace_cross.append({k: v for k, v in cross.items() if k not in ("score", "max_score")})

    dims: list[dict[str, Any]] = []
    for spec in ziwei_specs:
        dim_id = spec["id"]
        mx = spec.get("max", 25)
        if dim_id in _ZIWEI_DIM_IDS and palace_cross:
            avg = sum(
                p.get("score", 12)
                for p in [
                    score_palace_pair(chart_a, chart_b, ps, swap=bool(ps.get("swap_roles"))) for ps in palace_pairs[:2]
                ]
            ) / min(2, len(palace_pairs))
            dim = {
                "id": dim_id,
                "label": spec.get("label") or dim_id,
                "score": round(min(mx, avg * mx / 25), 1),
                "max_score": mx,
                "description": palace_cross[0]["summary"] if palace_cross else "宫位互涉",
                "layer": "fact",
                "engine": "ziwei",
                "weight": spec.get("weight", 0.2),
            }
        else:
            continue
        dims.append(dim)

    if not dims:
        for extra in (score_life_palace, score_wuxing_ju, score_yin_yang):
            d = extra(chart_a, chart_b)
            d["weight"] = 0.15
            dims.append(d)

    return dims, palace_cross


def collect_harmony_conflicts(chart_a, chart_b) -> tuple[list[str], list[str]]:
    return list(_collect_harmony(chart_a, chart_b)), list(_collect_conflicts(chart_a, chart_b))
