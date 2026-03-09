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
    "metal": "金", "wood": "木", "water": "水", "fire": "火", "earth": "土",
}

# 十神六亲缘分描述（按十神 × 强/中/弱三级，用 {kin} 占位符接收具体亲属名称）
_TEN_GOD_KIN_DESC: dict[str, dict[str, str]] = {
    "比肩": {
        "strong": "命中{kin}手足情深，比肩同气相扶，危急关头多有实质相助，合作共事时默契自然，共同进退而非单打独斗。",
        "mid":    "命中{kin}关系平和，各自独立中偶有往来，遇事可寻求协助，宜主动保持联系以维系温情。",
        "weak":   "命中{kin}缘分偏淡，各奔前程为主，珍视偶发相聚并主动联系，方能令这份情意不随岁月消散。",
    },
    "劫财": {
        "strong": "命中{kin}情分深厚，劫财竞争之性化作互相激励的动力，情义与竞争并存，需明确权责方能共赢相处。",
        "mid":    "命中{kin}关系中规中矩，偶有利益摩擦，相处之道在于各守本分与相互尊重，不争高下则情义自存。",
        "weak":   "命中{kin}缘分稀薄，情意淡漠，建议以共同利益为纽带、以小事作为情感连接契机，逐步修复疏离距离。",
    },
    "食神": {
        "strong": "命中{kin}缘深，食神温润滋养之气流注此段情缘，关系融洽自然，生活中常有温暖互动与细腻关怀，令人心安。",
        "mid":    "命中{kin}关系平和，有缘相聚但需用心付出，给予充足陪伴与关爱，方能令情缘持续稳固延绵。",
        "weak":   "命中{kin}缘分稍淡，情分偏薄，宜尊重对方自主性、主动增进沟通，以真心换取长久联结。",
    },
    "伤官": {
        "strong": "命中{kin}才气相通，伤官赋予此段情缘独特创造性，双方个性鲜明碰撞火花，以智慧引导替代强硬管束方见成效。",
        "mid":    "命中{kin}关系中等，个性差异带来的摩擦不少，彼此包容与理解是维系这段情缘的核心功课。",
        "weak":   "命中{kin}缘分较淡，情感距离偏大，宜减少管控、多给空间，让情缘在自由中自然恢复温度。",
    },
    "正财": {
        "strong": "命中{kin}缘分深厚，正财有根，关系基础稳固可依，彼此互动中常有实质支撑与温暖庇护，是命局中重要的情感依靠。",
        "mid":    "命中{kin}关系平顺，相处融洽，情感波澜不多，用心维系日常陪伴与仪式感，感情温度可持续稳升。",
        "weak":   "命中{kin}缘分稍淡，需主动投入沟通与陪伴，勿因疏于经营产生隔阂，珍视每一次真诚交流。",
    },
    "偏财": {
        "strong": "命中{kin}缘深，偏财有力，此段情缘中对方积极进取、资源广厚，往来中常有意外之助与丰盛馈赠，天然贵人。",
        "mid":    "命中{kin}关系正常，对方对成长有积极影响，逢大事可主动征询意见往往获益颇丰，宜规律联系深化纽带。",
        "weak":   "命中{kin}缘分偏淡，存在一定情感距离，宜主动创造相处机会，以耐心化解疏离，重建情感连接。",
    },
    "正官": {
        "strong": "命中{kin}缘深，正官护佑，此段关系稳重可托、责任感强，彼此间有清晰的承诺意识，是命局中诚信担当的情感基石。",
        "mid":    "命中{kin}关系平和稳定，互动有礼有节，双方尊重各自边界，感情在守序中保持持续温度。",
        "weak":   "命中{kin}缘分偏淡，感情根基稍显薄弱，需在细节上多加用心，以真诚行动填补缘薄所带来的情感缺口。",
    },
    "七杀": {
        "strong": "命中{kin}缘分强烈，七杀磁场赋予此段情缘张力与激情，对方个性强悍出众，需以慧心而非强权建立关系中的平衡。",
        "mid":    "命中{kin}关系有起伏，七杀带来的摩擦与张力并存，坦诚沟通是化解矛盾、维系深层感情的最可靠路径。",
        "weak":   "命中{kin}缘分稀薄，感情需多加主动维系，减少冲突并以柔克刚，方能逐步改善关系质量。",
    },
    "正印": {
        "strong": "命中{kin}缘极深，正印有根，此段情缘充满慈爱庇护，是命局中最坚实的精神后盾，这份底气支撑人生诸多重要抉择。",
        "mid":    "命中{kin}关系温和稳定，对方对成长有正向影响，宜规律表达关爱、主动沟通，维系这份难得的亲缘温情。",
        "weak":   "命中{kin}缘分稍淡，早年此段情缘有轻微缺位感，成年后若能主动化解积累的心结，往往带来深层内心疗愈。",
    },
    "偏印": {
        "strong": "命中{kin}缘深，偏印有力，此段情缘独立色彩鲜明，对方个性独特、视角超脱，互相启发多于依赖，成就独立人格。",
        "mid":    "命中{kin}关系中等，偏印之性偏内敛，情感表达不够直白，宜以行动互诉温情，欣赏彼此各自的独到之处。",
        "weak":   "命中{kin}缘分偏淡，此段情缘较为疏离，宜主动联系、减少等待，以耐心与真诚换取关系的逐步修复。",
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
    shensha_items: list[dict],          # 神煞列表: [{name, is_beneficial, dizhi, ...}]
    gender: str,                         # "male" / "female"
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
        pct   = score / total
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
    bi  = shishen_scores.get("比肩", 0.0)
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
        if any(kw in _v for kw in ("缘极深", "缘分深厚", "情分深厚", "缘深，", "手足情深")):
            _kin_summary_parts.append(f"{_k}（缘深）")
        elif any(kw in _v for kw in ("关系平和", "关系平顺", "关系中等", "关系正常", "关系中规")):
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
