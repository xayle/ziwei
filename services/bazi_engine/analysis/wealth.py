"""
services/bazi_engine/analysis/wealth.py — 财运引擎 (M2 任务 2.01)

算法规格: §4.11-A
输入:
    yongshen: YongShenResult
    wuxing:   WuxingResult
    shishen:  dict[str, float]     # 十神得分分布
    dayun_list: list[dict]         # 大运列表
输出:
    WealthAnalysisModel
验证:
    wealth_score ≠ strength.score
    tier in {"上","中","下"}
    industries 非空列表
"""
from __future__ import annotations

from app.schemas.analysis import WealthAnalysisModel

# 五行→行业映射
_WUXING_TO_INDUSTRIES: dict[str, list[str]] = {
    "metal":  ["金融", "律政", "机械制造", "珠宝"],
    "wood":   ["教育", "医药", "农林", "食品", "出版"],
    "water":  ["贸易", "运输", "IT", "资讯", "旅游"],
    "fire":   ["传媒", "餐饮", "能源", "娱乐演艺"],
    "earth":  ["房地产", "保险", "建筑", "农业"],
}

# 地支六冲对照
_BRANCH_CHONG: dict[str, str] = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}

# 天干五行（简化映射）
_STEM_ELEMENT: dict[str, str] = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth", "己": "earth",
    "庚": "metal", "辛": "metal",
    "壬": "water", "癸": "water",
}

# 地支五行
_BRANCH_ELEMENT: dict[str, str] = {
    "子": "water", "亥": "water",
    "寅": "wood", "卯": "wood",
    "巳": "fire", "午": "fire",
    "申": "metal", "酉": "metal",
    "丑": "earth", "辰": "earth", "未": "earth", "戌": "earth",
}

# 相生关系（A生B）
_SHENG: dict[str, str] = {
    "wood": "fire", "fire": "earth", "earth": "metal",
    "metal": "water", "water": "wood",
}

# 五行对应中文
_ELEMENT_CN: dict[str, str] = {
    "metal": "金", "wood": "木", "water": "水", "fire": "火", "earth": "土",
}


def compute_wealth(
    yongshen_favor: list[str],
    yongshen_avoid: list[str],
    wuxing_scores: dict[str, float],      # {"wood":..., "fire":..., ...}
    shishen_scores: dict[str, float],     # {"正财":..., "偏财":..., ...}
    strength_score: float,                # 日主强弱分（0-100）
    dayun_list: list[dict],               # 大运列表（每项含 stem/branch/ganzhi）
    day_branch: str = "",                 # 日支（用于地支冲断言）
) -> WealthAnalysisModel:
    """
    §4.11-A 财运引擎

    Parameters:
        yongshen_favor:  用神五行列表（英文，如 ["metal","water"]）
        yongshen_avoid:  忌神五行列表
        wuxing_scores:   五行原始得分字典
        shishen_scores:  十神得分分布
        strength_score:  日主强弱分
        dayun_list:      大运列表
        day_branch:      日支

    Returns:
        WealthAnalysisModel
    """
    # ─── 1. 财星力量 ────────────────────────────────────────────────────────
    zheng_cai = shishen_scores.get("正财", 0.0)
    pian_cai  = shishen_scores.get("偏财", 0.0)
    total_shishen = sum(shishen_scores.values()) or 1.0
    cai_power = (zheng_cai * 1.0 + pian_cai * 0.8) / total_shishen * 100  # 归一化

    # ─── 2. 用神匹配度 ─────────────────────────────────────────────────────
    # 财星五行属于哪些：正财/偏财对应的五行（需要从 wuxing 得分判断）
    total_wx = sum(wuxing_scores.values()) or 1.0
    yongshen_match = sum(
        wuxing_scores.get(e, 0.0) for e in yongshen_favor
    ) / total_wx * 100

    # ─── 3. 月令旺衰系数 ────────────────────────────────────────────────────
    # 简化：用最大五行占比作为旺衰指标（30-50为均衡=0.5；>50为旺）
    max_wx = max(wuxing_scores.values()) if wuxing_scores else 0
    if total_wx > 0:
        max_ratio = max_wx / total_wx
    else:  # pragma: no cover
        max_ratio = 0.0
    wangshuai_coeff = min(1.0, max(0.0, (max_ratio - 0.2) / 0.6))

    # ─── 合计分数 ─────────────────────────────────────────────────────────
    raw_score = cai_power * 0.5 + yongshen_match * 0.3 + wangshuai_coeff * 100 * 0.2

    # 身弱财旺反向修正
    if strength_score < 30:
        raw_score = raw_score * (strength_score / 50)

    wealth_score = int(min(100, max(0, round(raw_score))))

    # tier
    if wealth_score >= 70:
        tier = "上"
    elif wealth_score >= 40:
        tier = "中"
    else:
        tier = "下"

    # ─── 4. 年收入区间估算 ─────────────────────────────────────────────────
    if tier == "上":
        annual_range = "80-200万/年"
    elif tier == "中":
        annual_range = "20-80万/年"
    else:
        annual_range = "10-30万/年"

    # ─── 5. 行业推荐 ─────────────────────────────────────────────────────
    industries: list[str] = []
    for el in yongshen_favor:
        industries.extend(_WUXING_TO_INDUSTRIES.get(el, []))
    if not industries:
        industries = ["贸易", "实业"]
    industries = list(dict.fromkeys(industries))[:5]  # 去重，取前5

    # ─── 6. 大运趋势 ─────────────────────────────────────────────────────
    dayun_forecast: list[dict] = []
    for item in dayun_list:
        gz = item.get("ganzhi") or (
            (item.get("stem") or "") + (item.get("branch") or "")
        )
        stem  = item.get("stem", "")
        branch = item.get("branch", "")
        stem_el   = _STEM_ELEMENT.get(stem, "")
        branch_el = _BRANCH_ELEMENT.get(branch, "")

        # 天干与日主关系：先判断基础趋势
        if stem_el and yongshen_favor and stem_el in yongshen_favor:
            trend = "上升"
        elif stem_el and yongshen_avoid and stem_el in yongshen_avoid:
            trend = "下降"
        else:
            trend = "平稳"

        # 地支修正：冲日支 → 降级
        if day_branch and branch and _BRANCH_CHONG.get(branch) == day_branch:
            if trend == "上升":
                trend = "平稳"
            elif trend == "平稳":
                trend = "下降"
        # 地支与用神五行同气 → 升级
        elif branch_el and yongshen_favor and branch_el in yongshen_favor:
            if trend == "下降":
                trend = "平稳"
            elif trend == "平稳":
                trend = "上升"

        dayun_forecast.append({"ganzhi": gz, "trend": trend})

    # ─── 7. 策略建议 ─────────────────────────────────────────────────────
    if tier == "上":
        strategy = "财运旺盛，适合主动开拓增量，投资需留意过于分散。"
    elif tier == "中":
        strategy = "稳中求进，守住正职收入同时适度投资，避免贸然冒进。"
    else:
        strategy = "守成为主，节流优先，宜积累基础后再寻拓展时机。"

    # ─── inference_tags ─────────────────────────────────────────────────
    tags = []
    if zheng_cai > 0.5:
        tags.append("正财有根")
    if pian_cai > 0.5:
        tags.append("偏财有力")
    if yongshen_favor:
        tags.append(f"用神{''.join(_ELEMENT_CN.get(e, e) for e in yongshen_favor)}")
    if strength_score < 30:
        tags.append("财多身弱主贫困警示")

    # ─── interpretation_text ────────────────────────────────────────────
    interp = (
        f"此命财运评分{wealth_score}分（{tier}等），"
        f"财星力量{cai_power:.0f}/100，用神五行为"
        f"{'、'.join(_ELEMENT_CN.get(e, e) for e in yongshen_favor) or '未知'}。"
        f"推荐发展行业：{'、'.join(industries[:3])}。"
        f"{strategy}"
        f"（仅供学术研究参考）"
    )

    return WealthAnalysisModel(
        wealth_score=wealth_score,
        wealth_tier=tier,
        annual_range=annual_range,
        industries=industries,
        strategy=strategy,
        dayun_forecast=dayun_forecast,
        inference_tags=tags,
        interpretation_text=interp,
    )
