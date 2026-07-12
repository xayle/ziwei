"""
services/ziwei_engine/analysis.py — 逐宫文字解读模板

提供各宫主星组合的简要性质描述，
以及命宫/夫妻/事业/财帛等核心宫位解读。
"""

from __future__ import annotations

from .stars_main import StarPosition
from .tables import BRANCHES, PALACE_NAMES

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

# 宫位+主星组合断语（COMBO_TABLE，Z-07）
COMBO_TABLE: dict[str, str] = {
    "命宫+紫微": "帝星坐命，领导统御，贵气自显",
    "命宫+天机": "机星坐命，智谋多变，宜策划幕僚",
    "命宫+太阳": "太阳坐命，光明外向，男命尤佳",
    "命宫+武曲": "武曲坐命，务实理财，刚毅果断",
    "命宫+天同": "天同坐命，温和享福，人缘佳",
    "命宫+廉贞": "廉贞坐命，才艺丰富，防口舌是非",
    "命宫+天府": "天府坐命，稳重守成，财库渐丰",
    "命宫+太阴": "太阴坐命，细腻内敛，女命尤吉",
    "命宫+贪狼": "贪狼坐命，多才多欲，桃花丰沛",
    "夫妻宫+天同": "天同守夫妻，感情温和，宜慢热经营",
    "夫妻宫+廉贞": "廉贞守夫妻，感情浓烈，防纠葛",
    "财帛宫+武曲": "武曲守财，正财稳健，理财见长",
    "财帛宫+天府": "天府守财，积蓄能力强，守成为上",
    "官禄宫+紫微": "紫微守官，事业有统御机会",
    "官禄宫+七杀": "七杀守官，竞争开创，宜武职技艺",
    "迁移宫+天马": "天马守迁，动中求发展，宜出行",
}


def combo_narrative(palace_name: str, star_name: str) -> str:
    """查 COMBO_TABLE 得组合断语；无则回退单星描述。"""
    key = f"{palace_name}+{star_name}"
    return COMBO_TABLE.get(key) or STAR_DESC.get(star_name, "")


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

# ──────────────────────────────────────────────────────────────
# 三段式结构化解读数据表
# ──────────────────────────────────────────────────────────────
STAR_TRAIT: dict[str, str] = {
    "紫微": "尊贵自主、领导力强",
    "天机": "聪敏机变、善于谋划",
    "太阳": "光明热情、公众导向",
    "武曲": "务实果断、财务强势",
    "天同": "温和享福、贵人多助",
    "廉贞": "多才多艺、是非较多",
    "天府": "稳健保守、积累财富",
    "太阴": "感性细腻、内敛财聚",
    "贪狼": "多才多欲、桃花丰沛",
    "巨门": "口才出众、明暗是非",
    "天相": "忠厚助人、服务协调",
    "天梁": "清高孤傲、长辈缘深",
    "七杀": "勇猛果断、开创冲劲",
    "破军": "变动不休、破旧立新",
}

STAR_CONCERN_SHORT: dict[str, str] = {
    "紫微": "注意高傲孤立、过度自我要求",
    "天机": "防情感多变、过度谋算",
    "太阳": "防好面子、情绪起伏",
    "武曲": "防感情强硬、冲突加剧",
    "天同": "防过度安逸、进取不足",
    "廉贞": "防口舌是非、感情纠缠",
    "天府": "防过度保守、错失机遇",
    "太阴": "防情绪化、优柔寡断",
    "贪狼": "防欲望泛滥、定力不足",
    "巨门": "防是非缠身、多疑难信",
    "天相": "防依赖过强、决断力弱",
    "天梁": "防清高孤僻、不合群",
    "七杀": "防冲劲过猛、伤及自他",
    "破军": "防变动耗散、难以积累",
}

SHA_SHORT: dict[str, str] = {
    "擎羊": "刀伤血光与是非竞争",
    "陀罗": "拖延纠缠与暗中阻力",
    "火星": "暴烈冲动与突发变化",
    "铃星": "暗耗纠缠与迟缓变化",
    "地空": "空想耗散与思路发散",
    "地劫": "劫财破耗与意外损失",
}

HUA_SHORT: dict[str, str] = {
    "化禄": "财运贵气增旺、贵人多助",
    "化权": "权势决断力强、主导局面",
    "化科": "名声文采显扬、有利名誉",
    "化忌": "宜防是非损耗、进展受阻",
}

PALACE_DOMAIN: dict[str, str] = {
    "命宫": "性格格局",
    "兄弟宫": "兄弟财库",
    "夫妻宫": "婚恋感情",
    "子女宫": "子嗣下属",
    "财帛宫": "财运进财",
    "疾厄宫": "健康体质",
    "迁移宫": "外出社交",
    "奴仆宫": "交友合作",
    "官禄宫": "事业仕途",
    "田宅宫": "家宅资产",
    "福德宫": "精神享乐",
    "父母宫": "父母上司",
}

PALACE_SUGGESTION: dict[str, str] = {
    "命宫": "充分了解自身先天优势与局限，以主动成长代替宿命论，将命宫特质转化为事业与人际的核心竞争力。",
    "兄弟宫": "与手足及同辈合作时务必以书面约定权责与财务，感情再好也应保持清晰边界。",
    "夫妻宫": "感情上主动而不强势，尊重对方节奏；婚前了解核心价值观，婚后保持各自独立空间。",
    "子女宫": "对子女或下属以引导代替控制，容许失败与成长；创意类短期投资小额分散，做好止损预案。",
    "财帛宫": "建立多元进财渠道，制定理财计划，避免冲动决策；遭遇财务波动时优先保住本金。",
    "疾厄宫": "养成规律作息与运动习惯，定期体检；做好心理压力管理，关注先天易发病部位。",
    "迁移宫": "主动把握出行与展示机会，拓宽视野与人脉；出行前做好风险预案与应急准备。",
    "奴仆宫": "与合作伙伴建立清晰规则与契约，以长期信任代替短期利益；冲突时优先协商而非对抗。",
    "官禄宫": "选择与命盘星性契合的职业方向，稳步积累专业声望；职场争议中以实力说话，避免过早锋芒毕露。",
    "田宅宫": "用心维护家庭关系，不动产决策宜稳健；改善居家环境有助身心与运势共同提升。",
    "福德宫": "培养内在充实感，减少向外寻求认可；精神投资（学习、兴趣、信仰）回报最为持久。",
    "父母宫": "主动改善与父母、上司的沟通方式；争取支持时选择恰当时机与情绪平稳的表达方式。",
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
    auxes = [name for name, b in aux_stars.items() if b == palace_branch and not name.endswith("placeholder")]
    return mains, auxes


# ─────────────────────────────────────────────────────────────
# 吉星集合 / 煞星集合（用于 tags 生成）
# ─────────────────────────────────────────────────────────────
_JI_STARS = {"文昌", "文曲", "天魁", "天钺", "左辅", "右弼", "禄存", "天马"}
_SHA_STARS = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}


def generate_palace_tags(
    palace_branch: int,
    main_stars: dict[str, StarPosition],
    aux_stars: dict[str, int],
) -> list[str]:
    """
    为宫位生成简短语义标签列表。
    例：["紫微·庙·化禄", "天相·旺", "天魁", "⚡擎羊"]
    """
    tags: list[str] = []
    mains = [pos for pos in main_stars.values() if pos.branch_idx == palace_branch]

    if not mains:
        tags.append("空宫")
    else:
        for pos in mains:
            label = pos.name
            if pos.brightness in ("庙", "旺", "陷"):
                label += f"·{pos.brightness}"
            for t in pos.transforms:
                label += f"·{t}"
            tags.append(label)

    ji = [s for s in _JI_STARS if s in aux_stars and aux_stars[s] == palace_branch]
    tags.extend(ji)

    sha = [s for s in _SHA_STARS if s in aux_stars and aux_stars[s] == palace_branch]
    if sha:
        tags.append("⚡" + "·".join(sha))

    return tags


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
        # 添加每颗主星的性质描述（按亮度/四化分层）
        for pos in main_stars.values():
            if pos.branch_idx == palace_branch and pos.name in STAR_DESC:
                base = STAR_DESC[pos.name]
                # 亮度附注
                if pos.brightness == "庙":
                    bri_note = "（入庙，力量充分，吉性倍增）"
                elif pos.brightness == "旺":
                    bri_note = "（旺地，发挥七八成，整体正面）"
                elif pos.brightness == "陷":
                    bri_note = "（落陷，力量最弱，吉星难发力，需注意）"
                else:
                    bri_note = ""
                # 四化附注
                hua_notes = []
                for t in pos.transforms:
                    if "化禄" in t:
                        hua_notes.append("逢化禄，财运/贵气大增")
                    elif "化权" in t:
                        hua_notes.append("逢化权，权势/决断力强")
                    elif "化科" in t:
                        hua_notes.append("逢化科，名声/文采显扬")
                    elif "化忌" in t:
                        hua_notes.append("逢化忌，需防是非/损耗")
                hua_str = "；".join(hua_notes)
                note = bri_note + (f"；{hua_str}" if hua_str else "")
                lines.append(f"  {base}{note}")
    else:
        # 空宫：借对宫星曜论命
        opp_branch = _opposite_branch(palace_branch, main_stars)
        opp_mains = (
            [pos for pos in main_stars.values() if pos.branch_idx == opp_branch] if opp_branch is not None else []
        )

        if opp_mains:
            opp_names = "、".join(p.name for p in opp_mains)
            lines.append(f"主星：（空宫，借对宫 {opp_names} 论命）")
            for pos in opp_mains:
                if pos.name in STAR_DESC:
                    lines.append(f"  [借] {STAR_DESC[pos.name]}")
        else:
            lines.append("主星：（空宫，借对宫论命）")

    if auxes:
        lines.append("辅星：" + "、".join(auxes))
        for ax in auxes:
            if ax in AUX_STAR_DESC:
                lines.append(f"  {AUX_STAR_DESC[ax]}")

    return "\n".join(lines)


def _opposite_branch(
    palace_branch: int,
    main_stars: dict[str, StarPosition],
) -> int | None:
    """返回对宫的地支索引（+6），确保该宫有星存在。"""
    opp = (palace_branch + 6) % 12
    has_star = any(pos.branch_idx == opp for pos in main_stars.values())
    return opp if has_star else None


# ──────────────────────────────────────────────────────────────
# 三段式结构化解读（结论 / 解释 / 建议 / 短摘tooltip）
# ──────────────────────────────────────────────────────────────
def generate_palace_structured(
    palace_idx: int,
    palace_branch: int,
    main_stars: dict[str, StarPosition],
    aux_stars: dict[str, int],
) -> tuple[str, str, str, str]:
    """
    为宫位生成三段式结构化解读。
    返回 (conclusion, explanation, suggestion, tooltip)。
      conclusion : 一句话结论（40–70字）
      explanation: 逐星+辅星分段解释（换行符分隔，2–3段）
      suggestion : 一行可操作建议（30–60字）
      tooltip    : 20–40字宫格悬浮摘要
    """
    palace_name = PALACE_NAMES[palace_idx % 12]
    domain = PALACE_DOMAIN.get(palace_name, "宫位特质")

    mains = [pos for pos in main_stars.values() if pos.branch_idx == palace_branch]
    aux_in = [name for name, b in aux_stars.items() if b == palace_branch]
    sha_in = [s for s in SHA_SHORT if s in aux_in]
    ji_in = [s for s in _JI_STARS if s in aux_in]

    # ── 结论 ─────────────────────────────────────────────────
    if mains:
        star_part = "、".join(pos.name for pos in mains)
        traits = "、".join(dict.fromkeys(STAR_TRAIT.get(pos.name, pos.name) for pos in mains))
        all_hua = []
        for pos in mains:
            for t in pos.transforms:
                if t in HUA_SHORT:
                    all_hua.append(f"{t}（{HUA_SHORT[t][:7]}）")
        hua_part = "，".join(all_hua)
        sha_part = "，".join(SHA_SHORT[s][:9] for s in sha_in[:2]) if sha_in else ""
        concern = STAR_CONCERN_SHORT.get(mains[0].name, "")

        prefix = f"{palace_name}以{star_part}为主，{traits}"
        if hua_part:
            prefix += f"；{hua_part}"
        if sha_part:
            prefix += f"，应防{sha_part}"
        elif concern:
            prefix += f"，{concern}"
        conclusion = prefix.rstrip("，；") + "。"
    else:
        opp = (palace_branch + 6) % 12
        opp_mains = [pos for pos in main_stars.values() if pos.branch_idx == opp]
        opp_str = "、".join(p.name for p in opp_mains) if opp_mains else "对宫"
        conclusion = f"{palace_name}为空宫，借{opp_str}照射论命，{domain}以外显方式呈现，特质较为隐性。"

    # ── 解释 ─────────────────────────────────────────────────
    exp_lines: list[str] = []
    if mains:
        for pos in mains:
            base = STAR_DESC.get(pos.name, f"{pos.name}为主星")
            if pos.brightness in ("庙", "旺"):
                bri = f"（{pos.brightness}·力量充分）"
            elif pos.brightness == "陷":
                bri = "（陷·力量受限，需谨慎）"
            elif pos.brightness in ("平", "不"):
                bri = f"（{pos.brightness}·力量平淡）"
            else:
                bri = ""
            hua_items = [f"{t}→{HUA_SHORT[t]}" for t in pos.transforms if t in HUA_SHORT]
            hua_s = "；".join(hua_items)
            line = f"■ {pos.name}{bri}：{base}"
            if hua_s:
                line += f"；{hua_s}"
            exp_lines.append(line + "。")
    else:
        exp_lines.append(f"■ {palace_name}无主星入宫（空宫），以对宫星曜照射，宫位特质延迟或隐性显现。")

    aux_parts: list[str] = []
    for ax in aux_in[:5]:
        if ax in AUX_STAR_DESC:
            aux_parts.append(f"{ax}（{AUX_STAR_DESC[ax][:12]}）")
        elif ax in SHA_SHORT:
            aux_parts.append(f"⚠{ax}（{SHA_SHORT[ax]}）")
    if aux_parts:
        exp_lines.append("辅星：" + "；".join(aux_parts) + "。")

    if ji_in:
        exp_lines.append(f"贵人星{' 、'.join(ji_in)}同宫，名誉与贵人层面获助。")

    explanation = "\n".join(exp_lines)

    # ── 建议 ─────────────────────────────────────────────────
    base_sug = PALACE_SUGGESTION.get(palace_name, f"深入了解{domain}特质，积极趋吉避凶。")
    if sha_in:
        sha_names = "、".join(sha_in[:2])
        suggestion = base_sug.rstrip("。") + f"；留意煞星{sha_names}带来的变数与耗损。"
    else:
        suggestion = base_sug

    # ── Tooltip ───────────────────────────────────────────────
    if mains:
        star_tt = "，".join(pos.name + ("·" + pos.transforms[0] if pos.transforms else "") for pos in mains)
        trait_tt = STAR_TRAIT.get(mains[0].name, "")
        sha_tt = f"；注意{SHA_SHORT[sha_in[0]][:8]}" if sha_in else ""
        tooltip = f"{star_tt}：{trait_tt}{sha_tt}。"
    else:
        tooltip = f"{palace_name}空宫，{domain}隐性，借对宫照射观察。"

    if len(tooltip) > 45:
        tooltip = tooltip[:43] + "…"

    return conclusion, explanation, suggestion, tooltip


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
    life_mains = [pos for pos in main_stars.values() if pos.branch_idx == life_palace_branch]
    main_names = "、".join(dict.fromkeys(pos.name for pos in life_mains)) if life_mains else "空宫"
    main_traits = (
        "、".join(dict.fromkeys(STAR_TRAIT.get(pos.name, pos.name) for pos in life_mains))
        if life_mains
        else "需借对宫观察"
    )
    summary_parts = [
        f"命宫为{BRANCHES[life_palace_branch]}宫（{life_palace_stem}{BRANCHES[life_palace_branch]}）",
        f"身宫为{BRANCHES[body_palace_branch]}宫",
        f"五行局为{wuxing_ju_name}（{wuxing_ju}局）",
    ]
    if life_mains:
        summary_parts.append(f"命宫主星以{main_names}为主，气质偏向{main_traits}")
    else:
        summary_parts.append("命宫为空宫，宜结合对宫星曜观察")
    summary_parts.append(f"性别为{gender}")
    result["命盘概述"] = "；".join(summary_parts) + "。"

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

    parts: list[str] = []

    if life_mains:
        star_names = "、".join(p.name for p in life_mains)
        traits = "、".join(dict.fromkeys(STAR_TRAIT.get(p.name, p.name) for p in life_mains))
        parts.append(f"命宫主星以{star_names}为主，气质偏向{traits}")
    else:
        parts.append("命宫为空宫，需借对宫星曜观察")

    # 检查吉凶杂星
    sha_stars = [
        s
        for s in ["擎羊", "陀罗", "火星", "铃星", "地空", "地劫"]
        if s in aux_stars and aux_stars[s] == life_palace_branch
    ]
    if sha_stars:
        concern = "、".join(SHA_SHORT.get(s, s) for s in sha_stars[:2])
        parts.append(f"同宫见{'、'.join(sha_stars)}，需留意{concern}")

    ji_stars = [
        s
        for s in ["文昌", "文曲", "天魁", "天钺", "左辅", "右弼"]
        if s in aux_stars and aux_stars[s] == life_palace_branch
    ]
    if ji_stars:
        parts.append(f"同宫见{'、'.join(ji_stars)}，贵人助力与学习表达更容易显现")

    if life_mains:
        first_star = life_mains[0].name
        concern = STAR_CONCERN_SHORT.get(first_star)
        if concern:
            parts.append(f"核心提示：{concern}")

    return "；".join(parts) + "。"
