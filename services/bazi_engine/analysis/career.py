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
        # 注意：用切片复制，避免与 industries 共享同一个列表对象
        directions = list(_GEJU_CAREER.get(geju_name, ["实业", "综合管理"]))
    directions = list(dict.fromkeys(directions))[:5]

    # ─── 行业推荐 ─────────────────────────────────────────────────────
    # 同样用切片复制，避免 extend 污染 directions
    industries = list(_GEJU_CAREER.get(geju_name, ["综合行业"]))
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
        development_advice = (
            f"官杀有力且日主中和，具备较高的领导潜质，建议主动争取管理职位或项目负责人。"
            f"利用{geju_name}格局特点，在公司或行业内拓展多方人脉，建立跳跃式资源网络。"
            f"规划未来 3-5 年精进目标，系统性提升管理方法论与岗位可见度。"
        )
    elif shi_shang_pct >= 0.4:
        development_advice = (
            f"食伤旺盛，创造力与表达力尤为突出，最适合技术/创意/自由职业路线，谨慎进入官僚体系。"
            f"建议持续输出高质量作品或方案，将个人 IP 与专业能力稳固、变现。"
            f"可考虑展示个人作品集、申请行业各类奖项或将创意成果产品化、商业化。"
        )
    else:
        development_advice = (
            f"该命局适合稳步深耕，系统建立{geju_name}相关领域的专业技能体系。"
            f"在用神五行顺运年份把握重要决策时机，平日夯实专业基础、取得资质认证，逐步扩展跨部门协作能力。"
            f"弹性应对市场变化，不拘泥于单一道路，保持对新机遇的识别能力。"
        )

    # ─── 最佳行动时间 ─────────────────────────────────────────────────────
    _ys_top = "、".join(_ELEMENT_CN.get(e, e) for e in yongshen_favor[:2]) or "用神"
    optimal_timing = (
        f"{geju_name}格局下，用神（{_ys_top}）顺运年份为跳槽或创业最佳时机。"
        f"进入用神旺天干大运后，应求考或创业成功率会于相同格局人群中显著提升。"
        f"建议提前1年备资源、监测流年五行对期，在天时地利人和均具备时再出手。"
    )

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

    _dir_top = "、".join(directions[:3])
    _ind_top = "、".join(industries[:3])
    interp = (
        f"事业评分为 {career_score} 分，命局格局为【{geju_name}】，"
        f"主要事业方向包括：{_dir_top}，推荐优先考虑 {_ind_top} 等行业。"
        f"领导潜力评估：{'具备，可向管理路线发展' if leadership else '有限，适合专家型职业路线'}。"
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
