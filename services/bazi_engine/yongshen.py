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
from services.bazi_engine.wuxing import WuxingResult, ELEMENTS

# 五行相生相克
SHENG: dict[str, str] = {
    "wood": "fire", "fire": "earth", "earth": "metal",
    "metal": "water", "water": "wood",
}
KE: dict[str, str] = {
    "wood": "earth", "earth": "water", "water": "fire",
    "fire": "metal", "metal": "wood",
}
# 我的父母五行（生我）
SHENG_REV = {v: k for k, v in SHENG.items()}
# 我生（食伤）
# 克我（官杀）
KE_REV = {v: k for k, v in KE.items()}


@dataclass
class YongshenResult:
    """用神结果"""
    branch: str                        # 分支: 扶抑/从强/从弱/特殊格局/调候
    favor: list[str]                   # 喜用五行（元素名）
    avoid: list[str]                   # 忌神五行（元素名）
    rationale: str                     # 白话说明
    inference_tags: list[str] = field(default_factory=list)


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
    child_elem = SHENG.get(day_elem, "")        # 我生（食伤）
    ke_me = KE_REV.get(day_elem, "")            # 克我（官杀）
    i_ke = KE.get(day_elem, "")                 # 我克（财星）

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
            f"日主{strength.day_stem}（{day_elem}）中和，"
            f"以{parent_elem}（印）调气，{child_elem}（食伤）发挥为佳。"
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
        rationale=(
            f"从强格：日主{day_elem}极旺，顺势取{day_elem}和{parent_elem}为喜用，"
            f"忌{ke_me}来克（逆之则祸）。"
        ),
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
      1. 极端月令（寒月/热月）→ 调候法
      2. 极旺 + 无克泄 → 从强格
      3. 极弱 + 无印比 → 从弱格（顺从强势五行）
      4. 特殊格局（当前版本同从强/从弱处理）
      5. 默认 → 扶抑法
    """
    cold_months = {"亥", "子", "丑"}
    hot_months = {"巳", "午", "未"}

    day_elem = strength.day_elem

    # ① 月令极端 → 调候优先（寒热月且日主非调候喜用五行时）
    if month_branch in cold_months and day_elem in ("water", "metal"):
        return _get_tiaohou_yongshen(day_elem, month_branch)
    if month_branch in hot_months and day_elem in ("fire", "wood"):
        return _get_tiaohou_yongshen(day_elem, month_branch)

    # ② 极旺 → 判断是否从强（需要同类占绝对优势）
    if strength.tier == "极旺":
        same_or_parent_score = (
            wuxing.scores_weighted.get(day_elem, 0)
            + wuxing.scores_weighted.get(SHENG_REV.get(day_elem, ""), 0)
        )
        if same_or_parent_score >= 70:
            return _get_congqiang_yongshen(day_elem)

    # ③ 极弱 → 判断是否从弱
    if strength.tier == "极弱":
        # 找出最强五行
        dominant_elem = max(wuxing.scores_weighted, key=lambda e: wuxing.scores_weighted[e])
        same_score = wuxing.scores_weighted.get(day_elem, 0)
        parent_score = wuxing.scores_weighted.get(SHENG_REV.get(day_elem, ""), 0)
        if same_score + parent_score < 15:  # 几乎无根无援
            return _get_congruo_yongshen(day_elem, dominant_elem)

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
