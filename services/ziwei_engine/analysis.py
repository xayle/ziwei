"""
services/ziwei_engine/analysis.py — 逐宫文字解读模板

提供各宫主星组合的简要性质描述，
以及命宫/夫妻/事业/财帛等核心宫位解读。
"""
from __future__ import annotations

from .tables import PALACE_NAMES, BRANCHES
from .stars_main import StarPosition

# ──────────────────────────────────────────────────────────────
# 单星性质简介（精简版）
# ──────────────────────────────────────────────────────────────
STAR_DESC: dict[str, str] = {
    "紫微": "紫微为帝星，主贵气、领导力、孤独，性格自尊要求高",
    "天机": "天机为智慧星，聪明善变，适合谋划，感情多波折",
    "太阳": "太阳为父星/官星，光明热情，男命旺，宜公众事务",
    "武曲": "武曲为财星，刚毅果断，理财务实，感情较硬",
    "天同": "天同为福星，性情温和，享受生活，贵人多",
    "廉贞": "廉贞为囚星/次桃花，多才多艺，是非较多，感情纠葛",
    "天府": "天府为库星，保守稳重，积累财富，品质贵气",
    "太阴": "太阴为母星/田宅/财帛，感性细腻，女命尤佳",
    "贪狼": "贪狼为桃花/欲望星，多才艺，好享乐，感情丰富",
    "巨门": "巨门为口才/暗曜，能言善辩，多口舌是非",
    "天相": "天相为印星/服务，忠厚老实，乐于助人，宫廷气质",
    "天梁": "天梁为荫星，有长辈缘，清高孤傲，宜医卜星象",
    "七杀": "七杀为将星，英勇果断，冲劲十足，开创力强",
    "破军": "破军为耗星/先锋，变动不休，破坏中求生机，改革力强",
}

# ──────────────────────────────────────────────────────────────
# 亮度对宫位影响的简要说明
# ──────────────────────────────────────────────────────────────
BRIGHTNESS_EFFECT: dict[str, str] = {
    "庙": "入庙，力量充分发挥，吉星益善，凶星趋吉避凶",
    "旺": "旺地，发挥七八成，整体正面",
    "得": "得地，平稳，中性偏吉",
    "利": "利益之地，情况尚可",
    "平": "平和，力量平淡",
    "不": "不得力，力量受限",
    "陷": "落陷，力量最弱，吉星难发吉，凶星凶性增",
}

# ──────────────────────────────────────────────────────────────
# 主要辅星性质
# ──────────────────────────────────────────────────────────────
AUX_STAR_DESC: dict[str, str] = {
    "文昌": "科甲之星，利考试、文书、名誉",
    "文曲": "才华之星，利艺术、口才、异性缘",
    "天魁": "贵人星（天乙贵人），助力贵人相助",
    "天钺": "贵人星（玉堂贵人），助力贵人相助",
    "左辅": "辅助星，带来协助与补充",
    "右弼": "辅助星，带来协助与支持",
    "禄存": "财禄之星，稳健财源，亦有孤克之象",
    "天马": "驿马星，主变动奔波，宜出行",
    "擎羊": "煞星，刀伤血光，冲劲大，主是非竞争",
    "陀罗": "煞星，拖延纠缠，暗中阻力",
    "火星": "煞星，暴烈冲动，变化剧烈",
    "铃星": "煞星，暗耗纠缠，变化迟缓",
    "地空": "煞星，耗散思想，空想多",
    "地劫": "煞星，劫财破耗，意外损失",
}


def _stars_in_palace(
    palace_branch: int,
    main_stars: dict[str, StarPosition],
    aux_stars: dict[str, int],
) -> tuple[list[str], list[str]]:
    """返回某地支宫位中的（主星列表, 辅星列表）。"""
    mains = [
        f"{pos.name}({''.join(pos.transforms) if pos.transforms else pos.brightness})"
        for name, pos in main_stars.items()
        if pos.branch_idx == palace_branch
    ]
    auxes = [
        name for name, b in aux_stars.items()
        if b == palace_branch and not name.endswith("placeholder")
    ]
    return mains, auxes


def generate_palace_analysis(
    palace_idx: int,
    palace_branch: int,
    main_stars: dict[str, StarPosition],
    aux_stars: dict[str, int],
) -> str:
    """为某一宫位生成文字解读。"""
    palace_name = PALACE_NAMES[palace_idx % 12]
    branch_name = BRANCHES[palace_branch]
    mains, auxes = _stars_in_palace(palace_branch, main_stars, aux_stars)

    lines: list[str] = [f"【{palace_name} · {branch_name}宫】"]

    if mains:
        lines.append("主星：" + "、".join(mains))
        # 添加每颗主星的性质描述
        for pos in main_stars.values():
            if pos.branch_idx == palace_branch and pos.name in STAR_DESC:
                lines.append(f"  {STAR_DESC[pos.name]}")
    else:
        lines.append("主星：（空宫，借对宫星曜论命）")

    if auxes:
        lines.append("辅星：" + "、".join(auxes))

    return "\n".join(lines)


def generate_full_analysis(
    main_stars: dict[str, StarPosition],
    aux_stars: dict[str, int],
    life_palace_branch: int,
    life_palace_stem: str,
    body_palace_branch: int,
    wuxing_ju: int,
    wuxing_ju_name: str,
    gender: str,
) -> dict[str, str]:
    """
    生成完整的命盘文字解读字典。
    返回 {宫位名: 解读文字}
    """
    result: dict[str, str] = {}

    # 命盘信息头
    result["命盘概述"] = (
        f"命宫：{BRANCHES[life_palace_branch]}宫（{life_palace_stem}{BRANCHES[life_palace_branch]}）\n"
        f"身宫：{BRANCHES[body_palace_branch]}宫\n"
        f"五行局：{wuxing_ju_name}（{wuxing_ju}局）\n"
        f"性别：{gender}"
    )

    # 逐宫解读
    for i in range(12):
        b = (life_palace_branch - i) % 12
        analysis = generate_palace_analysis(i, b, main_stars, aux_stars)
        result[PALACE_NAMES[i]] = analysis

    return result


def generate_summary(
    main_stars: dict[str, StarPosition],
    aux_stars: dict[str, int],
    life_palace_branch: int,
) -> str:
    """生成命盘核心要点摘要（纯文本）。"""
    # 命宫主星
    life_mains = [pos for pos in main_stars.values() if pos.branch_idx == life_palace_branch]

    lines = ["═" * 40, "紫微斗数命盘核心要点", "═" * 40]

    if life_mains:
        star_names = "、".join(p.name for p in life_mains)
        lines.append(f"命宫主星：{star_names}")
        for p in life_mains:
            desc = STAR_DESC.get(p.name, "")
            if desc:
                lines.append(f"  {desc}")
    else:
        lines.append("命宫：空宫，借对宫论断")

    # 检查吉凶杂星
    sha_stars = [s for s in ["擎羊", "陀罗", "火星", "铃星", "地空", "地劫"]
                 if s in aux_stars and aux_stars[s] == life_palace_branch]
    if sha_stars:
        lines.append(f"命宫煞星：{'、'.join(sha_stars)} — 性格强烈，人生多波折，需磨砺成长")

    ji_stars = [s for s in ["文昌", "文曲", "天魁", "天钺", "左辅", "右弼"]
                if s in aux_stars and aux_stars[s] == life_palace_branch]
    if ji_stars:
        lines.append(f"命宫吉星：{'、'.join(ji_stars)} — 贵人助力，学业事业顺遂")

    lines.append("═" * 40)
    return "\n".join(lines)
