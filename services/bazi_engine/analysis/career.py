"""
services/bazi_engine/analysis/career.py — 事业引擎 (M2 任务 2.02)

算法规格: §4.11-B
"""
from __future__ import annotations

from app.schemas.analysis import CareerAnalysisModel

# 天干五行
_STEM_ELEMENT: dict[str, str] = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth", "己": "earth",
    "庚": "metal", "辛": "metal",
    "壬": "water", "癸": "water",
}

# 地支六冲
_BRANCH_CHONG: dict[str, str] = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}

# 地支五行
_BRANCH_ELEMENT: dict[str, str] = {
    "子": "water", "亥": "water",
    "寅": "wood",  "卯": "wood",
    "巳": "fire",  "午": "fire",
    "申": "metal", "酉": "metal",
    "丑": "earth", "辰": "earth", "未": "earth", "戌": "earth",
}

_ELEMENT_CN: dict[str, str] = {
    "metal": "金", "wood": "木", "water": "水", "fire": "火", "earth": "土",
}

# 格局对应事业方向
_GEJU_CAREER: dict[str, list[str]] = {
    "正官格": ["公务员", "管理层", "行政法务"],
    "七杀格": ["军警", "竞技", "高压行业"],
    "正印格": ["教育", "学术", "文化"],
    "偏印格": ["宗教", "艺术", "研究"],
    "正财格": ["金融商贸", "销售"],
    "偏财格": ["投资", "商业", "销售"],
    "食神格": ["餐饮", "创意", "技艺"],
    "伤官格": ["技术研发", "文创"],
    "建禄格": ["实业制造", "管理"],
    "羊刃格": ["竞争性行业", "体育"],
    "从财格": ["商业贸易", "金融"],
    "从官格": ["仕途", "管理"],
    "从儿格": ["技艺", "文艺"],
}


def compute_career(
    geju_name: str,
    yongshen_favor: list[str],
    yongshen_avoid: list[str],
    shishen_scores: dict[str, float],
    strength_score: float,
    dayun_list: list[dict],
    day_branch: str = "",
) -> CareerAnalysisModel:
    """
    §4.11-B 事业引擎

    Parameters:
        geju_name:      格局名称（如 "正财格"）
        yongshen_favor: 用神五行列表（英文）
        yongshen_avoid: 忌神五行列表
        shishen_scores: 十神得分分布
        strength_score: 日主强弱分
        dayun_list:     大运列表
        day_branch:     日支
    """
    total = sum(shishen_scores.values()) or 1.0

    guan = shishen_scores.get("正官", 0.0)
    sha  = shishen_scores.get("七杀", 0.0)
    shi  = shishen_scores.get("食神", 0.0)
    shang = shishen_scores.get("伤官", 0.0)
    cai  = shishen_scores.get("正财", 0.0) + shishen_scores.get("偏财", 0.0)
    yin  = shishen_scores.get("正印", 0.0) + shishen_scores.get("偏印", 0.0)

    guan_sha_pct = (guan + sha) / total
    shi_shang_pct = (shi + shang) / total
    cai_pct = cai / total
    yin_pct = yin / total

    # ─── 事业方向 ──────────────────────────────────────────────────────
    directions: list[str] = []
    if guan_sha_pct >= 0.6:
        directions = ["管理", "仕途", "行政"]
    elif shi_shang_pct >= 0.6:
        directions = ["技术", "创意", "研发"]
    elif cai_pct >= 0.6:
        directions = ["商业", "销售", "贸易"]
    elif yin_pct >= 0.6:
        directions = ["学术", "文职", "教育"]
    else:
        directions = _GEJU_CAREER.get(geju_name, ["实业", "综合管理"])

    # ─── 行业推荐 ─────────────────────────────────────────────────────
    industries = _GEJU_CAREER.get(geju_name, ["综合行业"])
    for el in yongshen_favor:
        if el == "metal":
            industries.extend(["金融", "法律", "机械"])
        elif el == "wood":
            industries.extend(["教育", "餐饮", "农业"])
        elif el == "water":
            industries.extend(["IT", "运输", "贸易"])
        elif el == "fire":
            industries.extend(["传媒", "能源", "餐饮"])
        elif el == "earth":
            industries.extend(["房地产", "建筑", "保险"])
    industries = list(dict.fromkeys(industries))[:5]

    # ─── 领导潜力 ─────────────────────────────────────────────────────
    leadership = (guan_sha_pct >= 0.25) and (40 <= strength_score <= 70)

    # ─── 发展建议 ─────────────────────────────────────────────────────
    if leadership:
        development_advice = "官杀有力、日主中和，具备领导潜质，可积极争取管理职位。"
    elif shi_shang_pct >= 0.4:
        development_advice = "食伤旺盛，创造力强，适合技术/创意路线，慎入官僚体系。"
    else:
        development_advice = "稳步积累专业技能，构建个人核心竞争力。"

    # ─── 最佳行动时间 ──────────────────────────────────────────────────
    optimal_timing = "用神旺运期间为最佳跳槽/创业时机"

    # ─── career_score ─────────────────────────────────────────────────
    # base ∈ [0, 40]（当 guan_sha_pct=1.0 时最大）；×2.5 归一化到 [0, 100]
    base = guan_sha_pct * 40 + cai_pct * 30 + yin_pct * 20 + shi_shang_pct * 10
    career_score = int(min(100, max(0, round(base * 2.5))))

    # ─── inference_tags ─────────────────────────────────────────────
    tags = []
    if guan_sha_pct >= 0.4:
        tags.append("官杀偏旺")
    if shi_shang_pct >= 0.4:
        tags.append("食伤有力")
    if leadership:
        tags.append("领导潜力")
    if strength_score < 30:
        tags.append("日主偏弱需增强")

    interp = (
        f"事业评分{career_score}分，格局{geju_name}，"
        f"主要方向：{'、'.join(directions[:2])}。"
        f"{development_advice}"
        f"（仅供学术研究参考）"
    )

    return CareerAnalysisModel(
        career_score=career_score,
        career_directions=directions,
        suitable_industries=industries,
        leadership_potential=leadership,
        development_advice=development_advice,
        optimal_move_timing=optimal_timing,
        inference_tags=tags,
        interpretation_text=interp,
    )
