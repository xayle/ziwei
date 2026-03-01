"""
services/bazi_engine/scoring.py — 八字评分模型 (M3 任务 3.04)

6维加权评分 [0-100]:
  五行均衡(20) + 日主强弱(15) + 用神得力(20) +
  格局高低(15) + 大运趋势(15) + 神煞吉凶(15) = 100

权重说明: "现代命理界通行约定，非古籍原文"
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# 维度权重定义（M3 规格）
DIMENSION_WEIGHTS = {
    "wuxing_balance":    20,   # 五行均衡
    "daymaster_strength": 15,  # 日主强弱
    "yongshen_power":    20,   # 用神得力
    "geju_level":        15,   # 格局高低
    "dayun_trend":       15,   # 大运趋势
    "shensha_luck":      15,   # 神煞吉凶
}
assert sum(DIMENSION_WEIGHTS.values()) == 100, "Weights must sum to 100"


@dataclass
class ScoringDetail:
    """六维评分明细"""
    wuxing_balance:    float  # 五行均衡 [0-20]
    daymaster_strength: float  # 日主强弱 [0-15]
    yongshen_power:    float  # 用神得力 [0-20]
    geju_level:        float  # 格局高低 [0-15]
    dayun_trend:       float  # 大运趋势 [0-15]
    shensha_luck:      float  # 神煞吉凶 [0-15]
    total_score:       float  # 综合分   [0-100]
    tier:              str    # "上命(≥75)"/"中命(50-74)"/"下命(<50)"
    weight_note:       str = "权重约定：现代命理界通行约定，非古籍原文"


# ── 各维度计算函数 ──────────────────────────────────────────────────────────

def _score_wuxing_balance(wuxing_scores: dict[str, float]) -> float:
    """
    五行均衡得分 [0-20]。
    使用五行分值的变异系数衡量均衡度：
      CV = std/mean → 越小越均衡
    """
    import statistics
    vals = list(wuxing_scores.values())
    if not vals or all(v == 0 for v in vals):
        return 8.0   # 中等
    mean = sum(vals) / len(vals)
    if mean == 0:
        return 8.0
    try:
        std = statistics.stdev(vals)
    except statistics.StatisticsError:
        return 12.0
    cv = std / mean          # 变异系数
    # CV=0 → 满分20; CV≥1.5 → 0分
    raw = max(0.0, (1.5 - cv) / 1.5) * 20
    return round(raw, 2)


def _score_daymaster_strength(strength_score: float, strength_tier: str) -> float:
    """
    日主强弱得分 [0-15]。
    中和最优→15, 偏旺/偏弱→10, 极旺/极弱→5
    """
    tier_score = {
        "极旺": 5.0, "偏旺": 10.0, "中和": 15.0,
        "偏弱": 10.0, "极弱": 5.0,
    }
    return float(tier_score.get(strength_tier, 8.0))


def _score_yongshen_power(
    yongshen_favor: list[str],
    wuxing_scores: dict[str, float],
) -> float:
    """
    用神得力得分 [0-20]。
    用神五行在命局中占比越高越好（用神得令）。
    """
    if not yongshen_favor:
        return 10.0
    total = sum(wuxing_scores.values()) or 1.0
    favor_total = sum(wuxing_scores.get(e, 0) for e in yongshen_favor)
    ratio = favor_total / total   # 用神占比
    # 满15%+ → 满分20, 0% → 5分
    raw = 5.0 + min(ratio / 0.15, 1.0) * 15.0
    return round(min(raw, 20.0), 2)


def _score_geju_level(geju_name: str, is_broken: bool) -> float:
    """
    格局高低得分 [0-15]。
    上等格局: 10-15; 中等: 7-10; 下等: 3-7; 破格: 0-4
    """
    if is_broken:
        return 3.0
    _TOP = {"正官格", "正印格", "食神格", "建禄格", "一气专旺格", "羊刃驾杀格"}
    _MID = {"七杀格", "偏印格", "正财格", "偏财格", "伤官格", "羊刃格"}
    if geju_name in _TOP:
        return 13.0
    elif geju_name in _MID:
        return 9.0
    else:
        return 6.0


def _score_dayun_trend(dayun_trend: str, is_favorable: bool) -> float:
    """
    大运趋势得分 [0-15]。
    顺用神上升: 13-15; 平稳: 7-10; 逆用神下降: 2-5
    """
    if is_favorable:
        if dayun_trend == "上升":
            return 14.0
        else:
            return 10.0
    else:
        if dayun_trend == "下降":
            return 3.0
        else:
            return 6.0


def _score_shensha_luck(shensha_items: list[dict]) -> float:
    """
    神煞吉凶得分 [0-15]。
    吉星+2/凶星-1.5，上限15，下限2
    """
    score = 8.0
    for s in shensha_items:
        is_beneficial = s.get("is_beneficial", True)
        score += 2.0 if is_beneficial else -1.5
    return round(min(15.0, max(2.0, score)), 2)


# ── 主评分函数 ─────────────────────────────────────────────────────────────

def compute_bazi_score(
    wuxing_scores: dict[str, float],
    strength_score: float,
    strength_tier: str,
    yongshen_favor: list[str],
    geju_name: str,
    is_broken: bool,
    dayun_trend: str,
    is_favorable_dayun: bool,
    shensha_items: list[dict],
) -> ScoringDetail:
    """
    M3 任务3.04 — 八字综合评分（6维加权）

    返回 ScoringDetail，包含各维度得分与综合分。
    """
    w_balance   = _score_wuxing_balance(wuxing_scores)
    w_strength  = _score_daymaster_strength(strength_score, strength_tier)
    w_yongshen  = _score_yongshen_power(yongshen_favor, wuxing_scores)
    w_geju      = _score_geju_level(geju_name, is_broken)
    w_dayun     = _score_dayun_trend(dayun_trend, is_favorable_dayun)
    w_shensha   = _score_shensha_luck(shensha_items)

    total = w_balance + w_strength + w_yongshen + w_geju + w_dayun + w_shensha

    if total >= 75:
        tier = "上命"
    elif total >= 50:
        tier = "中命"
    else:
        tier = "下命"

    return ScoringDetail(
        wuxing_balance    = round(w_balance,  2),
        daymaster_strength = round(w_strength, 2),
        yongshen_power    = round(w_yongshen, 2),
        geju_level        = round(w_geju,     2),
        dayun_trend       = round(w_dayun,    2),
        shensha_luck      = round(w_shensha,  2),
        total_score       = round(total,      2),
        tier              = tier,
    )


def scoring_to_dict(detail: ScoringDetail) -> dict:
    """转换为 JSON 可序列化的字典"""
    return {
        "dimensions": {
            "wuxing_balance":    {"score": detail.wuxing_balance,    "weight": DIMENSION_WEIGHTS["wuxing_balance"]},
            "daymaster_strength": {"score": detail.daymaster_strength, "weight": DIMENSION_WEIGHTS["daymaster_strength"]},
            "yongshen_power":    {"score": detail.yongshen_power,    "weight": DIMENSION_WEIGHTS["yongshen_power"]},
            "geju_level":        {"score": detail.geju_level,        "weight": DIMENSION_WEIGHTS["geju_level"]},
            "dayun_trend":       {"score": detail.dayun_trend,       "weight": DIMENSION_WEIGHTS["dayun_trend"]},
            "shensha_luck":      {"score": detail.shensha_luck,      "weight": DIMENSION_WEIGHTS["shensha_luck"]},
        },
        "total_score":  detail.total_score,
        "tier":         detail.tier,
        "weight_note":  detail.weight_note,
    }
