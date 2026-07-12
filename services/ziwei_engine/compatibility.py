"""
services/ziwei_engine/compatibility.py — 紫微斗数合盘六合度分析

算法维度（合计 100 分）：
  1. 命宫地支相合  25分  六合/三合/冲/同支/无关
  2. 五行相生      20分  两人五行局的相生/相克/同/无关
  3. 年支缘分      20分  年支六合/三合/冲/同支/无关
  4. 夫妻宫缘      20分  甲方夫妻宫 与 乙方命宫的地支/主星关系
  5. 阴阳互补      15分  命宫天干阴阳是否互补

公开接口：
  from .compatibility import calc_compatibility, CompatibilityResult
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tables import BRANCHES

# ──────────────────────────────────────────────────────────────
# 地支关系常量
# ──────────────────────────────────────────────────────────────

# 六合对：子丑 寅亥 卯戌 辰酉 巳申 午未
_LIUHE: list[frozenset] = [
    frozenset({0, 1}),
    frozenset({2, 11}),
    frozenset({3, 10}),
    frozenset({4, 9}),
    frozenset({5, 8}),
    frozenset({6, 7}),
]

# 三合局：申子辰 寅午戌 亥卯未 巳酉丑
_SANHE: list[frozenset] = [
    frozenset({8, 0, 4}),
    frozenset({2, 6, 10}),
    frozenset({11, 3, 7}),
    frozenset({5, 9, 1}),
]

# 六冲对：子午 丑未 寅申 卯酉 辰戌 巳亥
_CHONG: list[frozenset] = [
    frozenset({0, 6}),
    frozenset({1, 7}),
    frozenset({2, 8}),
    frozenset({3, 9}),
    frozenset({4, 10}),
    frozenset({5, 11}),
]


def _is_liuhe(a: int, b: int) -> bool:
    return frozenset({a, b}) in _LIUHE


def _is_sanhe(a: int, b: int) -> bool:
    return any(a in g and b in g for g in _SANHE)


def _is_chong(a: int, b: int) -> bool:
    return frozenset({a, b}) in _CHONG


# ──────────────────────────────────────────────────────────────
# 五行关系
# ──────────────────────────────────────────────────────────────

# 五行局数 → 五行
_JU_TO_WX: dict[int, str] = {2: "水", 3: "木", 4: "金", 5: "土", 6: "火"}

# 相生（我生者）: 水生木 木生火 火生土 土生金 金生水
_WX_SHENG: dict[str, str] = {"水": "木", "木": "火", "火": "土", "土": "金", "金": "水"}

# 相克（我克者）: 水克火 火克金 金克木 木克土 土克水
_WX_KE: dict[str, str] = {"水": "火", "火": "金", "金": "木", "木": "土", "土": "水"}


def _wx_relation(wx_a: str, wx_b: str) -> str:
    """返回 a 与 b 的关系字符串。"""
    if wx_a == wx_b:
        return "同"
    if _WX_SHENG.get(wx_a) == wx_b or _WX_SHENG.get(wx_b) == wx_a:
        return "相生"
    if _WX_KE.get(wx_a) == wx_b or _WX_KE.get(wx_b) == wx_a:
        return "相克"
    return "无关"


# ──────────────────────────────────────────────────────────────
# 数据结构
# ──────────────────────────────────────────────────────────────


@dataclass
class CompatibilityDimension:
    name: str
    score: int
    max_score: int
    description: str


@dataclass
class CompatibilityResult:
    total_score: int
    max_score: int
    level: str  # "上上签" / "上签" / "中签" / "下签" / "平"
    summary: str
    dimensions: list[CompatibilityDimension] = field(default_factory=list)
    person_a_info: dict = field(default_factory=dict)
    person_b_info: dict = field(default_factory=dict)
    harmony_points: list[str] = field(default_factory=list)
    conflict_points: list[str] = field(default_factory=list)
    complement_points: list[str] = field(default_factory=list)
    palace_compare: list[dict] = field(default_factory=list)
    disclaimer: str = "合盘分析基于规则化 heuristic 模型，仅供参考，不构成决策依据。"
    layer: str = "heuristic"


# ──────────────────────────────────────────────────────────────
# 主分析函数
# ──────────────────────────────────────────────────────────────


def calc_compatibility(chart_a, chart_b) -> CompatibilityResult:
    """
    计算两人紫微命盘的六合度。

    参数
    ----
    chart_a, chart_b : ZiweiChart
        两人完整命盘（由 ziwei_full() 返回）。

    返回
    ----
    CompatibilityResult
        综合得分、等级评定、各维度分析。
    """
    dims: list[CompatibilityDimension] = []

    lb_a = chart_a.life_palace_branch  # 甲方命宫地支索引
    lb_b = chart_b.life_palace_branch  # 乙方命宫地支索引

    # ── 维度 1：命宫地支相合（25 分）────────────────────────
    if _is_liuhe(lb_a, lb_b):
        s1 = 25
        d1 = f"两人命宫地支六合（{BRANCHES[lb_a]}、{BRANCHES[lb_b]}），天作之合，相处融洽，默契天然。"
    elif _is_sanhe(lb_a, lb_b):
        s1 = 20
        d1 = f"两人命宫地支三合（{BRANCHES[lb_a]}、{BRANCHES[lb_b]}），缘分深厚，志向相合，携手并进。"
    elif lb_a == lb_b:
        s1 = 16
        d1 = f"两人命宫同支（{BRANCHES[lb_a]}），同类相遇，价值观高度一致，但也易有竞争感。"
    elif _is_chong(lb_a, lb_b):
        s1 = 5
        d1 = f"两人命宫地支相冲（{BRANCHES[lb_a]}冲{BRANCHES[lb_b]}），个性差异较大，易生矛盾，需多包容。"
    else:
        s1 = 12
        d1 = f"两人命宫地支（{BRANCHES[lb_a]}、{BRANCHES[lb_b]}）无特殊合冲，相处平稳，缘分温和。"
    dims.append(CompatibilityDimension("命宫相合", s1, 25, d1))

    # ── 维度 2：五行相生（20 分）────────────────────────────
    wx_a = _JU_TO_WX.get(chart_a.wuxing_ju, "土")
    wx_b = _JU_TO_WX.get(chart_b.wuxing_ju, "土")
    rel = _wx_relation(wx_a, wx_b)
    if rel == "相生":
        s2 = 20
        if _WX_SHENG.get(wx_a) == wx_b:
            d2 = f"{wx_a}生{wx_b}，甲方滋养乙方，相辅相成，互有助力。"
        else:
            d2 = f"{wx_b}生{wx_a}，乙方滋养甲方，相辅相成，互有助力。"
    elif rel == "同":
        s2 = 13
        d2 = f"两人五行局同为{wx_a}，气场相近，理解容易，惟竞争感明显。"
    elif rel == "相克":
        s2 = 8
        if _WX_KE.get(wx_a) == wx_b:
            d2 = f"{wx_a}克{wx_b}，甲方气势较强，需注意避免压迫感。"
        else:
            d2 = f"{wx_b}克{wx_a}，乙方气势较强，甲方宜坚持自我。"
    else:
        s2 = 13
        d2 = f"{wx_a}与{wx_b}五行无直接生克，相处中性平和。"
    dims.append(CompatibilityDimension("五行相生", s2, 20, d2))

    # ── 维度 3：年支缘分（20 分）────────────────────────────
    yb_a = chart_a.lunar.year_branch_idx
    yb_b = chart_b.lunar.year_branch_idx
    if yb_a == yb_b:
        s3 = 12
        d3 = f"同生肖（{BRANCHES[yb_a]}年），背景相似有共鸣"
    elif _is_liuhe(yb_a, yb_b):
        s3 = 20
        d3 = f"两人年支六合（{BRANCHES[yb_a]}年、{BRANCHES[yb_b]}年），生肖天作一对，情投意合，缘份深。"
    elif _is_sanhe(yb_a, yb_b):
        s3 = 16
        d3 = f"生肖三合（{BRANCHES[yb_a]}、{BRANCHES[yb_b]}），志趣相投，合作顺畅。"
    elif _is_chong(yb_a, yb_b):
        s3 = 4
        d3 = f"年支相冲（{BRANCHES[yb_a]}与{BRANCHES[yb_b]}），生肖相克，易有明争暗斗，需耐心沟通。"
    else:
        s3 = 10
        d3 = f"年支（{BRANCHES[yb_a]}、{BRANCHES[yb_b]}）无特殊关系，相处平稳。"
    dims.append(CompatibilityDimension("年支缘分", s3, 20, d3))

    # ── 维度 4：夫妻宫缘（20 分）────────────────────────────
    pnames_a = {p.name: p for p in chart_a.palaces}
    hus_a = pnames_a.get("夫妻宫")
    life_b_pal = next((p for p in chart_b.palaces if p.name == "命宫"), None)

    s4 = 10
    d4 = "夫妻宫与对方命宫无特殊互动关系。"
    if hus_a and life_b_pal:
        hus_stars = {s["name"] for s in hus_a.main_stars}
        life_b_stars = {s["name"] for s in life_b_pal.main_stars}
        common_stars = hus_stars & life_b_stars
        if common_stars:
            s4 = 20
            d4 = f"甲方夫妻宫主星（{'/'.join(common_stars)}）正是乙方命宫之星，情缘天定，婚缘深厚，相遇即是归途。"
        elif hus_a.branch_idx == lb_b:
            s4 = 18
            d4 = "甲方夫妻宫地支与乙方命宫同支，婚缘有力，感情踏实。"
        elif _is_liuhe(hus_a.branch_idx, lb_b):
            s4 = 16
            d4 = "甲方夫妻宫与乙方命宫地支六合，情感连结天然，相互吸引。"
        elif _is_sanhe(hus_a.branch_idx, lb_b):
            s4 = 14
            d4 = "甲方夫妻宫与乙方命宫地支三合，感情格局顺畅。"
        elif _is_chong(hus_a.branch_idx, lb_b):
            s4 = 5
            d4 = "甲方夫妻宫与乙方命宫地支相冲，婚缘有阻滞，需磨合。"
    dims.append(CompatibilityDimension("夫妻宫缘", s4, 20, d4))

    # ── 维度 5：阴阳互补（15 分）────────────────────────────
    # 天干阴阳：甲丙戊庚壬=阳(0)，乙丁己辛癸=阴(1)
    yy_a = chart_a.life_palace_stem_idx % 2  # 0=阳, 1=阴
    yy_b = chart_b.life_palace_stem_idx % 2
    stem_a = chart_a.life_palace_gz[0]
    stem_b = chart_b.life_palace_gz[0]
    if yy_a != yy_b:
        s5 = 15
        d5 = (
            f"命宫天干一阴（{stem_b if yy_b else stem_a}）一阳（{stem_a if yy_a == 0 else stem_b}），"
            f"刚柔相济，阴阳互补，相得益彰。"
        )
    else:
        label = "阳" if yy_a == 0 else "阴"
        s5 = 8
        d5 = f"命宫天干同为{label}（{stem_a}、{stem_b}），同质相趋，可共进退，惟缺互补之力。"
    dims.append(CompatibilityDimension("阴阳互补", s5, 15, d5))

    # ── 综合评定 ─────────────────────────────────────────────
    total = sum(d.score for d in dims)
    max_total = sum(d.max_score for d in dims)  # 100
    pct = total / max_total if max_total else 0

    if pct >= 0.85:
        level = "上上签"
        summary = "天作之合，情缘深厚，两人相辅相成，诸事顺遂。"
    elif pct >= 0.70:
        level = "上签"
        summary = "缘分深厚，相伴成长，感情稳固，略有磨合但终得和谐。"
    elif pct >= 0.55:
        level = "中签"
        summary = "有缘相聚，需多沟通理解，用心经营可共克时艰。"
    elif pct >= 0.40:
        level = "下签"
        summary = "差异较大，需格外付出与磨合，共同成长方可长久。"
    else:
        level = "平"
        summary = "阻碍较多，双方需极大努力相互理解，宜审慎。"

    return CompatibilityResult(
        total_score=total,
        max_score=max_total,
        level=level,
        summary=summary,
        dimensions=dims,
        person_a_info={
            "birth_solar": chart_a.birth_solar,
            "gender": chart_a.gender,
            "life_gz": chart_a.life_palace_gz,
            "body_gz": chart_a.body_palace_gz,
            "wuxing_ju": chart_a.wuxing_ju_name,
        },
        person_b_info={
            "birth_solar": chart_b.birth_solar,
            "gender": chart_b.gender,
            "life_gz": chart_b.life_palace_gz,
            "body_gz": chart_b.body_palace_gz,
            "wuxing_ju": chart_b.wuxing_ju_name,
        },
        harmony_points=_collect_harmony(chart_a, chart_b),
        conflict_points=_collect_conflicts(chart_a, chart_b),
        complement_points=_collect_complements(chart_a, chart_b),
        palace_compare=_build_palace_compare(chart_a, chart_b),
        disclaimer="合盘分析基于规则化 heuristic 模型，仅供参考，不构成决策依据。",
        layer="heuristic",
    )


# ──────────────────────────────────────────────────────────────
# 冲合点 / 互补点 收集
# ──────────────────────────────────────────────────────────────

_KEY_PALACES = ["命宫", "财帛宫", "夫妻宫", "官禄宫", "迁移宫", "疾厄宫"]


def _collect_harmony(ca, cb) -> list[str]:
    """正向合和点列表。"""
    pts: list[str] = []
    lb_a, lb_b = ca.life_palace_branch, cb.life_palace_branch
    yb_a, yb_b = ca.lunar.year_branch_idx, cb.lunar.year_branch_idx

    if _is_liuhe(lb_a, lb_b):
        pts.append(f"命宫六合（{BRANCHES[lb_a]}⇌{BRANCHES[lb_b]}）：天然默契，磁场相吸")
    elif _is_sanhe(lb_a, lb_b):
        pts.append(f"命宫三合（{BRANCHES[lb_a]}△{BRANCHES[lb_b]}）：志趣相投，目标一致")

    if _is_liuhe(yb_a, yb_b):
        pts.append(f"生肖六合（{BRANCHES[yb_a]}⇌{BRANCHES[yb_b]}）：情投意合，命中注定")
    elif _is_sanhe(yb_a, yb_b):
        pts.append(f"生肖三合（{BRANCHES[yb_a]}△{BRANCHES[yb_b]}）：合作顺畅，相互成就")

    wx_a = _JU_TO_WX.get(ca.wuxing_ju, "土")
    wx_b = _JU_TO_WX.get(cb.wuxing_ju, "土")
    if _wx_relation(wx_a, wx_b) == "相生":
        pts.append(f"五行相生（{wx_a}↔{wx_b}）：能量互滋，彼此助益")

    # 夫妻宫 → 对方命宫主星重叠
    pmap_a = {p.name: p for p in ca.palaces}
    pmap_b = {p.name: p for p in cb.palaces}
    hw_a = pmap_a.get("夫妻宫")
    lp_b = pmap_b.get("命宫")
    if hw_a and lp_b:
        common = {s["name"] for s in hw_a.main_stars} & {s["name"] for s in lp_b.main_stars}
        if common:
            pts.append(f"夫妻宫主星重叠（{'/'.join(common)}）：情缘天定，命中注定伴侣")
        elif _is_liuhe(hw_a.branch_idx, lb_b):
            pts.append("甲方夫妻宫与乙方命宫六合：感情缘分顺畅有力")

    return pts


def _collect_cross_flying_ji(chart_from, chart_to, side_label: str) -> list[str]:
    """飞星化忌落至对方命宫地支所在宫位，或飞化冲克该宫。"""
    flying = getattr(chart_from, "flying", None)
    if not flying:
        return []

    pts: list[str] = []
    target_branch = chart_to.life_palace_branch
    target_palaces = [p.name for p in getattr(chart_from, "palaces", []) or [] if p.branch_idx == target_branch]
    if not target_palaces:
        return pts

    for fp in getattr(flying, "palaces", []) or []:
        palace_name = getattr(fp, "palace_name", "")
        flying_out = getattr(fp, "flying_out", {}) or {}
        ji_land = flying_out.get("化忌", "")
        for tp in target_palaces:
            if f"({tp})" in ji_land or tp in ji_land:
                pts.append(
                    f"{side_label}{palace_name}宫干化忌飞入同乙方命宫地支之{tp}：" "情款或承诺易有亏欠感，宜坦诚沟通"
                )

    chonged = getattr(flying, "chonged", None) or {}
    for palace_name in target_palaces:
        for desc in chonged.get(palace_name, []):
            if "化忌" in desc:
                pts.append(f"{side_label}飞星{desc}（对应乙方命宫地支）：冲克明显，需主动化解")

    return pts


def _collect_conflicts(ca, cb) -> list[str]:
    """冲克矛盾点列表。"""
    pts: list[str] = []
    lb_a, lb_b = ca.life_palace_branch, cb.life_palace_branch
    yb_a, yb_b = ca.lunar.year_branch_idx, cb.lunar.year_branch_idx

    if _is_chong(lb_a, lb_b):
        pts.append(f"命宫相冲（{BRANCHES[lb_a]}⚡{BRANCHES[lb_b]}）：个性强烈碰撞，易起争执")

    if _is_chong(yb_a, yb_b):
        pts.append(f"生肖相冲（{BRANCHES[yb_a]}⚡{BRANCHES[yb_b]}）：年支对立，暗中竞争")

    wx_a = _JU_TO_WX.get(ca.wuxing_ju, "土")
    wx_b = _JU_TO_WX.get(cb.wuxing_ju, "土")
    if _wx_relation(wx_a, wx_b) == "相克":
        winner = wx_a if _WX_KE.get(wx_a) == wx_b else wx_b
        loser = wx_b if winner == wx_a else wx_a
        pts.append(f"五行相克（{winner}克{loser}）：强弱失衡，需注意能量疏导")

    # 夫妻宫 → 命宫相冲
    pmap_a = {p.name: p for p in ca.palaces}
    hw_a = pmap_a.get("夫妻宫")
    if hw_a and _is_chong(hw_a.branch_idx, lb_b):
        pts.append("甲方夫妻宫与乙方命宫相冲：婚缘有阻滞，需主动化解")

    pts.extend(_collect_cross_flying_ji(ca, cb, "甲方"))
    pts.extend(_collect_cross_flying_ji(cb, ca, "乙方"))

    return pts


def _collect_complements(ca, cb) -> list[str]:
    """互补增益点列表。"""
    pts: list[str] = []
    # 阴阳互补
    yy_a = ca.life_palace_stem_idx % 2
    yy_b = cb.life_palace_stem_idx % 2
    if yy_a != yy_b:
        label_a = "阳" if yy_a == 0 else "阴"
        label_b = "阳" if yy_b == 0 else "阴"
        pts.append(f"阴阳互补（甲方{label_a}·乙方{label_b}）：刚柔相济，优势互补")

    # 五行互补（无生克、五行不同则中性互补）
    wx_a = _JU_TO_WX.get(ca.wuxing_ju, "土")
    wx_b = _JU_TO_WX.get(cb.wuxing_ju, "土")
    if wx_a != wx_b and _wx_relation(wx_a, wx_b) not in ("相克",):
        pts.append(f"五行差异（{wx_a}/{wx_b}）：不同特质形成互补，各有所长")

    # 身宫互补（身宫不同）
    bg_a = ca.body_palace_gz
    bg_b = cb.body_palace_gz
    if bg_a != bg_b:
        pts.append(f"身宫不同（{bg_a}/{bg_b}）：侧重点各异，携手覆盖更广人生面向")

    return pts


def _build_palace_compare(ca, cb) -> list[dict]:
    """生成六大关键宫位双方对比列表。"""
    pmap_a = {p.name: p for p in ca.palaces}
    pmap_b = {p.name: p for p in cb.palaces}
    result = []
    for pname in _KEY_PALACES:
        pa = pmap_a.get(pname)
        pb = pmap_b.get(pname)
        entry: dict = {"palace": pname}
        for side, p in (("a", pa), ("b", pb)):
            if p:
                entry[f"{side}_gz"] = f"{p.stem}{p.branch}"
                entry[f"{side}_stars"] = "/".join(s["name"] for s in p.main_stars) or "空"
                entry[f"{side}_tags"] = p.analysis_tags[:3] if p.analysis_tags else []
                entry[f"{side}_conclusion"] = p.conclusion or ""
            else:
                entry[f"{side}_gz"] = "—"
                entry[f"{side}_stars"] = "—"
                entry[f"{side}_tags"] = []
                entry[f"{side}_conclusion"] = ""
        # 宫位地支关系
        if pa and pb:
            rel = ""
            ai, bi = pa.branch_idx, pb.branch_idx
            if _is_liuhe(ai, bi):
                rel = "六合"
            elif _is_sanhe(ai, bi):
                rel = "三合"
            elif ai == bi:
                rel = "同支"
            elif _is_chong(ai, bi):
                rel = "相冲"
            entry["relation"] = rel
        else:
            entry["relation"] = ""
        result.append(entry)
    return result
