"""
四柱合婚算法（§5.1）— 基于天干地支生克与五行互补

评分维度（总分 100）：
  日主五行生克  40 分
  年支合冲      30 分
  五行互补      20 分
  天干合        10 分
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

# ── 五行基础数据 ─────────────────────────────────────────────────
STEM_ELEM: dict[str, str] = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth","己": "earth",
    "庚": "metal","辛": "metal",
    "壬": "water","癸": "water",
}

BRANCH_ELEM: dict[str, str] = {
    "子": "water", "丑": "earth", "寅": "wood",  "卯": "wood",
    "辰": "earth", "巳": "fire",  "午": "fire",  "未": "earth",
    "申": "metal", "酉": "metal", "戌": "earth", "亥": "water",
}

ELEM_CN: dict[str, str] = {
    "wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"
}

# 五行生克
_PRODUCES: dict[str, str] = {
    "wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"
}
_CONTROLS: dict[str, str] = {
    "wood": "earth", "earth": "water", "water": "fire", "fire": "metal", "metal": "wood"
}


def elem_relation(a: str, b: str) -> str:
    """返回 a 对 b 的关系: same/produces/controls/produced_by/controlled_by"""
    if a == b:                        return "same"
    if _PRODUCES.get(a) == b:         return "produces"
    if _CONTROLS.get(a) == b:         return "controls"
    if _PRODUCES.get(b) == a:         return "produced_by"
    if _CONTROLS.get(b) == a:         return "controlled_by"
    return "neutral"


# ── 地支六合 / 六冲 ─────────────────────────────────────────────
_SIX_HE: set[frozenset] = {
    frozenset({"子", "丑"}),
    frozenset({"寅", "亥"}),
    frozenset({"卯", "戌"}),
    frozenset({"辰", "酉"}),
    frozenset({"巳", "申"}),
    frozenset({"午", "未"}),
}

_SIX_CHONG: set[frozenset] = {
    frozenset({"子", "午"}),
    frozenset({"丑", "未"}),
    frozenset({"寅", "申"}),
    frozenset({"卯", "酉"}),
    frozenset({"辰", "戌"}),
    frozenset({"巳", "亥"}),
}

# 三合（水/木/火/金局）
_THREE_HE: list[frozenset] = [
    frozenset({"申", "子", "辰"}),  # 水局
    frozenset({"亥", "卯", "未"}),  # 木局
    frozenset({"寅", "午", "戌"}),  # 火局
    frozenset({"巳", "酉", "丑"}),  # 金局
]

# 天干五合
_STEM_HE: set[frozenset] = {
    frozenset({"甲", "己"}),
    frozenset({"乙", "庚"}),
    frozenset({"丙", "辛"}),
    frozenset({"丁", "壬"}),
    frozenset({"戊", "癸"}),
}

# 天干相冲（相克且互克）
_STEM_CHONG: set[frozenset] = {
    frozenset({"甲", "庚"}),
    frozenset({"乙", "辛"}),
    frozenset({"丙", "壬"}),
    frozenset({"丁", "癸"}),
}


# ── 获取八字四柱（精简版，仅用于合婚） ─────────────────────────
def _get_pillars(dt_local: datetime, lon: float, tz: str) -> dict[str, Any]:
    """
    返回 {"year": {"stem": ..., "branch": ...}, "month": ..., "day": ..., "hour": ...}
    加上五行权重 dict。
    使用 verify_full（与主八字引擎一致）。
    """
    from zoneinfo import ZoneInfo

    from services.bazi_full_service import BRANCH_ELEMENT as _BE
    from services.bazi_full_service import STEM_META
    from verify import verify_full

    zi = ZoneInfo(tz)
    local_aware = dt_local if dt_local.tzinfo is not None else dt_local.replace(tzinfo=zi)
    local_aware = local_aware.astimezone(zi)
    # verify_full 现要求传入 timezone-aware 的本地时间。
    result = verify_full(local_aware, lon=lon, use_solar=True, mode="single")
    p = result.pillars_primary

    pillars = {
        "year":  {"stem": p.year.stem,  "branch": p.year.branch},
        "month": {"stem": p.month.stem, "branch": p.month.branch},
        "day":   {"stem": p.day.stem,   "branch": p.day.branch},
        "hour":  {"stem": p.hour.stem,  "branch": p.hour.branch},
    }

    # 五行权重（天干+地支各1点，藏干不计）
    weights: dict[str, float] = {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0}
    for col in pillars.values():
        if col["stem"] in STEM_META:
            elem, _ = STEM_META[col["stem"]]
            weights[elem] += 1.0
        be = _BE or BRANCH_ELEM
        if col["branch"] in be:
            weights[be[col["branch"]]] += 1.0

    return {"pillars": pillars, "weights": weights}


# ── 核心评分 ─────────────────────────────────────────────────────
def compute_compatibility(
    a_dt: datetime, a_lon: float, a_tz: str,
    b_dt: datetime, b_lon: float, b_tz: str,
) -> dict[str, Any]:
    """
    四柱合婚综合评分。

    参数
    ----
    a_dt, b_dt : 本地 datetime（允许 naive；内部会按时区补齐）
    a_lon, b_lon : 经度
    a_tz, b_tz   : IANA 时区

    返回
    ----
    {
      score: int,          # 0-100
      grade: str,          # 上上 / 上 / 中 / 下 / 下下
      summary: str,
      details: [...],
      person_a: {pillars, weights},
      person_b: {pillars, weights},
    }
    """
    a = _get_pillars(a_dt, a_lon, a_tz)
    b = _get_pillars(b_dt, b_lon, b_tz)

    ap = a["pillars"]
    bp = b["pillars"]
    aw = a["weights"]
    bw = b["weights"]

    details: list[dict[str, Any]] = []
    total = 0

    # ── 1. 日主五行生克（40分） ─────────────────────────────────
    a_day_elem = STEM_ELEM.get(ap["day"]["stem"], "")
    b_day_elem = STEM_ELEM.get(bp["day"]["stem"], "")
    rel = elem_relation(a_day_elem, b_day_elem) if a_day_elem and b_day_elem else "neutral"
    day_score = {"same": 30, "produces": 40, "produced_by": 35, "controls": 15, "controlled_by": 15, "neutral": 20}.get(rel, 20)
    rel_cn = {
        "same":          f"同为{ELEM_CN.get(a_day_elem,'?')}，比和",
        "produces":      f"{ELEM_CN.get(a_day_elem,'?')}生{ELEM_CN.get(b_day_elem,'?')}",
        "produced_by":   f"{ELEM_CN.get(b_day_elem,'?')}生{ELEM_CN.get(a_day_elem,'?')}",
        "controls":      f"{ELEM_CN.get(a_day_elem,'?')}克{ELEM_CN.get(b_day_elem,'?')}",
        "controlled_by": f"{ELEM_CN.get(b_day_elem,'?')}克{ELEM_CN.get(a_day_elem,'?')}",
        "neutral":       "五行中性",
    }.get(rel, "")
    total += day_score
    details.append({
        "dimension": "日主五行",
        "score": day_score, "max": 40,
        "description": f"甲方日干 {ap['day']['stem']}（{ELEM_CN.get(a_day_elem,'?')}）× 乙方日干 {bp['day']['stem']}（{ELEM_CN.get(b_day_elem,'?')}）— {rel_cn}",
        "level": "佳" if day_score >= 35 else ("中" if day_score >= 25 else "差"),
    })

    # ── 2. 年支合冲（30分） ─────────────────────────────────────
    ay = ap["year"]["branch"]
    by_ = bp["year"]["branch"]
    pair = frozenset({ay, by_})
    branch_score = 0
    branch_note = ""
    if pair in _SIX_HE:
        branch_score = 30
        branch_note = f"年支六合（{ay}{by_}合）"
    elif any(pair <= s for s in _THREE_HE):
        branch_score = 22
        branch_note = f"年支三合（{ay}{by_}）"
    elif pair in _SIX_CHONG:
        branch_score = 0
        branch_note = f"年支六冲（{ay}{by_}冲）⚠ 需调和"
    else:
        branch_score = 15
        branch_note = f"年支无特殊关系（{ay} / {by_}）"
    total += branch_score
    details.append({
        "dimension": "年支合冲",
        "score": branch_score, "max": 30,
        "description": branch_note,
        "level": "佳" if branch_score >= 25 else ("中" if branch_score >= 12 else "差"),
    })

    # ── 3. 五行互补（20分） ──────────────────────────────────────
    # 衡量：乙方五行能否填补甲方的五行缺口
    elems = ["wood", "fire", "earth", "metal", "water"]
    total_a = sum(aw.values()) or 1
    total_b = sum(bw.values()) or 1
    # 各元素占比
    na = {e: aw[e] / total_a for e in elems}
    nb = {e: bw[e] / total_b for e in elems}
    # 互补度：缺口越大且对方越强越好
    complement_score = 0.0
    for e in elems:
        gap_a = max(0.0, 0.2 - na[e])   # 甲方缺口（均衡基准 20%）
        fill  = nb[e]                     # 乙方填补
        complement_score += gap_a * fill
        gap_b = max(0.0, 0.2 - nb[e])
        fill2 = na[e]
        complement_score += gap_b * fill2
    comp_norm = min(20.0, complement_score * 100)
    total += comp_norm
    # 找出甲方最弱元素
    weakest_a = min(aw, key=aw.get)
    weakest_b = min(bw, key=bw.get)
    details.append({
        "dimension": "五行互补",
        "score": round(comp_norm, 1), "max": 20,
        "description": (
            f"甲方最弱：{ELEM_CN[weakest_a]}（{aw[weakest_a]:.0f}%），"
            f"乙方最弱：{ELEM_CN[weakest_b]}（{bw[weakest_b]:.0f}%）"
        ),
        "level": "佳" if comp_norm >= 14 else ("中" if comp_norm >= 7 else "差"),
    })

    # ── 4. 天干合（10分） ───────────────────────────────────────
    stems_a = {ap[col]["stem"] for col in ("year", "month", "day", "hour")}
    stems_b = {bp[col]["stem"] for col in ("year", "month", "day", "hour")}
    he_pairs = [
        f"{list(p)[0]}{list(p)[1]}合"
        for p in _STEM_HE
        if p & stems_a and p & stems_b
    ]
    chong_pairs = [
        f"{list(p)[0]}{list(p)[1]}冲"
        for p in _STEM_CHONG
        if p & stems_a and p & stems_b
    ]
    stem_score = min(10, len(he_pairs) * 5) - len(chong_pairs) * 3
    stem_score = max(0, stem_score)
    total += stem_score
    stem_note = (", ".join(he_pairs) if he_pairs else "无天干合") + (
        "；" + ", ".join(chong_pairs) if chong_pairs else ""
    )
    details.append({
        "dimension": "天干合化",
        "score": stem_score, "max": 10,
        "description": stem_note,
        "level": "佳" if stem_score >= 7 else ("中" if stem_score >= 3 else "差"),
    })

    final_score = round(total)
    if   final_score >= 85: grade = "上上"
    elif final_score >= 70: grade = "上"
    elif final_score >= 50: grade = "中"
    elif final_score >= 30: grade = "下"
    else:                   grade = "下下"

    summaries = {
        "上上": "天生一对，五行相辅，年支相合，是难得的良配。",
        "上":   "整体搭配良好，略有磨合，相互扶持则感情稳固。",
        "中":   "五行各有长短，需要多沟通包容，婚后共同努力可白头。",
        "下":   "五行冲克明显，建议选择吉日化解，多采用调和方案。",
        "下下": "冲克严重，年支相冲，相处需特别谨慎，建议择日择地化解。",
    }

    return {
        "score":    final_score,
        "grade":    grade,
        "summary":  summaries[grade],
        "details":  details,
        "person_a": {
            "pillars": ap,
            "weights": {k: round(v / (sum(aw.values()) or 1) * 100, 1) for k, v in aw.items()},
            "day_stem": ap["day"]["stem"],
            "day_elem": a_day_elem,
        },
        "person_b": {
            "pillars": bp,
            "weights": {k: round(v / (sum(bw.values()) or 1) * 100, 1) for k, v in bw.items()},
            "day_stem": bp["day"]["stem"],
            "day_elem": b_day_elem,
        },
    }
