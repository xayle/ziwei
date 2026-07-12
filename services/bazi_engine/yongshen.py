"""
services/bazi_engine/yongshen.py — 用神决策树（5分支）

M1 任务 1.06: 5分支决策树 [S8/P61]
  ① 扶抑 ② 从强 ③ 从弱 ④ 特殊格局 ⑤ 调候
  验证: 每分支1案例

传统命理口诀：
  扶抑法(抑强扶弱) — 最常用，适用于中和、偏旺、偏弱命局
  从强格 — 日主极旺且无有力克泄，顺势而为
  从弱格 — 日主极弱且无有力帮扶，顺势而为
  特殊格局 — 专旺/从旺等（当前版本仅检测极端情况）
  调候法 — 月令寒暖，以调适为先
"""

from __future__ import annotations

from dataclasses import dataclass, field

from services.bazi_engine.strength import StrengthResult
from services.bazi_engine.wuxing import WuxingResult

# 五行相生相克
SHENG: dict[str, str] = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}
KE: dict[str, str] = {
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
    "metal": "wood",
}
# 我的父母五行（生我）
SHENG_REV = {v: k for k, v in SHENG.items()}
# 我生（食伤）
# 克我（官杀）
KE_REV = {v: k for k, v in KE.items()}


@dataclass
class YongshenResult:
    """用神结果"""

    branch: str  # 分支: 扶抑/从强/从弱/特殊格局/调候
    favor: list[str]  # 喜用五行（元素名）
    avoid: list[str]  # 忌神五行（元素名）
    rationale: str  # 白话说明
    inference_tags: list[str] = field(default_factory=list)
    primary: list[str] = field(default_factory=list)  # 第一用神五行
    secondary: list[str] = field(default_factory=list)  # 第二用神五行
    priority_reason: str = ""  # 格局/扶抑/调候优先级说明
    cong_variant: str = ""  # 真从 / 假从 / ""

    def __post_init__(self) -> None:
        _finalize_yongshen(self)


def _finalize_yongshen(result: YongshenResult) -> YongshenResult:
    """填充 primary/secondary 双层用神字段。"""
    if not result.primary and result.favor:
        result.primary = result.favor[:1]
    if not result.secondary and len(result.favor) > 1:
        result.secondary = result.favor[1:2]
    if not result.priority_reason:
        result.priority_reason = f"{result.branch}分支：{'、'.join(result.favor[:2]) or '—'}为喜"
    return result


def _apply_cong_variant(result: YongshenResult, variant: str) -> YongshenResult:
    result.cong_variant = variant
    if variant:
        result.priority_reason = f"{variant}：{result.priority_reason}"
    return result


def _get_fuyi_yongshen(
    day_elem: str,
    strength: StrengthResult,
    wuxing: WuxingResult,
) -> YongshenResult:
    """
    ① 扶抑法：弱则扶（增加同类+生我），强则抑（增加克我+泄我）
    适用: 中和/偏旺/偏弱（占命局~80%）
    """
    parent_elem = SHENG_REV.get(day_elem, "")  # 生我（印星）
    child_elem = SHENG.get(day_elem, "")  # 我生（食伤）
    ke_me = KE_REV.get(day_elem, "")  # 克我（官杀）
    i_ke = KE.get(day_elem, "")  # 我克（财星）

    if strength.is_weak:
        favor = [day_elem, parent_elem]
        avoid = [ke_me, child_elem, i_ke]
        tag = f"身弱用{parent_elem}印和{day_elem}比，忌{ke_me}官与食伤"
        rationale = (
            f"日主{strength.day_stem}（{day_elem}）偏弱，"
            f"宜以{parent_elem}（印星）生扶，{day_elem}（比劫）助力；"
            f"忌{ke_me}（官杀）克制，不宜{child_elem}（食伤）泄气。"
        )
    elif strength.is_strong:
        favor = [ke_me, child_elem, i_ke]
        avoid = [day_elem, parent_elem]
        tag = f"身强用{ke_me}官和{child_elem}食伤泄，忌过多比印"
        rationale = (
            f"日主{strength.day_stem}（{day_elem}）偏旺，"
            f"宜以{ke_me}（官杀）制约，或以{child_elem}（食伤）泄秀；"
            f"忌再增{day_elem}（比劫）和{parent_elem}（印星）。"
        )
    else:
        # 中和：以月令喜用为参考
        favor = [parent_elem, child_elem]
        avoid = [ke_me]
        tag = "中和命局，顺势而为"
        rationale = (
            f"日主{strength.day_stem}（{day_elem}）中和，以{parent_elem}（印）调气，{child_elem}（食伤）发挥为佳。"
        )

    return YongshenResult(
        branch="扶抑",
        favor=[e for e in favor if e],
        avoid=[e for e in avoid if e],
        rationale=rationale,
        inference_tags=[tag],
    )


def _get_congqiang_yongshen(day_elem: str) -> YongshenResult:
    """
    ② 从强格：日主极旺，四柱几乎全为同类/生我，顺势取同类为用
    """
    parent_elem = SHENG_REV.get(day_elem, "")
    child_elem = SHENG.get(day_elem, "")
    ke_me = KE_REV.get(day_elem, "")

    return YongshenResult(
        branch="从强",
        favor=[day_elem, parent_elem],
        avoid=[ke_me, child_elem],
        rationale=(f"从强格：日主{day_elem}极旺，顺势取{day_elem}和{parent_elem}为喜用，忌{ke_me}来克（逆之则祸）。"),
        inference_tags=["极旺从强格"],
    )


def _get_congruo_yongshen(day_elem: str, dominant_elem: str) -> YongshenResult:
    """
    ③ 从弱格：日主极弱，无根无援，顺从强势五行
    """
    parent_of_dom = SHENG_REV.get(dominant_elem, "")

    return YongshenResult(
        branch="从弱",
        favor=[dominant_elem, parent_of_dom],
        avoid=[day_elem, SHENG_REV.get(day_elem, "")],
        rationale=(
            f"从弱格：日主{day_elem}极弱无根，顺从旺神{dominant_elem}，"
            f"以{dominant_elem}和{parent_of_dom}为喜，"
            f"忌{day_elem}（比劫）再搅局（弃命从旺）。"
        ),
        inference_tags=[f"极弱从弱格(从{dominant_elem})"],
    )


def _get_tiaohou_yongshen(
    day_elem: str,
    month_branch: str,
) -> YongshenResult:
    """
    ⑤ 调候法：月令极寒/极热时优先调候
    寒月（亥子丑）→ 喜火（调寒），土次之
    热月（巳午未）→ 喜水（调热），金次之
    """
    cold_months = {"亥", "子", "丑"}
    hot_months = {"巳", "午", "未"}

    if month_branch in cold_months:
        favor = ["fire", "earth"]
        avoid = ["water", "metal"]
        rationale = f"月令{month_branch}寒冷，调候喜火（暖局），土次之；忌水金增寒。"
        tag = "寒月调候喜火"
    elif month_branch in hot_months:
        favor = ["water", "metal"]
        avoid = ["fire", "wood"]
        rationale = f"月令{month_branch}炎热，调候喜水（润局），金次之；忌木火增炎。"
        tag = "热月调候喜水"
    else:
        # 春秋温和，退回扶抑
        parent_elem = SHENG_REV.get(day_elem, "")
        favor = [day_elem, parent_elem]
        avoid = [KE_REV.get(day_elem, "")]
        rationale = f"月令温和，以扶抑为主，{day_elem}日主取{parent_elem}为调候辅助。"
        tag = "温和月令调候退回扶抑"

    return YongshenResult(
        branch="调候",
        favor=[e for e in favor if e],
        avoid=[e for e in avoid if e],
        rationale=rationale,
        inference_tags=[tag],
    )


def _roles(day_elem: str) -> dict[str, str]:
    """日主五行角色：印/食伤/官杀/财。"""
    return {
        "self": day_elem,
        "parent": SHENG_REV.get(day_elem, ""),
        "child": SHENG.get(day_elem, ""),
        "ke_me": KE_REV.get(day_elem, ""),
        "i_ke": KE.get(day_elem, ""),
    }


def _uniq_elems(items: list[str], limit: int = 2) -> list[str]:
    return [e for e in dict.fromkeys(items) if e][:limit]


_INNER_GEJU_NAMES = frozenset(
    {
        "正官格",
        "七杀格",
        "正印格",
        "偏印格",
        "正财格",
        "偏财格",
        "食神格",
        "伤官格",
    }
)

# 外格名称 → 专旺五行
_OUTER_GEJU_ELEM: dict[str, str] = {
    "曲直格": "wood",
    "炎上格": "fire",
    "稼穑格": "earth",
    "从革格": "metal",
    "润下格": "water",
}

# 化气格名称 → 化出五行
_HUAQI_GEJU_ELEM: dict[str, str] = {
    "化土格": "earth",
    "化金格": "metal",
    "化水格": "water",
    "化木格": "wood",
    "化火格": "fire",
}


def _get_extended_geju_yongshen(
    day_elem: str,
    geju_name: str,
    wuxing: WuxingResult,
) -> YongshenResult | None:
    """
    化气 / 外格（专旺）/ 从格 专用用神。
    规则：专旺顺旺（旺神+印），从格顺势（从神及其相生）。
    """
    scores = wuxing.scores_weighted if wuxing and hasattr(wuxing, "scores_weighted") else {}
    r = _roles(day_elem)

    if geju_name in _HUAQI_GEJU_ELEM:
        elem = _HUAQI_GEJU_ELEM[geju_name]
        parent = SHENG_REV.get(elem, "")
        killer = KE_REV.get(elem, "")
        child = SHENG.get(elem, "")
        favor = _uniq_elems([elem, parent])
        avoid = _uniq_elems([killer, child, day_elem], 3)
        return YongshenResult(
            branch="化气格用神",
            favor=favor,
            avoid=avoid,
            rationale=f"{geju_name}：化气已成，喜{elem}、{parent or '—'}助化神；忌{killer or '—'}来破。",
            inference_tags=[f"{geju_name}专用"],
        )

    if geju_name in _OUTER_GEJU_ELEM:
        elem = _OUTER_GEJU_ELEM[geju_name]
        parent = SHENG_REV.get(elem, "")
        killer = KE_REV.get(elem, "")
        child = SHENG.get(elem, "")
        favor = _uniq_elems([elem, parent])
        avoid = _uniq_elems([killer, child], 3)
        return YongshenResult(
            branch="外格用神",
            favor=favor,
            avoid=avoid,
            rationale=f"{geju_name}：专旺宜顺，喜{elem}、{parent or '—'}；忌{killer or '—'}克、{child or '—'}泄。",
            inference_tags=[f"{geju_name}专用"],
        )

    if geju_name == "从旺格":
        parent = SHENG_REV.get(day_elem, "")
        killer = KE_REV.get(day_elem, "")
        favor = _uniq_elems([day_elem, parent])
        avoid = _uniq_elems([killer, SHENG.get(day_elem, "")], 3)
        return YongshenResult(
            branch="从旺格用神",
            favor=favor,
            avoid=avoid,
            rationale=f"从旺格：日主{day_elem}极旺，顺势助旺，忌{killer or '—'}克泄。",
            inference_tags=["从旺格专用"],
        )

    if geju_name == "专旺格":
        if not scores:
            return None
        elem = max(scores, key=lambda k: scores.get(k) or 0.0)
        parent = SHENG_REV.get(elem, "")
        killer = KE_REV.get(elem, "")
        favor = _uniq_elems([elem, parent])
        avoid = _uniq_elems([killer, SHENG.get(elem, "")], 3)
        return YongshenResult(
            branch="专旺格用神",
            favor=favor,
            avoid=avoid,
            rationale=f"专旺格：{elem}气专一，喜{elem}、{parent or '—'}；忌{killer or '—'}逆旺。",
            inference_tags=["专旺格专用"],
        )

    if geju_name == "从财格":
        favor = _uniq_elems([r["i_ke"], r["child"]])
        avoid = _uniq_elems([r["self"], r["parent"], r["ke_me"]], 3)
        return YongshenResult(
            branch="从财格用神",
            favor=favor,
            avoid=avoid,
            rationale="从财格：弃命从财，喜财星与食伤生财；忌比劫印比夺财。",
            inference_tags=["从财格专用"],
        )

    if geju_name == "从官杀格":
        favor = _uniq_elems([r["ke_me"], r["parent"]])
        avoid = _uniq_elems([r["child"], r["self"]], 3)
        return YongshenResult(
            branch="从官杀格用神",
            favor=favor,
            avoid=avoid,
            rationale="从官杀格：弃命从官杀，喜官杀与印化；忌食伤制杀、比劫助身。",
            inference_tags=["从官杀格专用"],
        )

    if geju_name == "从儿格":
        favor = _uniq_elems([r["child"], r["i_ke"]])
        avoid = _uniq_elems([r["ke_me"], r["parent"]], 3)
        return YongshenResult(
            branch="从儿格用神",
            favor=favor,
            avoid=avoid,
            rationale="从儿格：弃命从食伤，喜食伤生财；忌印星夺食、官杀混杂。",
            inference_tags=["从儿格专用"],
        )

    if geju_name == "从势格":
        if not scores:
            return None
        ranked = sorted(scores, key=lambda k: scores.get(k) or 0.0, reverse=True)
        favor = _uniq_elems([ranked[0], ranked[1] if len(ranked) > 1 else ""])
        avoid = _uniq_elems([day_elem, SHENG_REV.get(day_elem, "")], 3)
        return YongshenResult(
            branch="从势格用神",
            favor=favor,
            avoid=avoid,
            rationale=f"从势格：日主弱而势在{'、'.join(favor)}，顺势而从；忌{day_elem}比劫助身逆势。",
            inference_tags=["从势格专用"],
        )

    return None


def _get_zhengge_yongshen(
    day_elem: str,
    geju_name: str,
    strength: StrengthResult,
    wuxing: WuxingResult,
) -> YongshenResult | None:
    """
    八正格配用神（子平真诠）：
      正官/七杀 → 官印 / 制杀(食) / 化杀(印)
      印格 → 官印相生 / 财制枭
      财格 → 身弱助身 / 食伤生财
      食伤 → 食神生财 / 伤官佩印 / 伤官生财
    """
    if geju_name not in _INNER_GEJU_NAMES:
        return None

    r = _roles(day_elem)
    scores = wuxing.scores_weighted if wuxing and hasattr(wuxing, "scores_weighted") else {}
    parent_score = scores.get(r["parent"], 0.0)
    child_score = scores.get(r["child"], 0.0)

    if geju_name == "正官格":
        if strength.is_weak:
            favor = _uniq_elems([r["parent"], r["ke_me"]])
            avoid = _uniq_elems([r["i_ke"], r["child"], r["self"]], 3)
            tag = "正官格身弱：印护官"
        else:
            favor = _uniq_elems([r["i_ke"], r["ke_me"]])
            avoid = _uniq_elems([r["child"], r["self"], r["parent"]], 3)
            tag = "正官格身强：财生官"
        rationale = f"正官格以{favor[0]}、{favor[1] if len(favor) > 1 else '—'}为格局用神。"

    elif geju_name == "七杀格":
        if child_score >= 8.0:
            favor = _uniq_elems([r["child"], r["parent"]])
            tag = "七杀格：食神制杀，印为辅"
        else:
            favor = _uniq_elems([r["parent"], r["self"]])
            tag = "七杀格：印绶化杀，比劫帮身"
        avoid = _uniq_elems([r["i_ke"], r["ke_me"] if r["ke_me"] != r["child"] else ""], 3)
        rationale = f"七杀格{tag.split('：', 1)[-1]}。"

    elif geju_name == "正印格":
        favor = _uniq_elems([r["ke_me"], r["parent"]])
        avoid = _uniq_elems([r["i_ke"], r["child"]], 3)
        tag = "正印格：官印相生"
        rationale = "正印格喜官印相生，财坏印为忌。"

    elif geju_name == "偏印格":
        favor = _uniq_elems([r["i_ke"], r["child"]])
        avoid = _uniq_elems([r["parent"], r["self"]], 3)
        tag = "偏印格：财制枭，食神泄秀"
        rationale = "偏印格（枭神）宜财星制枭、食神泄身。"

    elif geju_name in ("正财格", "偏财格"):
        i_ke_score = scores.get(r["i_ke"], 0.0)
        parent_elem_score = scores.get(r["parent"], 0.0)
        if strength.is_weak or strength.tier in ("极弱", "偏弱"):
            # 财格身弱：印比扶身 vs 食伤生财（视命局财/印孰重）
            if (
                geju_name == "偏财格"
                and strength.tier == "极弱"
                and i_ke_score >= 18.0
                and parent_elem_score < i_ke_score
            ):
                favor = _uniq_elems([r["i_ke"], r["child"]])
                avoid = _uniq_elems([r["ke_me"], r["self"], r["parent"]], 3)
                tag = "偏财格身弱：食伤生财"
            else:
                favor = _uniq_elems([r["parent"], r["self"]])
                avoid = _uniq_elems([r["ke_me"], r["child"]], 3)
                tag = "财格身弱：印比助身"
        else:
            favor = _uniq_elems([r["child"], r["ke_me"]])
            avoid = _uniq_elems([r["self"], r["parent"]], 3)
            tag = "财格身强：食伤生财，官杀护财"
        rationale = f"{geju_name}{tag.split('：', 1)[-1]}。"

    elif geju_name == "食神格":
        favor = _uniq_elems([r["i_ke"], r["child"]])
        avoid = _uniq_elems([r["parent"], r["ke_me"]], 3)
        tag = "食神格：食神生财"
        rationale = "食神格以财星承接食神秀气，枭印夺食为忌。"

    elif geju_name == "伤官格":
        if parent_score >= 12.0 or (strength.is_weak and parent_score >= 6.0):
            favor = _uniq_elems([r["parent"], r["i_ke"]])
            tag = "伤官格：伤官佩印"
        else:
            favor = _uniq_elems([r["i_ke"], r["child"]])
            tag = "伤官格：伤官生财"
        avoid = _uniq_elems([r["ke_me"], r["self"]], 3)
        rationale = f"伤官格{tag.split('：', 1)[-1]}。"

    else:
        return None

    return YongshenResult(
        branch=geju_name.replace("格", "格用神"),
        favor=favor,
        avoid=avoid if "avoid" in locals() else [],
        rationale=rationale,
        inference_tags=[tag],
    )


def _get_jianluge_yongshen(
    day_elem: str,
    wuxing: WuxingResult,
) -> YongshenResult:
    """
    建禄格用神：日主坐禄身强，不以月令为用。
    子平：「月令为日主禄神，取官煞财为用」。
    """
    ke_me = KE_REV.get(day_elem, "")
    i_ke = KE.get(day_elem, "")
    parent_elem = SHENG_REV.get(day_elem, "")

    favor = _uniq_elems([i_ke, ke_me])
    avoid = _uniq_elems([day_elem, parent_elem], 3)
    return YongshenResult(
        branch="建禄格",
        favor=favor,
        avoid=avoid,
        rationale=(
            f"建禄格：日主{day_elem}坐禄身强，取{i_ke or '—'}（财）、"
            f"{ke_me or '—'}（官杀）为用神；忌比劫印星再助旺。"
        ),
        inference_tags=["建禄格专用分支"],
    )


def _get_yangrenge_yongshen(day_elem: str) -> YongshenResult:
    """
    羊刃格用神：刃旺须制，官杀制刃为首要用神，食伤泄秀、财星辅之。
    忌印比再增旺。
    """
    ke_me = KE_REV.get(day_elem, "")  # 官杀（克我）
    child_elem = SHENG.get(day_elem, "")  # 食伤（我生）
    i_ke = KE.get(day_elem, "")  # 财星（我克）
    parent_elem = SHENG_REV.get(day_elem, "")  # 印星（生我）

    favor = [e for e in [ke_me, child_elem, i_ke] if e]
    avoid = [e for e in [day_elem, parent_elem] if e]
    return YongshenResult(
        branch="月刃格",
        favor=favor,
        avoid=avoid,
        rationale=(
            f"月刃格：刃旺须制，取{ke_me}（官杀）制刃为用神，"
            f"{child_elem}（食伤）泄旺，{i_ke}（财星）辅之（财滋官杀）；"
            f"忌{day_elem}比劫再助刃旺，{parent_elem}印星亦忌。"
        ),
        inference_tags=["月刃格专用分支"],
    )


def compute_yongshen(
    day_stem: str,
    month_branch: str,
    strength: StrengthResult,
    wuxing: WuxingResult,
    geju_name: str = "",
) -> YongshenResult:
    """
    用神决策树入口（5分支）。

    优先级:
      0. 特殊格局（建禄格/羊刃格）→ 专用分支（geju_name 传入时）
      0a. 化气/外格/从格 → `_get_extended_geju_yongshen`
      0b. 八正格 → `_get_zhengge_yongshen`（官印/制杀/佩印/生财等）
      1. 极端月令（寒月/热月）→ 调候法
      2. 极旺 + 无克泄 → 从强格
      3. 极弱 + 无印比 → 从弱格（顺从强势五行）
      4. 特殊格局（当前版本同从强/从弱处理）
      5. 默认 → 扶抑法
    """
    cold_months = {"亥", "子", "丑"}
    hot_months = {"巳", "午", "未"}

    day_elem = strength.day_elem

    # ⓪ 特殊格局：建禄格/羊刃格 → 专用用神分支（优先级最高）
    if "建禄" in geju_name:
        return _get_jianluge_yongshen(day_elem, wuxing)
    if "月刃" in geju_name or "羊刃" in geju_name:
        return _get_yangrenge_yongshen(day_elem)

    # ⓪a 化气/外格/从格配用神
    extended = _get_extended_geju_yongshen(day_elem, geju_name, wuxing)
    if extended is not None:
        return extended

    # ⓪b 八正格配用神（子平真诠，优先于扶抑/从格/调候合并）
    zhengge = _get_zhengge_yongshen(day_elem, geju_name, strength, wuxing)
    if zhengge is not None:
        return zhengge

    # ① 月令极端 → 调候优先（寒热月且日主非调候喜用五行时）
    if month_branch in cold_months and day_elem in ("water", "metal"):
        return _get_tiaohou_yongshen(day_elem, month_branch)
    if month_branch in hot_months and day_elem in ("fire", "wood"):
        return _get_tiaohou_yongshen(day_elem, month_branch)

    # ② 极旺 → 判断是否从强（需要同类占绝对优势）
    if strength.tier == "极旺":
        same_or_parent_score = wuxing.scores_weighted.get(day_elem, 0) + wuxing.scores_weighted.get(
            SHENG_REV.get(day_elem, ""), 0
        )
        if same_or_parent_score >= 70:
            return _apply_cong_variant(_get_congqiang_yongshen(day_elem), "真从")
        if same_or_parent_score >= 55:
            return _apply_cong_variant(_get_congqiang_yongshen(day_elem), "假从")

    # ③ 极弱 → 判断是否从弱
    if strength.tier == "极弱":  # P2-F: 防护 scores_weighted 为空时 max() 抛 ValueError
        if not wuxing.scores_weighted:
            return _get_fuyi_yongshen(day_elem, strength, wuxing)  # 找出最强五行
        dominant_elem = max(wuxing.scores_weighted, key=lambda e: wuxing.scores_weighted[e])
        same_score = wuxing.scores_weighted.get(day_elem, 0)
        parent_score = wuxing.scores_weighted.get(SHENG_REV.get(day_elem, ""), 0)
        if same_score + parent_score < 15:  # 几乎无根无援
            return _apply_cong_variant(_get_congruo_yongshen(day_elem, dominant_elem), "真从")
        if same_score + parent_score < 25:
            return _apply_cong_variant(_get_congruo_yongshen(day_elem, dominant_elem), "假从")

    # ⑤ 调候辅助（非极端月令）
    # 此处决定使用扶抑还是调候：若月令已给出明显寒热，仍适当参考
    if month_branch in cold_months or month_branch in hot_months:
        tiaohou = _get_tiaohou_yongshen(day_elem, month_branch)
        fuyi = _get_fuyi_yongshen(day_elem, strength, wuxing)
        # 合并：调候喜用优先，同时保留扶抑喜用
        merged_favor = list(dict.fromkeys(tiaohou.favor + fuyi.favor))[:3]
        merged_avoid = list(dict.fromkeys(tiaohou.avoid + fuyi.avoid))[:3]
        return YongshenResult(
            branch="调候+扶抑",
            favor=merged_favor,
            avoid=merged_avoid,
            rationale=tiaohou.rationale + " 兼顾：" + fuyi.rationale,
            inference_tags=tiaohou.inference_tags + fuyi.inference_tags,
        )

    # 默认扶抑
    return _get_fuyi_yongshen(day_elem, strength, wuxing)
