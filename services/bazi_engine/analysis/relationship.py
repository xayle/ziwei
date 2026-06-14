"""
services/bazi_engine/analysis/relationship.py — 六亲引擎 (M2 任务 2.05)

算法规格: §4.11-E
"""

from __future__ import annotations

from app.schemas.analysis import RelationshipAnalysisModel

# 六亲十神映射（男命）
_LIUQIN_MALE: dict[str, str] = {
    "比肩": "兄弟",
    "劫财": "兄弟",
    "食神": "子女",
    "伤官": "子女",
    "正财": "妻",
    "偏财": "父",
    "正官": "子女（男）",
    "七杀": "子女",
    "正印": "母",
    "偏印": "母",
}

# 六亲十神映射（女命）
_LIUQIN_FEMALE: dict[str, str] = {
    "比肩": "姐妹",
    "劫财": "姐妹",
    "食神": "子女",
    "伤官": "子女",
    "正财": "父",
    "偏财": "父",
    "正官": "夫",
    "七杀": "情人/再婚",
    "正印": "母",
    "偏印": "母",
}

# 神煞方位→贵人中文
_SHENSHA_GUIREN: dict[str, str] = {
    "天乙贵人": "天乙贵人（贵人相助）",
    "太极贵人": "太极贵人（智慧显现）",
    "文昌贵人": "文昌贵人（学业进益）",
    "将星": "将星（领导威权）",
}

_ELEMENT_CN: dict[str, str] = {
    "metal": "金",
    "wood": "木",
    "water": "水",
    "fire": "火",
    "earth": "土",
}

# 十神六亲缘分描述（按十神 × 强/中/弱三级，用 {kin} 占位符接收具体亲属名称）
_TEN_GOD_KIN_DESC: dict[str, dict[str, str]] = {
    "比肩": {
        "strong": "命中{kin}手足情深，比肩同气相扶，危急关头多有实质相助且出手毫不犹豫，共患难的经历成为彼此最牢固的情感底色，合作共事时默契自然、进退一致。",
        "mid": "命中{kin}关系平和，各自独立中偶有往来，遇事可寻求协助且对方多能尽力，宜主动保持定期联系以维系这份因距离而容易冷却的温情。",
        "weak": "命中{kin}缘分偏淡，各奔前程为主，彼此在对方生命中的存在感相对有限，珍视偶发的相聚时光并在日常中主动联系，方能令这份情意不随岁月悄然消散。",
    },
    "劫财": {
        "strong": "命中{kin}情分深厚，劫财竞争之性在此化作互相激励的精进动力，情义与竞争并存、相辅相成，但需明确权责边界方能在坦诚中实现共赢相处。",
        "mid": "命中{kin}关系中规中矩，偶有利益层面的小摩擦，相处之道在于各守本分与发自内心的相互尊重，不争高下则情义自然得以长存。",
        "weak": "命中{kin}缘分稀薄，情意相对淡漠，以共同利益为情感纽带、以小事作为日常联系契机，是逐步修复疏离距离最自然也最有效的路径。",
    },
    "食神": {
        "strong": "命中{kin}缘深，食神温润滋养之气贯穿这段情缘，关系融洽自然、有温有度，生活中常有细腻周到的关怀与不声张的体贴，令人心安处处有所依靠。",
        "mid": "命中{kin}关系平和，有缘相聚但需用心付出，给予充足陪伴与真诚关爱才能令情缘持续稳固，情感的维系往往比想象中更需要主动灌溉。",
        "weak": "命中{kin}缘分稍淡，情分偏薄且易忽视，宜尊重对方自主性、主动创造互动机会，以真心与耐心换取联结的逐步深化与延续。",
    },
    "伤官": {
        "strong": "命中{kin}才气相通，伤官赋予此段情缘独特的创造性张力，双方个性鲜明、碰撞出真实的火花与思想共鸣，以开放接纳替代强硬管束方能令才华共同绽放。",
        "mid": "命中{kin}关系中等，个性差异带来的摩擦时有发生，彼此包容与主动理解是维系这段情缘最重要的日常功课，差异本身若被善用便能成就独特的互补。",
        "weak": "命中{kin}缘分较淡，情感距离偏大且不易靠近，宜减少管控欲望、给予充分空间，让情缘在尊重中自然呼吸，温度往往因放松而悄然回升。",
    },
    "正财": {
        "strong": "命中{kin}缘分深厚，正财有根，情感联结稳固可靠、有实质可依，彼此互动中常有力所能及的支撑与来自内心的真诚庇护，是命局中重要且稳定的情感基石。",
        "mid": "命中{kin}关系平顺，相处融洽且少有大起大落，用心维系日常陪伴与情感仪式感，这段感情的温度便可持续保有且稳步升温。",
        "weak": "命中{kin}缘分稍淡，需主动投入沟通时间与陪伴质量，勿因一时疏于经营产生难以察觉的隔阂，珍视每一次真诚交流所积累的情感能量。",
    },
    "偏财": {
        "strong": "命中{kin}缘深，偏财有力，此段情缘中对方积极进取、资源广厚且乐于相助，往来中常有意外之助与令人欣喜的丰盛馈赠，是命局中毫不费力的天然贵人。",
        "mid": "命中{kin}关系正常稳定，对方对成长有积极正向的影响力，逢人生大事可主动征询意见往往获益颇深，规律联系并真诚表达感激是深化情缘的自然之道。",
        "weak": "命中{kin}缘分偏淡，彼此之间存在一定的情感距离，宜主动创造共处机会、以耐心化解疏离感，重建真实的情感连接需要双向的持续投入。",
    },
    "正官": {
        "strong": "命中{kin}缘深，正官护佑，此段关系稳重可托、责任感强且承诺意识清晰，在命局中构成诚信担当的情感基石，是可以倚赖的存在。",
        "mid": "命中{kin}关系平和稳定，互动有礼有节，双方尊重各自边界，感情在守序中保持持续而不失温度的稳进，是经得起时间考验的亲密联结。",
        "weak": "命中{kin}缘分偏淡，感情根基稍显薄弱，需在细节上多加用心、以真诚的行动填补缘薄所带来的情感缺口，唯有持续投入方能令情缘逐渐生根。",
    },
    "七杀": {
        "strong": "命中{kin}缘分强烈，七杀磁场赋予此段情缘鲜明的张力与激情，对方个性强悍出众、充满能量，需以慧心与包容而非权力之争建立关系中真实的平衡。",
        "mid": "命中{kin}关系有起伏，七杀带来的摩擦与活力并存，坦诚而有温度的沟通是化解矛盾、维系深层感情最可靠且最值得坚持的路径。",
        "weak": "命中{kin}缘分稀薄，情感联结需主动维系，减少对立式沟通、以柔性方式建立信任，方能令稀薄的缘分在时间中逐步积累出真实的感情厚度。",
    },
    "正印": {
        "strong": "命中{kin}缘极深，正印有根，此段情缘充满慈爱庇护与无条件的精神支撑，是命局中最坚实的内心后盾，这份深远的底气支撑人生诸多重要抉择时的从容。",
        "mid": "命中{kin}关系温和稳定，对方对成长有真实的正向影响，宜规律表达关爱并主动沟通，维系这份难得的亲缘温情需要对等的珍视与回应。",
        "weak": "命中{kin}缘分稍淡，此段情缘在某些关键时刻有轻微缺位感，成年后若能主动化解心结、以成熟心态重建联结，往往带来意想不到的深层内心疗愈。",
    },
    "偏印": {
        "strong": "命中{kin}缘深，偏印有力，此段情缘独立色彩鲜明，对方个性独特、视角超脱常规，互相启发与拓展认知远多于相互依赖，成就各自独立人格的同时构筑深刻羁绊。",
        "mid": "命中{kin}关系中等，偏印之性偏内敛含蓄，情感表达方式不够直接明白，宜以行动互诉温情，并用心欣赏彼此各自独到之处带来的互补价值。",
        "weak": "命中{kin}缘分偏淡，此段情缘较为疏离且不易靠近，宜主动联系、减少等待对方先迈步的心理预设，以真诚与耐心换取关系的逐步消融与温度回升。",
    },
}

# 日主天干社交策略加成（各约40-60字）
_STEM_SOCIAL_STRATEGY: dict[str, str] = {
    "甲": "甲木日主宜以开创性领导力驱动人际，主动连接不同圈层、启动协作项目，在人脉生态中扮演发起者角色，以正直担当赢得长期信任。",
    "乙": "乙木日主社交优势在于柔韧渗透与细水长流，宜深耕少数高质量关系，细腻的情感投入与审美化表达是吸引志同道合伙伴的隐性磁场。",
    "丙": "丙火日主天然具备感召力，社群组织与品牌输出是最高效的人脉拓展方式，持续的热情正能量让自己成为圈子中无可替代的精神坐标。",
    "丁": "丁火日主以深度一对一交流构建真实连接，细腻的倾听与精准洞察让对方感到被真正理解，是建立高黏性高信任度关系网络的核心竞争力。",
    "戊": "戊土日主以厚重诚信为社交根基，稳定可靠的形象天然吸引长期合作伙伴，适合担任多方信任节点，在复杂关系网络中充当协调整合的压舱石。",
    "己": "己土日主宜以专业深度建立口碑，低调务实的作风在圈子中形成独特辨识度，以品质换口碑、以信誉聚人心，渐积渐厚的人脉自然而至。",
    "庚": "庚金日主以果断执行力与高标准赢得尊重，直接清晰的表达在专业人脉中建立强势存在感，让实力本身成为最有力的社交名片。",
    "辛": "辛金日主社交品质优于数量，精心维护少数深度关系带来更高回报，审美与精致感是进入高端圈层的隐性入场券，以精益求精脱颖而出。",
    "壬": "壬水日主社交灵活多变，跨界整合是核心竞争优势，在不同领域间担当信息流通节点，让人脉网络在流动中持续增值放大。",
    "癸": "癸水日主以深度洞察与共情能力为社交利器，适合在小圈子内建立深厚信任，将内心世界的丰富转化为高价值情感支持资源，成为人际中的精神依靠。",
}


def compute_relationship(
    shishen_scores: dict[str, float],
    shensha_items: list[dict],  # 神煞列表: [{name, is_beneficial, dizhi, ...}]
    gender: str,  # "male" / "female"
    day_stem: str = "",
    dayun_list: list[dict] | None = None,
) -> RelationshipAnalysisModel:
    """
    §4.11-E 六亲引擎
    """
    total = sum(shishen_scores.values()) or 1.0

    liuqin_map = _LIUQIN_MALE if gender == "male" else _LIUQIN_FEMALE

    # ─── 1. 六亲关系 ─────────────────────────────────────────────────────
    liu_qin: dict[str, str] = {}
    for shen, kin in liuqin_map.items():
        score = shishen_scores.get(shen, 0.0)
        pct = score / total
        _kin_descs = _TEN_GOD_KIN_DESC.get(shen, {})
        if pct >= 0.3:
            desc = _kin_descs.get("strong", f"命中{kin}缘分深厚，情感联结稳固，互动中常有支撑与提携。").format(kin=kin)
        elif pct >= 0.1:
            desc = _kin_descs.get("mid", f"命中{kin}关系平和，相处自然，宜顺缘而行，不强求。").format(kin=kin)
        else:
            desc = _kin_descs.get("weak", f"命中{kin}缘分较淡，建议主动维系情感联系，珍惜相聚机会。").format(kin=kin)
        if kin not in liu_qin:
            liu_qin[kin] = desc

    # ─── 2. 贵人 ─────────────────────────────────────────────────────
    noble_people: list[str] = []
    for s in shensha_items:
        if s.get("is_beneficial"):
            name = s.get("name", "") or ""
            hint: str = _SHENSHA_GUIREN.get(name, name) or name
            noble_people.append(hint)
    noble_people = list(dict.fromkeys(noble_people))[:5]
    if not noble_people:
        noble_people = ["命中贵人缘较淡，需广结善缘"]

    # ─── 3. 小人 ─────────────────────────────────────────────────────
    bi = shishen_scores.get("比肩", 0.0)
    jie = shishen_scores.get("劫财", 0.0)
    sha = shishen_scores.get("七杀", 0.0)
    petty_people: list[str] = []
    if (bi + jie) / total >= 0.4:
        petty_people.append("劫财旺，需防身边竞争者/小人夺财")
    if sha / total >= 0.3:
        petty_people.append("七杀有力，防权力制约或小人横祸")
    if not petty_people:
        petty_people = ["小人星力量弱，整体人际较顺"]

    # ─── 4. 社交策略 ─────────────────────────────────────────────────
    yin = shishen_scores.get("正印", 0.0) + shishen_scores.get("偏印", 0.0)
    food = shishen_scores.get("食神", 0.0)

    if yin / total >= 0.3:
        strategy = (
            "印星旺盛，亲和力强，常受贵人推荐和信任网络的加持，适合口碑型社交展示。"
            "建议主动大方分享知识和经验，以和谐态度成为包容联结者，自然吸引高质量相助。"
        )
    elif food / total >= 0.3:
        strategy = (
            "食神旺盛，社交对象广泛，善于分享的人最终得福。"
            "高频参与社群活动、开设工作坊或展示成果，是拓展优质人脉的最短路径。"
        )
    elif (bi + jie) / total >= 0.4:
        strategy = (
            "比劫旺盛，竞争心强，人际层面需主动建立清晰的个人品牌和差异化价值。"
            "防范因激烈竞争而损伤的关系，在实力层面而非情绪层面建立合作。"
        )
    else:
        strategy = (
            "命局均衡，人际关系中幸而不尽，广泛社交比专注单一圈子更有利。"
            "覆盖不同行业和背景的人群网络，保持开放的学习态度，打造多元化价值。"
        )

    # day_stem 天干社交风格加成
    _stem_strat = _STEM_SOCIAL_STRATEGY.get(day_stem, "")
    if _stem_strat:
        strategy = strategy + _stem_strat

    # ─── relationship_score ─────────────────────────────────────────
    guiren_count = len([s for s in shensha_items if s.get("is_beneficial")])
    score = min(100, max(0, 50 + guiren_count * 10 - len(petty_people) * 5))
    relationship_score = int(score)

    # ─── inference_tags ─────────────────────────────────────────────
    tags = []
    if guiren_count >= 2:
        tags.append("贵人多助")
    if (bi + jie) / total >= 0.4:
        tags.append("比劫夺财小人防范")
    if sha / total >= 0.3:
        tags.append("七杀压制需化")

    _noble_str = "；".join(noble_people[:3])
    _kin_summary_parts = []
    for _k, _v in list(liu_qin.items())[:4]:
        if any(
            kw in _v
            for kw in (
                "缘极深",
                "缘分深厚",
                "情分深厚",
                "缘深，",
                "手足情深",
                "才气相通",
                "缘分强烈",
            )
        ):
            _kin_summary_parts.append(f"{_k}（缘深）")
        elif any(
            kw in _v
            for kw in (
                "关系平和",
                "关系平顺",
                "关系中等",
                "关系正常",
                "关系中规",
                "关系有起伏",
                "关系温和",
            )
        ):
            _kin_summary_parts.append(f"{_k}（平和）")
        else:
            _kin_summary_parts.append(f"{_k}（缘淡）")
    _kin_brief = "、".join(_kin_summary_parts) if _kin_summary_parts else "各有缘分"
    interp = (
        f"六亲人际评分为 {relationship_score} 分。"
        f"六亲速览：{_kin_brief}，详见各项说明。"
        f"贵人运势：{_noble_str}，宜主动维系信任型人际网络，以真诚换取长久支持。"
        f"小人警惕：{'；'.join(petty_people)}。"
        f"社交策略建议：{strategy}"
        f"（仅供学术研究参考）"
    )

    return RelationshipAnalysisModel(
        relationship_score=relationship_score,
        liu_qin=liu_qin,
        noble_people=noble_people,
        petty_people=petty_people,
        social_strategy=strategy,
        inference_tags=tags,
        interpretation_text=interp,
    )
