"""
services/bazi_engine/analysis/liunian_domain.py — 流年四维预测 (M3 §4.11-H)

四维: 财运 / 事业 / 婚恋 / 健康，每维 ≤60 字

规则：
  财运:
    正财/偏财透且用神含财 → "正财当令，宜拓收入"
    比劫多透              → "比劫争财，防竞争损财"
    无财气且弱            → "守成减负，谨防支出超支"
  事业:
    官杀得令              → "官杀当旺，有升迁机遇，宜主动表现"
    食伤生财              → "食伤生财，宜创新展能，展露才华"
    流年驿马              → "驿马流年，宜出差调动，远行有益"
  婚恋:
    官星透（女命）         → "单身者宜扩大社交圈，有良缘机遇"
    年支桃花              → "桃花流年，感情缘分旺盛"
    七杀透（女命）         → "感情有波折，宜冷静面对，不轻率决策"
    通用                  → "感情平稳，重在自我成长"
  健康:
    克日主五行占优         → "提防身体透支，关注精力管理"
    某五行>50%             → "关注对应脏腑保养"
    与用神合              → "身体状态佳，保持规律作息"
"""
from __future__ import annotations

from typing import Literal

# 五行与脏腑对应
_ORGAN_MAP = {
    "wood":  "肝胆",
    "fire":  "心血管",
    "earth": "脾胃",
    "metal": "肺肠",
    "water": "肾脏",
}

# 五行克关系：A克B
_OVERCOME: dict[str, str] = {
    "wood": "earth",
    "fire": "metal",
    "earth": "water",
    "metal": "wood",
    "water": "fire",
}

# 干支对应五行（天干）
_STEM_WUXING = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth", "己": "earth",
    "庚": "metal", "辛": "metal",
    "壬": "water", "癸": "water",
}

# 地支桃花规则：年/日支三合局首支 → 桃花地支
_TAOHUAL_MAP = {
    "寅": "卯", "午": "卯", "戌": "卯",   # 寅午戌 → 桃花在卯
    "亥": "子", "卯": "子", "未": "子",   # 亥卯未 → 桃花在子
    "申": "酉", "子": "酉", "辰": "酉",   # 申子辰 → 桃花在酉
    "巳": "午", "酉": "午", "丑": "午",   # 巳酉丑 → 桃花在午
}

# 地支驿马规则：年支三合局→驿马地支
_YIMA_MAP = {
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "亥": "巳", "卯": "巳", "未": "巳",
    "巳": "亥", "酉": "亥", "丑": "亥",
}

# 天干十神分类
_ZHENGCAI_STEMS = set()  # 正财天干集合（运行时根据日主计算，此处占位）
_PIANCAI_STEMS  = set()
_SHISHEN_LUCKY  = {"食神", "正印", "天乙贵人", "正官", "正财"}


def _is_taohua(day_branch: str, year_branch: str) -> bool:
    taohua = _TAOHUAL_MAP.get(day_branch)
    return taohua == year_branch


def _is_yima(day_branch: str, year_branch: str) -> bool:
    yima = _YIMA_MAP.get(day_branch)
    return yima == year_branch


def compute_liunian_domain_forecasts(
    year:            int,
    year_stem:       str,
    year_branch:     str,
    day_stem:        str,
    day_branch:      str,
    shishen_scores:  dict[str, float],
    yongshen_favor:  list[str],
    wuxing_scores:   dict[str, float],
    gender:          str = "male",
) -> dict[str, str]:
    """
    M3 §4.11-H — 流年四维预测

    参数:
        year:           流年年份（如 2025）
        year_stem:      流年天干（甲/乙/...）
        year_branch:    流年地支（子/丑/...）
        day_stem:       日主天干
        day_branch:     日柱地支（用于桃花/驿马计算）
        shishen_scores: 十神占比 {十神名: float}
        yongshen_favor: 用神五行列表（英文）
        wuxing_scores:  五行分布 {english: float}
        gender:         "male" / "female"

    返回:
        {"财运": str, "事业": str, "婚恋": str, "健康": str}
    """
    year_wuxing = _STEM_WUXING.get(year_stem, "")
    day_wuxing  = _STEM_WUXING.get(day_stem, "")
    total_wx    = sum(wuxing_scores.values()) or 1.0

    # ── 财运 ──────────────────────────────────────────────────────────────────
    zhengcai_score = shishen_scores.get("正财", 0.0)
    piancai_score  = shishen_scores.get("偏财", 0.0)
    bijie_score    = (shishen_scores.get("比肩", 0.0) +
                      shishen_scores.get("劫财", 0.0))
    has_cai_yongshen = bool(yongshen_favor)  # 用神存在即有财运支撑
    yin_score = (shishen_scores.get("正印", 0.0) + shishen_scores.get("偏印", 0.0))

    if (zhengcai_score > 0.1 or piancai_score > 0.1) and has_cai_yongshen:
        caiyun = (
            f"{year}年正财当令，用神顺势得力，财运进入活跃期。"
            f"宜积极拓展新收入渠道，副业兼职或投资理财均有斩获，把握上半年财运高峰。"
            f"注意合同与票据管理，签约前仔细核查条款，防止漏洞失财。"
        )
    elif bijie_score > 0.35:
        caiyun = (
            f"{year}年比劫争财局面显现，竞争者环绕，财务竞争风险偏高。"
            f"合伙生意需谨慎，建议书面确认权责，防止口头承诺引发纠纷。"
            f"守成为上，减少不必要投资，稳住本职收入为先。"
        )
    elif yin_score > 0.3 and year_wuxing not in yongshen_favor:
        caiyun = (
            f"{year}年印星压财，财星受制，正财进账偏缓。"
            f"适合复盘已有资产配置，学习财务知识规划未来，精简开支填补缺口。"
            f"勿轻易投机，以稳健理财方式积累资本。"
        )
    elif (zhengcai_score + piancai_score) < 0.05:
        caiyun = (
            f"{year}年财气偏弱，主动创收阻力较大，守成减负为宜。"
            f"谨防支出超支，勿轻易借贷或为他人担保，控制消费冲动。"
            f"可将精力转向技能提升，为下一个财运高峰期蓄力。"
        )
    elif year_wuxing in yongshen_favor:
        caiyun = (
            f"{year}年流年五行顺用神，财运有明显小幅提升。"
            f"适合把握短期机遇小试牛刀，谨慎中不失进取，财务决策宜快不宜拖。"
            f"建议在上半年确定主要收入方向，下半年稳固成果。"
        )
    else:
        caiyun = (
            f"{year}年财运整体平稳，无大起大落，宜按既定计划执行理财规划。"
            f"定期收支记账，优化消费结构，尽早清理高息负债。"
            f"不宜贸然冒进，守住当前收入基础即为上策。"
        )

    # ── 事业 ──────────────────────────────────────────────────────────────────
    guansha_score = (shishen_scores.get("正官", 0.0) +
                     shishen_scores.get("七杀", 0.0))
    shishang_score = (shishen_scores.get("食神", 0.0) +
                      shishen_scores.get("伤官", 0.0))
    is_yima = _is_yima(day_branch, year_branch)

    if guansha_score > 0.2:
        shiye = (
            f"{year}年官杀当旺，职场升迁信号明显，上司或贵人对你表现格外关注。"
            f"宜主动请缨承担重要项目，展现领导力与执行力，争取晋升或调薪机会。"
            f"注意规章制度，官杀之年行事须合规，切勿逾越职场边界。"
        )
    elif shishang_score > 0.2 and year_wuxing in yongshen_favor:
        shiye = (
            f"{year}年食伤生财，创造力与表达力进入高峰，适合开拓新业务或副业。"
            f"以专业才华换取成果，技术型独立工作者本年尤其有突破空间。"
            f"可考虑展示个人作品集或申请专利，将创意变现。"
        )
    elif is_yima:
        shiye = (
            f"{year}年驿马临命，宜出差调动、探索新市场，外出奔波反而有利于开运。"
            f"异地合作、跨城市项目或海外业务均有发展机遇，不必拘泥于本地圈子。"
            f"保持灵活机动，随机应变是本年职场制胜关键。"
        )
    elif year_wuxing in yongshen_favor:
        shiye = (
            f"{year}年流年顺应用神，事业稳中有进，专注本职岗位可有所突破。"
            f"适合深耕专业技能，完善个人知识体系，积累行业资源与口碑。"
            f"稳扎稳打，以量变推动质变，本年奠基为主，成果将在下一个大运期显现。"
        )
    else:
        shiye = (
            f"{year}年职场气场偏平，宜避免轻易跳槽或创业，维持现有格局为先。"
            f"利用空档期主动学习、考证、建立行业人脉，为下一个顺运年份蓄势。"
            f"减少无谓内耗，聚焦最核心的工作交付，保持职业信誉。"
        )

    # ── 婚恋 ──────────────────────────────────────────────────────────────────
    guanxing_score = shishen_scores.get("正官", 0.0)
    qisha_score    = shishen_scores.get("七杀", 0.0)
    is_taohua      = _is_taohua(day_branch, year_branch)

    if is_taohua:
        hunlian = (
            f"{year}年桃花临年支，感情缘分进入旺盛周期。"
            f"单身者宜主动扩大社交圈，参加聚会、兴趣社群，正缘可能出现于日常偶遇。"
            f"已婚者注重感情保鲜，策划小惊喜与旅行，防止第三者介入。"
        )
    elif gender == "female" and guanxing_score > 0.15:
        hunlian = (
            f"{year}年官星透出，女命有正式感情机遇，有缘遇见气场稳重的异性。"
            f"单身者宜减少自我封闭，借助朋友介绍或正式社交场合拓展圈子。"
            f"已婚者感情基础稳固，宜共同规划未来，感情升温有利家庭和谐。"
        )
    elif gender == "female" and qisha_score > 0.2:
        hunlian = (
            f"{year}年七杀透出，感情关系有摩擦与变数，情绪波动较大。"
            f"宜冷静面对感情挫折，不轻率做分手或结婚等重大决策，理性沟通优先。"
            f"给自己和伴侣足够的独立空间，避免控制欲或争执升级。"
        )
    elif year_wuxing in yongshen_favor:
        hunlian = (
            f"{year}年流年气场和谐，感情整体顺畅，互动增多、关系升温。"
            f"单身者有望遇到真诚相配之人；伴侣感情可考虑进一步确立关系。"
            f"已婚者夫妻默契提升，共同出行或参与活动有助于拉近距离。"
        )
    else:
        hunlian = (
            f"{year}年感情运势平稳，无明显大起大落，重在经营现有亲密关系。"
            f"主动倾听伴侣需求，减少因小事引发的争执，以耐心换取信任。"
            f"单身者不必急于求成，内修自我才是吸引良缘的根本。"
        )

    # ── 健康 ──────────────────────────────────────────────────────────────────
    克day = _OVERCOME.get(year_wuxing, "")
    is_克day = (克day == day_wuxing) if 克day else False

    dominant_el = max(wuxing_scores, key=lambda k: wuxing_scores.get(k, 0.0)) if wuxing_scores else ""
    dominant_ratio = wuxing_scores.get(dominant_el, 0) / total_wx if dominant_el else 0

    is_yongshen_favorable_year = year_wuxing in yongshen_favor

    if is_克day:
        organ = _ORGAN_MAP.get(day_wuxing, "脏腑")
        jiankang = (
            f"{year}年流年五行克制日主，{organ}系统承压，注意定期检查。"
            f"防止精力透支，保证充足睡眠（7-8小时），减少不必要的熬夜与应酬。"
            f"情志保持平和，避免忧思过重，调节压力是本年养生重点。"
        )
    elif dominant_ratio > 0.5:
        organ = _ORGAN_MAP.get(dominant_el, "相关脏腑")
        jiankang = (
            f"{year}年命局五行偏旺，{organ}可能因过度运作而出现问题，需关注相关保养。"
            f"饮食均衡，避免过度偏食某类食物，保持五行饮食调和。"
            f"建议每半年进行一次全面体检，将潜在问题消灭于萌芽状态。"
        )
    elif is_yongshen_favorable_year:
        jiankang = (
            f"{year}年流年与用神相合，整体气血较为充盈，精力状态良好。"
            f"适合在本年强化运动习惯，建立锻炼规律，为健康打好基础。"
            f"保持情绪稳定与规律作息，疫病防护不可松懈，偶发小疾及时就诊即可。"
        )
    else:
        jiankang = (
            f"{year}年健康运势整体平稳，无明显大病征兆，以预防为主。"
            f"定期进行常规体检，关注睡眠质量与消化系统。"
            f"注意情绪起伏对身体的影响，保持良好心态是本年养生管理的核心要素。"
        )

    return {
        "财运": caiyun,
        "事业": shiye,
        "婚恋": hunlian,
        "健康": jiankang,
    }
