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
        if pct >= 0.3:
            desc = "有力，关系较亲近"
        elif pct >= 0.1:
            desc = "一般，关系平淡"
        else:
            desc = "弱，关系疏远或缘分浅"
        if kin not in liu_qin:
            liu_qin[kin] = f"{shen}（{pct*100:.0f}%）{desc}"

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
        strategy = "印星旺，亲和力强，适合贵人推荐型社交，信任口碑。"
    elif food / total >= 0.3:
        strategy = "食神旺，人云亦云，善于分享者得福，多参与社群活动。"
    elif (bi + jie) / total >= 0.4:
        strategy = "比劫旺，竞争感强，需主动建立个人品牌以区分自身价值。"
    else:
        strategy = "命局均衡，人际关系中庸，广泛社交比专注单一圈层更有利。"

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

    interp = (
        f"六亲关系评分{relationship_score}分。"
        f"贵人为{'、'.join(noble_people[:2])}。"
        f"{strategy}"
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
