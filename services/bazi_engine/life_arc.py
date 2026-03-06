"""
services/bazi_engine/life_arc.py — 人生弧线引擎 (M3 任务 3.07)

LifeArcModel 生成:
  dayun / geju / strength / yongshen 四因子评分 → overall_tier
  overall_tier ∈ {"局高", "局中", "局小"}
  峰值期(peak_periods) / 谨慎期(caution_periods)
  早中晚年运势描述
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# 四因子评分权重
# ──────────────────────────────────────────────────────────────────────────────

LIFE_ARC_WEIGHTS = {
    "dayun":    0.35,   # 大运趋势综合评分
    "geju":     0.25,   # 格局等级
    "strength": 0.20,   # 日主强弱（以中和为优）
    "yongshen": 0.20,   # 用神在命局中的得力程度
}
assert abs(sum(LIFE_ARC_WEIGHTS.values()) - 1.0) < 1e-9

# 格局等级分值映射（百分制）
_GEJU_SCORE: dict[str, float] = {
    "正官格": 85.0, "正印格": 82.0, "食神格": 80.0, "建禄格": 78.0,
    "一气专旺格": 90.0, "羊刃驾杀格": 88.0,
    "七杀格": 72.0, "偏印格": 68.0, "正财格": 75.0, "偏财格": 70.0,
    "伤官格": 65.0, "羊刃格": 62.0,
}
_GEJU_DEFAULT = 60.0
_GEJU_BROKEN  = 40.0

# 强弱层次分值（中和最优）
_STRENGTH_SCORE: dict[str, float] = {
    "极旺": 50.0, "偏旺": 70.0, "中和": 100.0,
    "偏弱": 70.0, "极弱": 50.0,
}


@dataclass
class LifeArcModel:
    """人生弧线结果（M3 返回值）"""
    overall_tier:    str              # 局高 / 局中 / 局小
    total_score:     float            # 综合分 [0-100]
    early_fortune:   str              # 幼年～青年（0-25岁）
    mid_fortune:     str              # 壮年（25-55岁）
    late_fortune:    str              # 晚年（55岁+）
    peak_periods:    list[str]        # 峰值期，如 ["35-45岁：甲午大运，财官双旺"]
    caution_periods: list[str]        # 谨慎期
    factor_scores:   dict[str, float] # 四因子明细分
    summary:         str              # 30字以内总结
    disclaimer: str = (
        "人生弧线为八字综合推演结果，仅供学术研究参考，"
        "不构成任何形式的预测或建议。"
    )


# ──────────────────────────────────────────────────────────────────────────────
# 内部辅助函数
# ──────────────────────────────────────────────────────────────────────────────

def _compute_dayun_factor(dayun_list: list[dict]) -> float:
    """
    大运因子分 [0-100]。

    dayun_list 中每一步含 is_favorable(bool) 和 trend("上升"/"平稳"/"下降")。
    取前6步（一般含主要人生阶段），加权统计。
    """
    if not dayun_list:
        return 60.0

    trend_val = {"上升": 85.0, "平稳": 65.0, "下降": 40.0}
    total = 0.0
    steps = dayun_list[:6]
    for i, dy in enumerate(steps):
        base = 85.0 if dy.get("is_favorable", True) else 45.0
        trend_score = trend_val.get(dy.get("trend", "平稳"), 65.0)
        combined = (base + trend_score) / 2
        total += combined
    return round(total / len(steps), 2)


def _compute_geju_factor(geju_name: str, is_broken: bool) -> float:
    """格局因子分"""
    if is_broken:
        return _GEJU_BROKEN
    return _GEJU_SCORE.get(geju_name, _GEJU_DEFAULT)


def _compute_strength_factor(strength_tier: str) -> float:
    """日主强弱因子分（中和=100，偏极=50-70）"""
    return _STRENGTH_SCORE.get(strength_tier, 65.0)


def _compute_yongshen_factor(
    yongshen_favor: list[str],
    wuxing_scores: dict[str, float],
) -> float:
    """
    用神得力因子 [0-100]。
    用神五行在命局中的总占比 → 归一化为百分制。
    """
    if not yongshen_favor:
        return 60.0
    total = sum(wuxing_scores.values()) or 1.0
    favor_total = sum(wuxing_scores.get(e, 0.0) for e in yongshen_favor)
    ratio = favor_total / total
    # ratio=0.15+ → 接近满分; 0 → 30分
    score = 30.0 + min(ratio / 0.20, 1.0) * 70.0
    return round(score, 2)


def _build_phase_text(dayun_list: list[dict], phase: str) -> str:
    """构建早/中/晚年描述"""
    if phase == "early":
        relevant = [d for d in dayun_list if d.get("start_age", 0) < 25]
        label = "早年（0-25岁）"
    elif phase == "mid":
        relevant = [d for d in dayun_list if 25 <= d.get("start_age", 0) < 55]
        label = "壮年（25-55岁）"
    else:
        relevant = [d for d in dayun_list if d.get("start_age", 0) >= 55]
        label = "晚年（55岁+）"

    if not relevant:
        return f"{label}：大运信息不足，建议参考完整排盘。"

    favorable_count = sum(1 for d in relevant if d.get("is_favorable", True))
    total = len(relevant)

    if favorable_count == total:
        quality = "顺旺，诸事顺遂，用神得令，宜积极进取"
    elif favorable_count >= total * 0.6:
        quality = "总体偏顺，多得贵助，间有波折，把握顺运最为关键"
    elif favorable_count >= total * 0.4:
        quality = "顺逆参半，宜稳中求进，顺运时出击，逆运时守成"
    else:
        quality = "逆运居多，宜低调守成、积德蓄势，待时而动"

    ganzhi_list = "、".join(
        d.get("ganzhi") or (d.get("stem","") + d.get("branch",""))
        for d in relevant
        if d.get("ganzhi") or (d.get("stem") and d.get("branch"))
    )
    if ganzhi_list:
        return f"{label}：历经{ganzhi_list}大运，运势{quality}。"
    return f"{label}：运势{quality}。"


def _find_peak_periods(dayun_list: list[dict]) -> list[str]:
    """找出顺运且趋势上升的大运步，作为峰值期"""
    peaks = []
    for d in dayun_list:
        if d.get("is_favorable", False) and d.get("trend") in ("上升", "平稳"):
            ganzhi = d.get("ganzhi") or (d.get("stem","") + d.get("branch",""))
            start  = d.get("start_age", "?")
            end    = d.get("end_age",   "?")
            peaks.append(f"{start}-{end}岁·{ganzhi}大运（顺运）")
    return peaks or ["暂无明显顺运峰值期，宜均衡规划"]


def _find_caution_periods(dayun_list: list[dict]) -> list[str]:
    """找出逆运的大运步，作为谨慎期"""
    cautions = []
    for d in dayun_list:
        if not d.get("is_favorable", True):
            ganzhi = d.get("ganzhi") or (d.get("stem","") + d.get("branch",""))
            start  = d.get("start_age", "?")
            end    = d.get("end_age",   "?")
            cautions.append(f"{start}-{end}岁·{ganzhi}大运（逆运，宜守成稳进）")
    return cautions or ["暂无明显逆运期"]


# ──────────────────────────────────────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────────────────────────────────────

def compute_life_arc(
    dayun_list: list[dict],
    geju_name: str,
    is_broken: bool,
    strength_tier: str,
    strength_score: float,
    yongshen_favor: list[str],
    wuxing_scores: dict[str, float],
) -> LifeArcModel:
    """
    M3 任务3.07 — 人生弧线计算

    参数:
        dayun_list:    大运列表，每项含 ganzhi/start_age/end_age/is_favorable/trend 等
        geju_name:     命局格局名称
        is_broken:     是否破格
        strength_tier: 日主强弱层次
        strength_score: 日主强弱原始分
        yongshen_favor: 用神五行列表（英文）
        wuxing_scores:  五行得分字典（英文键）

    返回:
        LifeArcModel 实例
    """
    # 四因子原始分
    f_dayun    = _compute_dayun_factor(dayun_list)
    f_geju     = _compute_geju_factor(geju_name, is_broken)
    f_strength = _compute_strength_factor(strength_tier)
    f_yongshen = _compute_yongshen_factor(yongshen_favor, wuxing_scores)

    # 加权合分
    total = (
        f_dayun    * LIFE_ARC_WEIGHTS["dayun"]    +
        f_geju     * LIFE_ARC_WEIGHTS["geju"]     +
        f_strength * LIFE_ARC_WEIGHTS["strength"] +
        f_yongshen * LIFE_ARC_WEIGHTS["yongshen"]
    )
    total = round(total, 2)

    # 总等级
    if total >= 70:
        tier = "局高"
        summary = f"命局综合评分{total:.1f}，格局较高，人生整体顺遂，机遇丰富"
    elif total >= 45:
        tier = "局中"
        summary = f"命局综合评分{total:.1f}，格局中等，顺逆参半，宜把握好运，守住逆运"
    else:
        tier = "局小"
        summary = f"命局综合评分{total:.1f}，格局偏小，宜踏实积累，以平常心处之"

    return LifeArcModel(
        overall_tier    = tier,
        total_score     = total,
        early_fortune   = _build_phase_text(dayun_list, "early"),
        mid_fortune     = _build_phase_text(dayun_list, "mid"),
        late_fortune    = _build_phase_text(dayun_list, "late"),
        peak_periods    = _find_peak_periods(dayun_list),
        caution_periods = _find_caution_periods(dayun_list),
        factor_scores   = {
            "dayun":    f_dayun,
            "geju":     f_geju,
            "strength": f_strength,
            "yongshen": f_yongshen,
        },
        summary = summary,
    )


def life_arc_to_dict(model: LifeArcModel) -> dict:
    """转换为 JSON 可序列化字典"""
    return {
        "overall_tier":    model.overall_tier,
        "total_score":     model.total_score,
        "early_fortune":   model.early_fortune,
        "mid_fortune":     model.mid_fortune,
        "late_fortune":    model.late_fortune,
        "peak_periods":    model.peak_periods,
        "caution_periods": model.caution_periods,
        "factor_scores":   model.factor_scores,
        "summary":         model.summary,
        "disclaimer":      model.disclaimer,
    }
