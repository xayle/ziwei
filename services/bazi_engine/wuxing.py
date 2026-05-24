"""
services/bazi_engine/wuxing.py — 五行计分引擎（含藏干权重贡献）

M1 任务 1.03: 修复 S6/P63 — compute_wuxing() hidden_contrib 全零 bug
- 天干贡献: 每支天干 +1.0（权重=1.0）
- 地支主气贡献: 按 BRANCH_HIDDEN_STEMS 主气权重（通常0.6）× 0.5 折算
- 藏干贡献: 全部藏干按权重 × 0.3 折算（分别统计到各五行）
- 输出: counts_basic + scores_weighted
- 附: missing_elements + dominant_elements(>40%)
- 验证: hidden_contrib ≠ {}
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from services.bazi_engine.tables import (
    BRANCH_HIDDEN_STEMS,
    BRANCHES,
    STEM_ELEMENT,
    STEMS,
    WANGXIANG,
)

ELEMENTS = ("wood", "fire", "earth", "metal", "water")

ELEMENTS_CN: dict[str, str] = {
    "wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"
}


@dataclass
class WuxingResult:
    """五行计算结果（M1 v2，含藏干贡献）"""

    # 基础计数（天干+地支本气各1.0，无权重）
    counts_basic: dict[str, float] = field(default_factory=dict)

    # 加权得分（天干×1.0 + 地支本气×0.6 + 地支藏干× 权重×0.3）
    # 最终归一化到 0-100
    scores_weighted: dict[str, float] = field(default_factory=dict)

    # 分项贡献（用于调试/展示）
    stem_contrib: dict[str, float] = field(default_factory=dict)
    branch_hidden_contrib: dict[str, float] = field(default_factory=dict)  # 地支全部藏干贡献

    # 附加分析
    missing_elements: list[str] = field(default_factory=list)    # 完全为0的五行
    dominant_elements: list[str] = field(default_factory=list)  # 占比 > 40%

    # 月令加持系数（供 strength.py 使用）
    month_branch_wangxiang: dict[str, int] = field(default_factory=dict)


def _elem_of_stem(stem: str) -> Optional[str]:
    return STEM_ELEMENT.get(stem, (None, None))[0]  # type: ignore[return-value]


def compute_wuxing(
    year_stem: str,
    year_branch: str,
    month_stem: str,
    month_branch: str,
    day_stem: str,
    day_branch: str,
    hour_stem: str,
    hour_branch: str,
) -> WuxingResult:
    """
    计算八字四柱五行分布（含藏干权重贡献）。

    权重分配方案（v4 规范）:
      天干: ×1.0（透出天干力量最强）
      地支藏干: ×0.3 × 该藏干在地支中的权重（主气0.6×0.3=0.18, 中气0.3×0.3=0.09, 余气0.1×0.3=0.03）
    """
    stem_contrib: dict[str, float] = {e: 0.0 for e in ELEMENTS}
    branch_hidden_contrib: dict[str, float] = {e: 0.0 for e in ELEMENTS}

    stems = [year_stem, month_stem, day_stem, hour_stem]
    branches = [year_branch, month_branch, day_branch, hour_branch]

    # 天干贡献
    for stem in stems:
        elem = _elem_of_stem(stem)
        if elem:
            stem_contrib[elem] += 1.0

    # 地支藏干贡献（含所有藏干，按权重×0.3折算）
    for branch in branches:
        hidden = BRANCH_HIDDEN_STEMS.get(branch, [])
        for hidden_stem, weight in hidden:
            elem = _elem_of_stem(hidden_stem)
            if elem:
                branch_hidden_contrib[elem] += weight * 0.3

    # 合并得分（加权）
    scores_weighted_raw = {e: stem_contrib[e] + branch_hidden_contrib[e] for e in ELEMENTS}
    total_weighted = sum(scores_weighted_raw.values()) or 1.0
    scores_weighted = {e: round(v / total_weighted * 100, 2) for e, v in scores_weighted_raw.items()}

    # 基础计数（天干+地支本气各1.0，不含中余气）
    counts_basic: dict[str, float] = {e: 0.0 for e in ELEMENTS}
    for stem in stems:
        elem = _elem_of_stem(stem)
        if elem:
            counts_basic[elem] += 1.0
    for branch in branches:
        hidden = BRANCH_HIDDEN_STEMS.get(branch, [])
        if hidden:
            main_stem, _ = hidden[0]  # 主气
            elem = _elem_of_stem(main_stem)
            if elem:
                counts_basic[elem] += 1.0

    # 月令旺相
    month_wangxiang = WANGXIANG.get(month_branch, {})

    # 附加分析
    missing = [e for e in ELEMENTS if scores_weighted.get(e, 0) < 1.0]
    dominant = [e for e in ELEMENTS if scores_weighted.get(e, 0) > 40.0]

    return WuxingResult(
        counts_basic=counts_basic,
        scores_weighted=scores_weighted,
        stem_contrib=stem_contrib,
        branch_hidden_contrib=branch_hidden_contrib,
        missing_elements=missing,
        dominant_elements=dominant,
        month_branch_wangxiang=month_wangxiang,
    )


def compute_shishen_scores(
    day_stem: str,
    year_stem: str,
    month_stem: str,
    hour_stem: str,
    year_branch: str,
    month_branch: str,
    day_branch: str,
    hour_branch: str,
) -> dict[str, float]:
    """
    计算十神得分分布（各十神在八字中的累积权重）。
    用于 wealth/career/marriage 分析引擎输入。

    :return: dict，如 {"正财": 1.8, "七杀": 0.9, ...}
    """
    from services.bazi_engine.tables import get_ten_god

    scores: dict[str, float] = {}

    stems_with_weight = [
        (year_stem, 1.0),
        (month_stem, 1.0),
        (hour_stem, 1.0),
        # day_stem 本身是"日主"，不计入十神
    ]

    for stem, w in stems_with_weight:
        tg = get_ten_god(day_stem, stem)
        scores[tg] = scores.get(tg, 0.0) + w

    # 地支藏干
    branches = [year_branch, month_branch, day_branch, hour_branch]
    for branch in branches:
        hidden = BRANCH_HIDDEN_STEMS.get(branch, [])
        for hidden_stem, weight in hidden:
            if hidden_stem == day_stem:
                continue  # 跳过与日主相同的藏干
            tg = get_ten_god(day_stem, hidden_stem)
            scores[tg] = scores.get(tg, 0.0) + weight * 0.3

    return scores
