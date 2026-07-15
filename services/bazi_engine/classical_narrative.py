"""
services/bazi_engine/classical_narrative.py — 格局启发式句式与顺逆气机（B-09 / E-01）

软模板：子平口诀式归纳，**不是** verified 典籍原文，禁止当「典籍依据」展示。
产品层须标 heuristic / inference；有 book+classic_id 的 cite 走 content_policy。
"""

from __future__ import annotations

# 八正格 + 从化/外格 → 启发式句式（soft narrative，非典籍 verified 摘录）
_GEJU_HEURISTIC_SENTENCE: dict[str, str] = {
    "正官格": "官清印顺，贵气有序；宜守正道，忌伤官破官。",
    "七杀格": "杀旺有制则威权；食神制杀、印星化杀，皆为救应。",
    "正印格": "印旺生身，学业才德之基；忌财星坏印。",
    "偏印格": "枭印逢食则化，主技艺出众；宜财制枭。",
    "正财格": "财有根透，日主有力能承；忌比劫争财。",
    "偏财格": "偏财主横财商贸；身强则发，身弱宜印比。",
    "食神格": "食神生财，才学丰富；忌枭印夺食。",
    "伤官格": "伤官见官为忌；佩印或生财，可化凶为秀。",
    "建禄格": "月令临官，日主有根；取财官为用。",
    "月刃格": "刃旺须制，官杀制刃为首。",
    "从旺格": "从旺宜顺，逆之则祸；助旺忌克。",
    "专旺格": "一气专旺，顺之则吉，逆之则凶。",
    "曲直格": "木气专旺，仁寿之格；喜水木，忌金来破。",
    "炎上格": "火气专旺，礼智名显；喜木火，忌水来激。",
    "稼穑格": "土气专旺，信厚守成；喜火土，忌木疏太过。",
    "从革格": "金气专旺，威武刚烈；喜土金，忌火炼太过。",
    "润下格": "水气专旺，智谋机变；喜金水，忌土来堤。",
    "化土格": "甲己化土，化气已成；喜土火，忌木克。",
    "化金格": "乙庚化金，化气已成；喜土金，忌火克。",
    "化水格": "丙辛化水，化气已成；喜金水，忌土克。",
    "化木格": "丁壬化木，化气已成；喜水木，忌金克。",
    "化火格": "戊癸化火，化气已成；喜木火，忌水克。",
    "从财格": "弃命从财，宜顺财势；忌比劫印比夺财。",
    "从官杀格": "弃命从官杀，宜服从管理；忌食伤制杀。",
    "从儿格": "弃命从食伤，专事创作技艺。",
    "从势格": "日主极弱，顺势而从最强之神。",
    "普通格": "五行较均衡，以扶抑调候为用。",
}

_DERIVED_GEJU_SENTENCE: dict[str, str] = {
    "伤官佩印格": "伤官佩印，才华有制，贵气内蕴。",
    "杀印相生格": "杀印相生，威权与学识并重。",
    "食神制杀格": "食神制杀，以柔克刚，清贵之格。",
    "财滋弱杀格": "财滋弱杀，杀有源而不孤。",
    "官杀混杂格": "官杀混杂，须取清用或制化，方得贵气。",
    "伤官见官格": "伤官见官，为祸百端；佩印或生财可解。",
    "财多身弱格": "财多身弱，富屋贫人；宜印比扶身。",
    "印绶护身格": "印绶护身，逢凶化吉；忌财星坏印。",
    "食神生财格": "食神生财，福禄自至；忌枭印夺食。",
    "羊刃驾杀格": "羊刃驾杀，威权显赫；宜制不宜冲。",
}

# 兼容旧名：仍指向同一字典（勿当作典籍引用表）
_GEJU_CLASSIC_SENTENCE = _GEJU_HEURISTIC_SENTENCE


def geju_heuristic_sentence(geju_name: str, derived_geju: str | None = None) -> str:
    """返回格局对应的启发式句式；未知格局返回通用说明。非 verified 典籍摘录。"""
    if derived_geju and derived_geju in _DERIVED_GEJU_SENTENCE:
        return _DERIVED_GEJU_SENTENCE[derived_geju]
    return _GEJU_HEURISTIC_SENTENCE.get(geju_name, f"{geju_name or '普通格'}：以用神喜忌与大运流年参论。")


def geju_classic_sentence(geju_name: str, derived_geju: str | None = None) -> str:
    """已弃用别名：请用 geju_heuristic_sentence。保留以免破坏调用方。"""
    return geju_heuristic_sentence(geju_name, derived_geju)


def is_soft_geju_narrative(text: str | None) -> bool:
    """判别 classic_ref 是否为软模板（无【书名】前缀的引擎句）。"""
    if not text or not str(text).strip():
        return False
    s = str(text).strip()
    if s.startswith("【") and "】" in s[:40]:
        return False
    return True


def shun_ni(
    direction: str,
    yongshen_shift: str = "neutral",
    *,
    tier: str = "",
) -> dict[str, str]:
    """
    顺逆气机 helper：综合大运方向与用神进退。

    Returns:
        {tone, summary} — tone 为 顺/逆/平
    """
    fwd = direction == "forward"
    if yongshen_shift == "forward":
        tone = "顺"
        summary = "大运顺行且用神得助，气机流通" if fwd else "大运逆行而用神仍进，宜守中藏锋"
    elif yongshen_shift == "backward":
        tone = "逆"
        summary = "用神受制，宜稳守过渡" if fwd else "逆行叠忌，忌重大决断"
    else:
        tone = "平"
        summary = "气机中和，随运而变"
    if tier:
        summary = f"{summary}（{tier}）"
    return {"tone": tone, "summary": summary}
