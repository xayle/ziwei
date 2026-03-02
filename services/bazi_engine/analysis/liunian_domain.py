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
    has_cai_yongshen = any(
        el in ("wood", "fire", "earth", "metal", "water")
        and el in yongshen_favor
        for el in yongshen_favor
    )
    # 正财/偏财透出且用神含财
    if (zhengcai_score > 0.1 or piancai_score > 0.1) and has_cai_yongshen:
        caiyun = "正财当令，用神得力，宜积极拓展收入渠道，时机有利。"
    elif bijie_score > 0.35:
        caiyun = "比劫争财，竞争激烈，防合伙纠纷及财务损失，守成为上。"
    elif (zhengcai_score + piancai_score) < 0.05:
        caiyun = "财气偏弱，守成减负为宜，谨防支出超支，勿轻易借贷。"
    elif year_wuxing in yongshen_favor:
        caiyun = "流年五行顺用神，财运有小幅提升，把握短期机遇。"
    else:
        caiyun = "财运平稳，按计划执行理财规划，不宜冒进。"

    # ── 事业 ──────────────────────────────────────────────────────────────────
    guansha_score = (shishen_scores.get("正官", 0.0) +
                     shishen_scores.get("七杀", 0.0))
    shishang_score = (shishen_scores.get("食神", 0.0) +
                      shishen_scores.get("伤官", 0.0))
    is_yima = _is_yima(day_branch, year_branch)

    if guansha_score > 0.2:
        shiye = "官杀当旺，升迁机遇明显，宜主动表现争取晋升或重要项目。"
    elif shishang_score > 0.2 and any(
        _STEM_WUXING.get(year_stem) in yongshen_favor for _ in [1]
    ):
        shiye = "食伤生财，宜创新展能，以才华换取成果，适合开拓新业务。"
    elif is_yima:
        shiye = "驿马流年，宜出差调动、拓展新市场，外出有助于开运。"
    elif year_wuxing in yongshen_favor:
        shiye = "流年顺用神，事业稳中有进，专注本职可有所突破。"
    else:
        shiye = "事业宜稳扎稳打，避免轻易跳槽，积累实力以待时机。"

    # ── 婚恋 ──────────────────────────────────────────────────────────────────
    guanxing_score = shishen_scores.get("正官", 0.0)
    qisha_score    = shishen_scores.get("七杀", 0.0)
    is_taohua      = _is_taohua(day_branch, year_branch)

    if is_taohua:
        hunlian = "桃花流年，感情缘分旺盛，单身者宜主动社交，已婚者注重感情保鲜。"
    elif gender == "female" and guanxing_score > 0.15:
        hunlian = "官星透出，单身女性宜扩大社交圈，有正式感情机遇；已婚者感情稳定。"
    elif gender == "female" and qisha_score > 0.2:
        hunlian = "七杀透出，感情有波折，宜冷静面对，不轻率做决策，理性沟通为上。"
    elif year_wuxing in yongshen_favor:
        hunlian = "流年气场和谐，感情顺畅，有利于增进亲密关系的发展。"
    else:
        hunlian = "感情平稳，重在自我成长与经营现有关系，不必急于求成。"

    # ── 健康 ──────────────────────────────────────────────────────────────────
    # 克日主五行
    克day = _OVERCOME.get(year_wuxing, "")
    is_克day = (克day == day_wuxing) if 克day else False

    # 某五行>50%
    dominant_el = max(wuxing_scores, key=lambda k: wuxing_scores.get(k, 0.0)) if wuxing_scores else ""
    dominant_ratio = wuxing_scores.get(dominant_el, 0) / total_wx if dominant_el else 0

    # 与用神合
    is_yongshen_favorable_year = year_wuxing in yongshen_favor

    if is_克day:
        organ = _ORGAN_MAP.get(day_wuxing, "脏腑")
        jiankang = f"流年克日主，关注{organ}健康，防止精力透支，避免过度劳累。"
    elif dominant_ratio > 0.5:
        organ = _ORGAN_MAP.get(dominant_el, "相关脏腑")
        jiankang = f"五行{dominant_el}偏旺超50%，关注{organ}保养，保持饮食均衡。"
    elif is_yongshen_favorable_year:
        jiankang = "流年与用神相合，身体状态普遍较佳，保持规律作息即可。"
    else:
        jiankang = "健康运势平稳，定期体检为宜，注意日常作息与情绪管理。"

    return {
        "财运": caiyun[:60] if len(caiyun) > 60 else caiyun,
        "事业": shiye[:60]  if len(shiye)  > 60 else shiye,
        "婚恋": hunlian[:60] if len(hunlian) > 60 else hunlian,
        "健康": jiankang[:60] if len(jiankang) > 60 else jiankang,
    }
