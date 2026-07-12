"""
services/bazi_engine/analysis/marriage.py — 婚姻引擎 (M2 任务 2.03)

算法规格: §4.11-C
"""

from __future__ import annotations

from app.schemas.analysis import MarriageAnalysisModel

# 地支六冲
_BRANCH_CHONG: dict[str, str] = {
    "子": "午",
    "午": "子",
    "丑": "未",
    "未": "丑",
    "寅": "申",
    "申": "寅",
    "卯": "酉",
    "酉": "卯",
    "辰": "戌",
    "戌": "辰",
    "巳": "亥",
    "亥": "巳",
}

# 地支六合
_BRANCH_HE: dict[str, str] = {
    "子": "丑",
    "丑": "子",
    "寅": "亥",
    "亥": "寅",
    "卯": "戌",
    "戌": "卯",
    "辰": "酉",
    "酉": "辰",
    "巳": "申",
    "申": "巳",
    "午": "未",
    "未": "午",
}

# 地支三合（部分代表）
_BRANCH_SANHE: dict[str, str] = {
    "子": "水局",
    "辰": "水局",
    "申": "水局",
    "寅": "木局",
    "午": "木局",
    "戌": "木局",
    "卯": "木局",
    "巳": "火局",
    "酉": "火局",
    "丑": "火局",
    "亥": "水局",
    "未": "木局",
}

# 自刑支
_BRANCH_ZIXING: set[str] = {"子", "午", "酉", "亥"}

# 桃花支
_TAOHUA: set[str] = {"子", "午", "卯", "酉"}

# 天干五行
_STEM_ELEMENT: dict[str, str] = {
    "甲": "wood",
    "乙": "wood",
    "丙": "fire",
    "丁": "fire",
    "戊": "earth",
    "己": "earth",
    "庚": "metal",
    "辛": "metal",
    "壬": "water",
    "癸": "water",
}

# 地支五行
_BRANCH_ELEMENT: dict[str, str] = {
    "子": "water",
    "亥": "water",
    "寅": "wood",
    "卯": "wood",
    "巳": "fire",
    "午": "fire",
    "申": "metal",
    "酉": "metal",
    "丑": "earth",
    "辰": "earth",
    "未": "earth",
    "戌": "earth",
}

_ELEMENT_CN: dict[str, str] = {
    "metal": "金",
    "wood": "木",
    "water": "水",
    "fire": "火",
    "earth": "土",
}

# 配偶五行（中文）→ 英文，用于婚恋窗口匹配
_PARTNER_WUXING_EN: dict[str, str] = {
    "金": "metal",
    "木": "wood",
    "水": "water",
    "火": "fire",
    "土": "earth",
}


def compute_marriage(
    all_branches: list[str],  # 四柱地支列表（年支/月支/日支/时支）
    day_branch: str,  # 日支（配偶宫）
    shishen_scores: dict[str, float],
    shensha_items: list[dict],  # 神煞列表（含 name/is_beneficial/dizhi）
    gender: str,  # "male" / "female"
    yongshen_favor: list[str],
    yongshen_avoid: list[str],
    dayun_list: list[dict],
    strength_score: float = 50.0,
) -> MarriageAnalysisModel:
    """
    §4.11-C 婚姻引擎
    """
    total = sum(shishen_scores.values()) or 1.0

    guan = shishen_scores.get("正官", 0.0)
    sha = shishen_scores.get("七杀", 0.0)
    cai = shishen_scores.get("正财", 0.0) + shishen_scores.get("偏财", 0.0)

    guan_sha_pct = (guan + sha) / total
    cai_pct = cai / total

    # ─── 1. 日支稳定性评分 ──────────────────────────────────────────────
    stability_delta = 0
    if day_branch in _BRANCH_ZIXING:
        stability_delta -= 15
    if any(_BRANCH_CHONG.get(b) == day_branch for b in all_branches if b != day_branch):
        stability_delta -= 15
    if day_branch in _BRANCH_HE and _BRANCH_HE[day_branch] in all_branches:
        stability_delta += 10
    if day_branch in _BRANCH_SANHE:
        stability_delta += 10

    # ─── 2. 性别加成 ─────────────────────────────────────────────────
    gender_delta = 0
    guan_sha_mixed = guan > 0 and sha > 0  # 官杀混杂
    warnings = []

    if gender == "female":
        if guan_sha_pct >= 0.3 and not guan_sha_mixed:
            gender_delta += 10
        if guan_sha_mixed:
            warnings.append("官杀混杂，感情易波折，注意感情专一")
    else:  # male
        if 0.3 <= cai_pct <= 0.7:
            gender_delta += 10
        if cai_pct > 0.7:
            warnings.append("财星过旺，易沉迷感情，需警惕烂桃花")

    # ─── marriage_score ──────────────────────────────────────────────
    base_score = 50 + stability_delta + gender_delta
    marriage_score = int(min(100, max(0, base_score)))

    # ─── 3. 桃花 ─────────────────────────────────────────────────────
    taohua_count = sum(1 for b in all_branches if b in _TAOHUA)
    if taohua_count >= 2:
        peach_blossom = "旺"
    elif taohua_count == 1:
        peach_blossom = "中"
    else:
        peach_blossom = "弱"

    # ─── 4. 配偶五行 ─────────────────────────────────────────────────
    if gender == "male":
        # 夫星=财星五行（正财/偏财）→通过日主推
        partner_shishen_cn = "财星（正财/偏财）"
        partner_wuxing = _ELEMENT_CN.get(yongshen_favor[0] if yongshen_favor else "earth", "土")
    else:
        partner_shishen_cn = "夫星（正官/七杀）"
        partner_wuxing = _ELEMENT_CN.get(yongshen_favor[0] if yongshen_favor else "metal", "金")

    # ─── 5. 配偶画像 ─────────────────────────────────────────────────
    _partner_personality = {
        "金": "性格坚毅果断、处事有条理，重承诺、有责任心",
        "木": "性格温和仁慈、富有朝气，具创造力、乐于助人",
        "水": "性格灵活聪慧、适应力强，善沟通、有艺术细胞",
        "火": "性格热情开朗、表现力强，积极乐观、有感召力",
        "土": "性格稳重踏实、诚信忠厚，顾家、注重实际",
    }
    _partner_career = {
        "金": "职业倾向于金融、法律、机械或管理类领域",
        "木": "职业倾向于教育、医疗、设计或文化创意类领域",
        "水": "职业倾向于IT、传媒、运输或贸易类领域",
        "火": "职业倾向于传媒、餐饮、能源或艺术演艺类领域",
        "土": "职业倾向于房地产、农业、建筑或保险类领域",
    }
    _partner_interact = {
        "金": "相处之道：给予足够空间与尊重，避免过于强硬对立，共同规划财务目标",
        "木": "相处之道：保持沟通与理解，共同成长，注重精神层面的交流",
        "水": "相处之道：保持情感中的安全感，避免过度掌控，尊重对方的自由天性",
        "火": "相处之道：欣赏对方的热情与活力，互相鼓励，共同维系生活仪式感",
        "土": "相处之道：以平等尊重为基础，重视家庭生活，共同营造稳定温馨的家庭氛围",
    }
    partner_profile = (
        f"配偶{partner_shishen_cn}，五行偏{partner_wuxing}。"
        f"{_partner_personality.get(partner_wuxing, '性格均衡，处事得体')}。"
        f"{_partner_career.get(partner_wuxing, '职业多元，适应力强')}。"
        f"{_partner_interact.get(partner_wuxing, '相处之道：互相理解与包容，维系长久感情')}。"
    )

    # ─── 6. 配偶方位 ─────────────────────────────────────────────────
    direction_map = {
        "金": "西方",
        "木": "东方",
        "水": "北方",
        "火": "南方",
        "土": "中部，西南",
    }
    partner_direction = direction_map.get(partner_wuxing, "东方")

    # ─── 7. 最佳婚龄 ─────────────────────────────────────────────────
    if gender == "female":
        if guan_sha_pct >= 0.4:
            optimal_marriage_age = "26-30岁"
        else:
            optimal_marriage_age = "28-35岁"
    else:
        if cai_pct >= 0.4:
            optimal_marriage_age = "25-30岁"
        else:
            optimal_marriage_age = "28-33岁"

    # ─── 8. 婚恋窗口（大运） ──────────────────────────────────────────
    marriage_windows: list[str] = []
    for dyun in dayun_list[:5]:  # 前5步大运
        gz = dyun.get("ganzhi") or ((dyun.get("stem") or "") + (dyun.get("branch") or ""))
        branch = dyun.get("branch", "")
        dyun.get("stem", "")
        # 大支五行与配偶星五行同气或相生 → 婚期窗口
        br_el = _BRANCH_ELEMENT.get(branch, "")
        partner_el_en = _PARTNER_WUXING_EN.get(partner_wuxing, "")
        _SHENG_EN: dict[str, str] = {
            "wood": "fire",
            "fire": "earth",
            "earth": "metal",
            "metal": "water",
            "water": "wood",
        }
        is_window = bool(br_el and partner_el_en and (br_el == partner_el_en or _SHENG_EN.get(br_el) == partner_el_en))
        if is_window:
            start_age = dyun.get("start_age", 0)
            end_age = dyun.get("end_age", start_age + 10)
            marriage_windows.append(f"{gz}（{start_age}-{end_age}岁）大运助婚期")

    # ─── 9. 子女 ─────────────────────────────────────────────────────
    shi = shishen_scores.get("食神", 0.0)
    shang = shishen_scores.get("伤官", 0.0)
    shi_shang_pct = (shi + shang) / total

    if gender == "female":
        if shi_shang_pct >= 0.3:
            children_outlook = "食伤有力，子嗣缘较好"
            children_timing = "最佳生育期在大运食神/印绶旺运"
        else:
            children_outlook = "子嗣缘一般，需注意身体调养"
            children_timing = "宜在命局有利之年备孕"
    else:
        bi_jie = shishen_scores.get("比肩", 0.0) + shishen_scores.get("劫财", 0.0)
        if bi_jie / total >= 0.3:
            children_outlook = "官/子星受制，子女缘稍弱"
        else:
            children_outlook = "子女缘中等，宜用神旺运添丁"
        children_timing = "大运遇印运或食神运为有利时机"

    # ─── inference_tags ─────────────────────────────────────────────
    tags = []
    if peach_blossom == "旺":
        tags.append("桃花旺")
    if stability_delta < 0:
        tags.append("日支不稳")
    if guan_sha_mixed:
        tags.append("官杀混杂")
    tags.extend(warnings)

    _win_str = (
        ("、".join(marriage_windows[:2]) + "为最佳婚恋时机，") if marriage_windows else "大运顺运期为婚恋高峰期，"
    )
    (
        f"婚姻综合评分 {marriage_score} 分，桃花指数【{peach_blossom}】，配偶五行属【{partner_wuxing}】。"
        f"{partner_profile}"
        f"建议在 {optimal_marriage_age} 之间考虑确定关系，{_win_str}"
        f"子女缘分评估：{children_outlook}，{children_timing}。"
        f"{'感情注意事项：' + '；'.join(warnings) + '。' if warnings else '整体感情运势平稳，宜用心经营、顺其自然。'}"
        f"（仅供学术研究参考）"
    )
    # interp 后续会在新字段计算完后用新内容覆盖，此处保留临时值

    # ─── 新增：情感禁区 ──────────────────────────────────────────────────
    pitfall_items: list[str] = []
    if guan_sha_mixed:
        pitfall_items.append(
            "官杀混杂：感情中容易同时接受多段关系的情感投入，需克制「脚踏多船」的诱惑，"
            "主动培养感情专注度，一旦确定伴侣关系须保持高度专一，否则极易引发婚姻不稳或情感纠纷。"
        )
    if stability_delta < -10:
        pitfall_items.append(
            "日支冲害：配偶宫不稳，感情关系中容易因性格差异或外部压力出现裂缝，"
            "建议婚前充分了解双方价值观与生活习惯（至少3年），避免冲动型婚姻决策；"
            "婚后遭遇冲年（日支六冲流年）时，需主动投入感情修复，切勿在此期间做出离婚决定。"
        )
    if peach_blossom == "旺" and taohua_count >= 2:
        pitfall_items.append(
            "桃花过旺：异性缘极佳但感情线复杂，在竞争性感情关系中容易分心，"
            "需有意识降低外部情感干扰，专注深耕核心感情；同时提防「烂桃花」在流年桃花旺时入侵。"
        )
    if gender == "female" and guan_sha_pct >= 0.4:
        pitfall_items.append(
            "官星过旺（女命）：感情中容易对伴侣要求过高或情感投入过度，"
            "建议保持独立的事业追求与个人空间，避免将全部情感价值投注于单一关系；"
            "在感情受挫时需警惕「自我惩罚」心理，及时寻求情感支持。"
        )
    if gender == "male" and cai_pct >= 0.5:
        pitfall_items.append(
            "财星过旺（男命）：对感情的投入容易伴随物质利益考量，"
            "在伴侣选择上需避免纯以条件衡量，注重精神契合度与长期价值观一致性，"
            "否则即便物质条件匹配，婚姻内核缺乏情感共鸣也难以长久稳定。"
        )
    if not pitfall_items:
        pitfall_items.append(
            "命局感情结构较为平衡，整体情感风险度较低，宜顺其自然培养稳定感情关系；"
            "即便如此，仍需保持良好的沟通习惯与情感界限意识，是维系长久婚姻的基础保障。"
        )
    emotional_pitfalls = "；".join(pitfall_items)

    # ─── 新增：二婚指征 ──────────────────────────────────────────────────
    sha_pct = sha / total
    if sha_pct >= 0.3:
        second_marriage_indicator = (
            f"七杀力量偏强（占比{sha_pct:.0%}），命局中隐含婚姻波折信号，"
            "第一段感情中容易遭遇磕碰或分离，有一定概率经历婚变或二婚。"
            "化解方向：建议婚前充分了解伴侣三年以上再定终身；在感情遭遇重大危机时，"
            "优先尝试专业婚姻咨询而非冲动离婚；流年七杀旺时（申、酉年遇庚辛天干透出）尤需警惕感情动荡。"
        )
    elif guan_sha_mixed:
        second_marriage_indicator = (
            "官杀混杂，感情经历中容易出现多段重要关系，再婚指征为中等。"
            "婚变往往源于感情专注度不足或双方价值观随时间产生偏差；"
            "化解方向：珍视第一段婚姻，在关系出现危机信号时主动投资感情修复（共同旅行/专业咨询/仪式感建立），"
            "在流年官杀双透年份保持高度情感专注，避免外部诱惑乘虚而入。"
        )
    else:
        second_marriage_indicator = (
            "命局官杀结构较为清晰，婚姻稳定性及感情专注度整体良好，再婚风险属于较低水平。"
            "双方只要保持有效沟通与相互理解，长期和谐婚姻的概率较高；"
            "即便遭遇婚姻低谷期，也具备通过沟通协商平稳度过的内在心理基础与情感韧性。"
        )

    return MarriageAnalysisModel(
        marriage_score=marriage_score,
        peach_blossom=peach_blossom,
        partner_wuxing=partner_wuxing,
        partner_profile=partner_profile,
        partner_direction=partner_direction,
        optimal_marriage_age=optimal_marriage_age,
        marriage_windows=marriage_windows,
        children_outlook=children_outlook,
        children_timing=children_timing,
        inference_tags=tags,
        interpretation_text=(
            f"婚姻综合评分 {marriage_score} 分，桃花指数【{peach_blossom}】，配偶五行属【{partner_wuxing}】。\n"
            f"{partner_profile}\n"
            f"建议在 {optimal_marriage_age} 之间考虑确定关系，{_win_str}\n"
            f"子女缘分评估：{children_outlook}，{children_timing}。\n"
            f"【情感禁区】{emotional_pitfalls}\n"
            f"【再婚指征】{second_marriage_indicator}"
            f"（仅供学术研究参考）"
        ),
        emotional_pitfalls=emotional_pitfalls,
        second_marriage_indicator=second_marriage_indicator,
    )
