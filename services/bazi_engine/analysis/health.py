"""
services/bazi_engine/analysis/health.py — 健康引擎 (M2 任务 2.04)

算法规格: §4.11-D
"""
from __future__ import annotations

from app.schemas.analysis import HealthAnalysisModel

# 五行→脏腑
_WUXING_TO_ORGAN: dict[str, list[str]] = {
    "wood":  ["肝", "胆"],
    "fire":  ["心", "小肠"],
    "earth": ["脾", "胃"],
    "metal": ["肺", "大肠"],
    "water": ["肾", "膀胱"],
}

# 五行中文
_ELEMENT_CN: dict[str, str] = {
    "metal": "金", "wood": "木", "water": "水", "fire": "火", "earth": "土",
}

# 五行→养生建议
_WUXING_TO_HEALTH_ADVICE: dict[str, str] = {
    "wood":  "保护肝胆，适量运动，避免过度劳累，少饮酒。",
    "fire":  "注意心血管，保持平和心态，避免过度兴奋。",
    "earth": "调理脾胃，规律饮食，避免暴饮暴食。",
    "metal": "保护肺大肠，注意呼吸道，适当户外活动。",
    "water": "保护肾膀胱，注意腰膝保暖，避免过度劳神。",
}

# 五行→运动建议
_WUXING_TO_EXERCISE: dict[str, str] = {
    "wood":  "太极、瑜伽、有氧慢跑",
    "fire":  "游泳、冥想、柔和运动",
    "earth": "快走、健身操、轻量运动",
    "metal": "户外呼吸操、登山、骑行",
    "water": "拉伸、低强度有氧、水中运动",
}

# 五行→饮食建议
_WUXING_TO_DIET: dict[str, str] = {
    "wood":  "多食绿色蔬菜，减少辛辣刺激",
    "fire":  "多食苦瓜、莲子等清心食物，减少辛辣",
    "earth": "多食黄色食物（玉米、南瓜），规律三餐",
    "metal": "多食白色食物（梨、白萝卜），润肺养气",
    "water": "多食黑色食物（黑豆、核桃），补肾固元",
}


def compute_health(
    wuxing_scores: dict[str, float],   # {"wood":..., "fire":..., ...}
    yongshen_favor: list[str],
    yongshen_avoid: list[str],
    day_stem: str = "",
) -> HealthAnalysisModel:
    """
    §4.11-D 健康引擎

    Parameters:
        wuxing_scores:  五行得分字典
        yongshen_favor: 用神五行（英文）
        yongshen_avoid: 忌神五行
        day_stem:       日干
    """
    total = sum(wuxing_scores.values()) or 1.0

    # ─── 1. 五行偏旺/偏弱判断 ───────────────────────────────────────────
    avg = total / 5
    strong_wuxing: list[str] = []
    weak_wuxing:   list[str] = []

    for el, score in wuxing_scores.items():
        ratio = score / total
        if ratio > 0.40:  # 偏旺
            strong_wuxing.append(el)
        if ratio < 0.10:  # 偏弱
            weak_wuxing.append(el)

    # ─── 2. 风险脏腑 ──────────────────────────────────────────────────
    risk_organs: list[str] = []
    for el in strong_wuxing:
        for organ in _WUXING_TO_ORGAN.get(el, []):
            labeled = f"{organ}（偏旺需节制）"
            if labeled not in risk_organs:
                risk_organs.append(labeled)
    for el in weak_wuxing:
        for organ in _WUXING_TO_ORGAN.get(el, []):
            labeled = f"{organ}（偏弱需滋补）"
            if labeled not in risk_organs:
                risk_organs.append(labeled)

    # ─── 3. 风险等级 ──────────────────────────────────────────────────
    weak_count = len(weak_wuxing)
    if weak_count >= 2:
        risk_level = "高"
    elif weak_count == 1:
        risk_level = "中"
    else:
        risk_level = "低"

    # ─── 4. 健康评分 ──────────────────────────────────────────────────
    # 最大五行比例偏差
    max_ratio = max(wuxing_scores.values()) / total if wuxing_scores else 0.2
    deviation = abs(max_ratio - 0.2) * 100  # 均匀分布时每个20%
    health_score = int(min(100, max(0, round(100 - min(deviation * 3, 40)))))

    # ─── 5. 养生/运动/饮食（优先推荐用神五行方向） ─────────────────────
    if yongshen_favor:
        prim_el = yongshen_favor[0]
    elif wuxing_scores:
        prim_el = min(wuxing_scores.keys(), key=lambda k: wuxing_scores[k])
    else:
        prim_el = "earth"

    health_advice = _WUXING_TO_HEALTH_ADVICE.get(prim_el, "保持作息规律，定期体检。")
    exercise      = [
        _WUXING_TO_EXERCISE.get(prim_el, "适量有氧运动"),
        "每天快走 30 分钟，降低循环血压力、增强心肺功能",
        "每周两次拉伸或正念练习以放松神经、缓解压力",
    ]
    diet          = [
        _WUXING_TO_DIET.get(prim_el, "均衡饮食，清淡为主"),
        "每日饮水不少于 1500ml，额外补充新鲜蔬果",
        "少食加工食品和高糖饮料，减少内脏负担",
        "晚餐应在 19:00 前完成，防止影响消化与睡眠",
    ]

    # ─── 6. 旺盛期 ─────────────────────────────────────────────────────
    if yongshen_favor:
        el_cn = "、".join(_ELEMENT_CN.get(e, e) for e in yongshen_favor)
        peak_period = f"用神（{el_cn}）旺运期间精力充沛，为身体调养最佳时机"
    else:
        peak_period = "格局均衡，各大运均较平稳"

    # ─── inference_tags ─────────────────────────────────────────────
    tags = []
    for el in strong_wuxing:
        tags.append(f"{_ELEMENT_CN.get(el,el)}偏旺慎{''.join(_WUXING_TO_ORGAN.get(el,[]))}")
    for el in weak_wuxing:
        tags.append(f"{_ELEMENT_CN.get(el,el)}偏弱需补{''.join(_WUXING_TO_ORGAN.get(el,[]))}")
    if not tags:
        tags.append("五行均衡，体质较佳")

    _risk_str = ("风险脏腑：" + "、".join(risk_organs[:3]) + "。") if risk_organs else "脏腑整体平衡。"
    _ex_top = exercise[0]
    _diet_top = diet[0]
    interp = (
        f"健康评分为 {health_score} 分，整体风险等级【{risk_level}】。"
        f"{_risk_str}"
        f"运动建议：以「{_ex_top}」为主，配合每天快走与舒展，延缓升火气。"
        f"饮食建议：{_diet_top}，配合充足水分摄入与规律三餐。"
        f"旺盛期参考：{peak_period}。"
        f"（仅供学术研究参考）"
    )

    return HealthAnalysisModel(
        health_score=health_score,
        risk_organs=risk_organs,
        risk_level=risk_level,
        health_advice=health_advice,
        exercise=exercise,
        diet=diet,
        peak_period=peak_period,
        inference_tags=tags,
        interpretation_text=interp,
    )
