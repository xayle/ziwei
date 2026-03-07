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

    # ─── 新增：季节健康预警模板 ──────────────────────────────────────────
    _SEASONAL_HEALTH: dict[str, str] = {
        "wood": (
            "春季（2-4月）肝胆气机旺盛，宜疏泄情绪、避免「春困」积郁引发肝气郁结；"
            "夏季可借助心火疏通气血；秋季燥金克木，是肝病与情绪问题的高发期，需提前养护。"
            "建议春分前后加强户外有氧活动，秋分后减少精神刺激，以菊花茶、枸杞调护肝目，"
            "每晚23点前入睡让肝脏充分排毒修复。"
        ),
        "fire": (
            "夏季（6-8月）心火偏旺，心血管压力增大，需尽量避免高温下的剧烈运动；"
            "冬季水旺克火，心脏功能相对减弱，需注意保暖防寒、减少高盐高脂饮食。"
            "建议夏季作息宜早睡早起，午间小憩20分钟养心；冬季补充维生素D与欧米伽-3，"
            "加强核心区域保暖，尤其保护后背心脏投影区域。"
        ),
        "earth": (
            "长夏（7-8月梅雨季）湿气重，脾胃负担加重，最易出现消化不良与湿困乏力；"
            "秋燥期脾胃功能较旺，是滋补调理的最佳时机。"
            "建议梅雨季减少甜腻食物，多食薏仁、赤豆、山药、茯苓祛湿健脾；"
            "秋季适当进补但勿过补伤胃，餐后散步10-15分钟促进脾胃运化。"
        ),
        "metal": (
            "秋季（9-11月）燥气重，肺与大肠最易受损，需格外注意呼吸道防护与皮肤保湿；"
            "春季木旺过盛时可能连带影响脾土，间接引发肺肾功能下降。"
            "建议秋季常备润肺食材（梨、百合、银耳、麦冬），保持室内湿度45%-65%，"
            "雾霾天出门佩戴高效防护口罩，每日坚持腹式呼吸10分钟强化肺活量。"
        ),
        "water": (
            "冬季（11月-次年1月）是肾精消耗的高峰期，切忌过度劳神与房事过频，防止肾气亏损；"
            "夏季土旺克水，容易出现腰膝无力、水肿等肾虚信号，需提前调护。"
            "建议冬至前后服用黑芝麻、核桃、枸杞子、桑葚等补肾食材；"
            "夏季避免久站久坐，加强腰背部肌肉锻炼，每晚睡前搓腰眼（双手搓热后按摩腰骶区3分钟）。"
        ),
    }
    seasonal_health = _SEASONAL_HEALTH.get(
        prim_el,
        "根据季节变化调整作息与饮食，遵循春养肝、夏养心、长夏养脾、秋养肺、冬养肾的节律，顺应自然养生。",
    )

    # ─── 新增：心理健康建议模板 ──────────────────────────────────────────
    _MENTAL_HEALTH: dict[str, str] = {
        "wood": (
            "木性命局者心理能量充沛，但情绪张力较高，容易因外部阻力积累愤怒与挫败感，"
            "最大心理风险为长期压抑后突然爆发，损伤亲密关系。"
            "调适建议：每周安排1次「情绪清空」时间（跑步/倾诉/写日记），"
            "主动学习接纳式沟通技巧，将竞争驱动力转化为自我成长动力；"
            "若感到情绪频繁积压，建议尝试EFT情绪释放疗法或正念冥想课程。"
        ),
        "fire": (
            "火性命局者情绪高扬表达充沛，但持续性焦虑与注意力涣散是主要心理隐患，"
            "最大风险为被情绪驱动做出冲动决策，事后追悔。"
            "调适建议：建立「24小时冷却期」决策习惯，在强烈情绪下推迟到次日再做正式决定；"
            "冥想与正念练习可显著降低情绪波动基线，建议每天8-10分钟；"
            "减少咖啡因摄入，增加规律睡眠，防止情绪过激的生理性触发。"
        ),
        "earth": (
            "土性命局者稳定踏实，但过度担忧与反刍思维是主要心理障碍，"
            "容易对未知变化产生持续焦虑，消耗决策能量。"
            "调适建议：为每个「担忧项」建立行动清单，将模糊焦虑具象化为可管理的待办事项；"
            "正念呼吸与身体扫描练习是最适合土性的减压工具；"
            "每周设定「担忧专属时段」（如周三20点集中处理所有焦虑），避免全天候焦虑模式。"
        ),
        "metal": (
            "金性命局者自律高效，但完美主义与低自我慈悲是主要心理困境，"
            "容易在失败或不完美时产生严苛的自责循环，长期导致内在动力枯竭。"
            "调适建议：建立「成长日志」每日记录进步（哪怕很小），用自我肯定替代自我批评；"
            "定期参与非竞技性纯享受活动，让大脑从「成就评估模式」中解脱；"
            "若自我批评模式持续超过2周，建议咨询CBT（认知行为疗法）。"
        ),
        "water": (
            "水性命局者感受力深刻、情绪共情力强，但情绪沉浸与忧郁倾向是主要心理隐患，"
            "最大风险为将内心忧郁放大并持续沉浸，逐渐与现实生活脱节。"
            "调适建议：建立「情绪退出仪式」（深呼吸+感恩清单），强制引导大脑切换到行动状态；"
            "规律有氧运动（每周3次以上）是缓解水性忧郁最有效的工具；"
            "构建3-5人的深度支持网络，在情绪低谷时有可信赖的倾诉对象而非独自承受。"
        ),
    }
    mental_health_advice = _MENTAL_HEALTH.get(
        prim_el,
        "保持规律作息与运动，建立情绪日记习惯，在感受强烈情绪时主动寻求支持而非独自承受。",
    )

    # ─── 新增：体质类型模板 ─────────────────────────────────────────────
    _CONSTITUTION: dict[str, str] = {
        "wood": (
            "体质类型：气郁质 × 阴虚质混合型。"
            "肝气容易郁结，长期情绪紧张者可能伴有入睡困难、口苦咽干、胁肋不适等典型症状。"
            "调理重点：疏肝理气（玫瑰花、佛手、香附、柴胡）配合滋阴（枸杞、制首乌、女贞子），"
            "避免过激情绪波动与熬夜，配合有氧运动（太极/瑜伽/慢跑）促进肝气流动。"
        ),
        "fire": (
            "体质类型：阴虚火旺质。"
            "心火偏旺者常见心烦易怒、失眠多梦、手脚心发热等上火症状，长期可导致心血亏耗。"
            "调理重点：滋阴降火（生地、麦冬、五味子、莲子心）配合宁心安神（酸枣仁、远志、柏子仁），"
            "夏季避免冰镇食物过量以免伤及心阳，保持规律睡眠（深睡时段22-02时）护心最佳方案。"
        ),
        "earth": (
            "体质类型：气虚质 × 痰湿质混合型。"
            "脾胃功能相对薄弱，体内湿气偏重，常见食欲不振、大便溏薄、肢体沉重、腹部易胀等症状。"
            "调理重点：健脾益气（党参、黄芪、白术、山药）配合祛湿化痰（薏仁、茯苓、陈皮、半夏），"
            "饮食清淡规律，减少冰凉甜腻，餐后散步10-15分钟助消化运化，勿久坐伤脾。"
        ),
        "metal": (
            "体质类型：气虚质 × 燥热质混合型。"
            "肺气偏弱者容易出现反复感冒、皮肤干燥、便秘、声音低弱等症状，秋季最为明显。"
            "调理重点：补肺益气（玉屏风散、西洋参、黄精）配合润燥生津（雪梨、百合、银耳、天冬），"
            "坚持每日腹式呼吸锻炼10分钟改善肺活量，春秋换季时主动接种流感疫苗预防。"
        ),
        "water": (
            "体质类型：阳虚质 × 肾虚质混合型。"
            "肾阳不足者常见畏寒肢冷、夜尿频繁、腰膝酸软、精力下降等典型症状，冬季最为明显。"
            "调理重点：温补肾阳（菟丝子、巴戟天、杜仲、益智仁、核桃仁）配合固肾藏精（熟地、山茱萸、枸杞），"
            "每日坚持「搓腰眼」运动（双手搓热后按摩腰骶区3分钟），并练习踮脚尖激活肾经，冬季尤重保暖腰腹。"
        ),
    }
    constitution_type = _CONSTITUTION.get(
        prim_el,
        "体质均衡，整体健康基础较好，宜维持规律作息与均衡饮食，每年进行一次全面体检以早发现潜在健康风险。",
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
        interpretation_text=(
            f"健康评分为 {health_score} 分，整体风险等级【{risk_level}】。"
            f"{_risk_str}\n"
            f"运动建议：以「{_ex_top}」为主，配合每天快走与舒展。\n"
            f"饮食建议：{_diet_top}，配合充足水分摄入与规律三餐。\n"
            f"旺盛期参考：{peak_period}。\n"
            f"【季节养生】{seasonal_health}\n"
            f"【心理健康】{mental_health_advice}\n"
            f"【体质辨识】{constitution_type}"
            f"（仅供学术研究参考）"
        ),
        seasonal_health=seasonal_health,
        mental_health_advice=mental_health_advice,
        constitution_type=constitution_type,
    )
