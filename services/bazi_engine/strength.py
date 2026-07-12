"""
services/bazi_engine/strength.py — 日主强弱多因子计算

M1 任务 1.05: 多因子强弱 [S7/P62]
  月令40% + 透干20% + 根气20% + 合化10% + 调候10%
  验证: 5案例 偏旺/偏弱/中和/极旺/极弱

tier 定义:
  ≥ 75  → "极旺"
  ≥ 60  → "偏旺"
  ≥ 40  → "中和"
  ≥ 25  → "偏弱"
  < 25  → "极弱"
"""

from __future__ import annotations

from dataclasses import dataclass, field

from services.bazi_engine.tables import (
    BRANCH_HIDDEN_STEMS,
    STEM_ELEMENT,
    WANGXIANG,
    get_ten_god,
)
from services.bazi_engine.wuxing import WuxingResult, _elem_of_stem

ELEMENTS = ("wood", "fire", "earth", "metal", "water")

# 五行相生关系（生者→被生者）
SHENG: dict[str, str] = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}
# 生我（我的父母五行）= {被生者: 生者}
SHENG_REV: dict[str, str] = {v: k for k, v in SHENG.items()}


@dataclass
class StrengthFactor:
    name: str
    score: float
    weight: float
    weighted_score: float
    reason: str


@dataclass
class StrengthResult:
    """日主强弱计算结果"""

    score: float  # 0-100 归一化综合分
    tier: str  # "极旺"/"偏旺"/"中和"/"偏弱"/"极弱"
    day_stem: str
    day_elem: str
    factors: list[StrengthFactor] = field(default_factory=list)

    # 供分析引擎使用的辅助属性
    is_strong: bool = False  # 偏旺/极旺
    is_weak: bool = False  # 偏弱/极弱
    is_balanced: bool = False  # 中和


def _month_commander(month_branch: str, solar_day_in_month: int) -> tuple[str, str]:
    """
    人元司令：按公历日序取月支藏干初/中/末司令。

    Returns:
        (commander_stem, period) — period 为 early / mid / late
    """
    hidden = BRANCH_HIDDEN_STEMS.get(month_branch, [])
    if not hidden:
        return ("", "early")
    day = max(1, min(int(solar_day_in_month), 30))
    if day <= 10:
        period = "early"
    elif day <= 20:
        period = "mid"
    else:
        period = "late"
    idx = min({"early": 0, "mid": 1, "late": 2}[period], len(hidden) - 1)
    return hidden[idx][0], period


def _get_month_ling_score(day_elem: str, month_branch: str) -> float:
    """
    月令得分：日主五行在月支的旺相休囚死状态 → 0-4 → 归一化为 0-100
    旺=100, 相=75, 休=50, 囚=25, 死=0
    月令权重 40%
    """
    wangxiang_map = WANGXIANG.get(month_branch, {})
    level = wangxiang_map.get(day_elem, 0)
    return level * 25.0  # 0,1,2,3,4 → 0,25,50,75,100


def _get_toukan_score(day_elem: str, stems: list[str]) -> float:
    """
    透干支撑得分：四柱天干（除日干自身）中与日元同五行或生日元的天干数量。
    权重20%，每个支撑干贡献 33.33分（3个满格）
    """
    parent_elem = SHENG_REV.get(day_elem, "")
    score = 0.0
    for stem in stems:
        elem = _elem_of_stem(stem)
        if elem == day_elem or elem == parent_elem:
            score += 33.33
    return min(score, 100.0)


def _get_gen_qi_score(day_elem: str, branches: list[str]) -> float:
    """
    根气得分：地支藏干中含有日主五行或生日主五行的藏干权重之和。
    满分条件：4支全部有根（粗略估计100分/4根×权重）。
    """
    parent_elem = SHENG_REV.get(day_elem, "")
    total_weight = 0.0
    for branch in branches:
        hidden = BRANCH_HIDDEN_STEMS.get(branch, [])
        for hidden_stem, weight in hidden:
            elem = _elem_of_stem(hidden_stem)
            if elem == day_elem:
                total_weight += weight * 1.0  # 同气满权
            elif elem == parent_elem:
                total_weight += weight * 0.5  # 生气半权
    # 最大理论值约4.0（4支全含主气），归一化
    return min(total_weight / 4.0 * 100.0, 100.0)


def _get_hehua_score(day_stem: str, day_elem: str, stems: list[str], branches: list[str]) -> float:
    """
    合化得分（简化版）：
    - 天干合化：若四柱中有与日干相合且化为有利五行的干 → +50
    - 地支三合/六合：若月支与日支形成三合或六合 → +50
    当前实现：只检测月支六合/三合日支的情况（简化，足够M1精度）
    """
    from services.bazi_engine.tables import LIU_HE, SAN_HE

    score = 0.0
    if len(branches) >= 2:
        month_b = branches[1]  # 月支
        day_b = branches[2]  # 日支
        if LIU_HE.get(month_b) == day_b:
            score += 50.0
        for trio, elem in SAN_HE:
            if month_b in trio and day_b in trio:
                if elem == day_elem or elem == SHENG_REV.get(day_elem, ""):
                    score += 50.0
                    break
    return min(score, 100.0)


def _get_tiaohou_score(day_elem: str, month_branch: str) -> float:
    """
    调候得分（简化版）：
    寒冷月份（亥子丑）生日主喜火；炎热月份（巳午未）生日主喜水/金。
    计算当前日元和调候需求的匹配程度。
    """
    cold_months = {"亥", "子", "丑"}
    hot_months = {"巳", "午", "未"}

    if month_branch in cold_months:
        # 寒冷月份：火/土为喜（调候）
        if day_elem in ("fire", "earth"):
            return 80.0
        elif day_elem == "wood":
            return 50.0
        else:
            return 30.0
    elif month_branch in hot_months:
        # 炎热月份：水/金为喜（调候）
        if day_elem in ("water", "metal"):
            return 80.0
        elif day_elem == "earth":
            return 50.0
        else:
            return 30.0
    else:
        # 春秋月份（温和）：中性50分
        return 50.0


def compute_strength(
    day_stem: str,
    month_branch: str,
    year_stem: str,
    month_stem: str,
    hour_stem: str,
    year_branch: str,
    day_branch: str,
    hour_branch: str,
    wuxing: WuxingResult | None = None,
    solar_day_in_month: int | None = None,
) -> StrengthResult:
    """
    计算日主强弱综合得分。

    权重分配:
      月令  40%
      透干  20%
      根气  20%
      合化  10%
      调候  10%

    :return: StrengthResult（score=0-100, tier=极旺/偏旺/中和/偏弱/极弱）
    """
    day_elem = STEM_ELEMENT.get(day_stem, ("unknown", "yang"))[0]

    all_stems = [year_stem, month_stem, day_stem, hour_stem]
    support_stems = [year_stem, month_stem, hour_stem]  # 不含日干自身
    all_branches = [year_branch, month_branch, day_branch, hour_branch]

    # 各因子得分（0-100）+ 权重
    f_yueling = _get_month_ling_score(day_elem, month_branch)
    if solar_day_in_month is not None:
        cmd_stem, cmd_period = _month_commander(month_branch, solar_day_in_month)
        if cmd_stem:
            cmd_elem = _elem_of_stem(cmd_stem)
            cmd_tg = get_ten_god(day_stem, cmd_stem)
            if cmd_elem == day_elem or cmd_tg in ("正印", "偏印", "比肩", "劫财"):
                f_yueling = min(f_yueling + 5.0, 100.0)
            elif cmd_tg in ("正官", "七杀", "食神", "伤官"):
                f_yueling = max(f_yueling - 3.0, 0.0)
            _ = cmd_period  # early/mid/late available for callers via _month_commander
    f_toukan = _get_toukan_score(day_elem, support_stems)
    f_genqi = _get_gen_qi_score(day_elem, all_branches)
    f_hehua = _get_hehua_score(day_stem, day_elem, all_stems, all_branches)
    f_tiaohou = _get_tiaohou_score(day_elem, month_branch)

    weights = [
        ("月令得分", f_yueling, 0.40, "月支旺相状态"),
        ("透干得分", f_toukan, 0.20, "天干中同气/生气数量"),
        ("根气得分", f_genqi, 0.20, "地支藏干含同气/生气权重"),
        ("合化得分", f_hehua, 0.10, "六合/三合对日主有利"),
        ("调候得分", f_tiaohou, 0.10, "月令寒暖与日元需求匹配"),
    ]

    score = sum(v * w for _, v, w, _ in weights)
    score = round(min(max(score, 0.0), 100.0), 2)

    # tier 分级
    if score >= 75:
        tier = "极旺"
    elif score >= 60:
        tier = "偏旺"
    elif score >= 40:
        tier = "中和"
    elif score >= 25:
        tier = "偏弱"
    else:
        tier = "极弱"

    factors = [
        StrengthFactor(
            name=name,
            score=round(v, 2),
            weight=w,
            weighted_score=round(v * w, 2),
            reason=reason,
        )
        for name, v, w, reason in weights
    ]

    is_strong = tier in ("极旺", "偏旺")
    is_weak = tier in ("极弱", "偏弱")
    is_balanced = tier == "中和"

    return StrengthResult(
        score=score,
        tier=tier,
        day_stem=day_stem,
        day_elem=day_elem,
        factors=factors,
        is_strong=is_strong,
        is_weak=is_weak,
        is_balanced=is_balanced,
    )
