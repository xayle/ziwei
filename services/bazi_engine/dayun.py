"""
services/bazi_engine/dayun.py — 大运排盘（M1 任务 1.07）

修复项:
  S9/P59: 男阳顺/男阴逆/女阳逆/女阴顺（旧代码忽略性别参数）
  P60:    逆排锚定改为 prev_jie_dt（旧代码误用 next_jie_dt）

大运方向规则:
  男命阳年生 → 顺行  (forward)
  男命阴年生 → 逆行  (backward)
  女命阳年生 → 逆行  (backward)
  女命阴年生 → 顺行  (forward)
  若 gender=None → 降级: 阳年=顺, 阴年=逆 (与旧代码兼容)

起运岁数公式:
  顺行: delta = next_jie_dt - birth_dt  （正方向到下一节）
  逆行: delta = birth_dt - prev_jie_dt  （逆方向到上一节）
  start_age_months = ceil(delta_days / days_per_month)
  start_age = start_age_months // 12
"""
from __future__ import annotations

from datetime import datetime
from math import ceil
from typing import Optional

from backends import get_jieqi_context
from services.bazi_engine.classic_refs import get_refs_by_tag
from services.bazi_engine.tables import (
    STEMS,
    BRANCHES,
    STEM_ELEMENT,
    get_ten_god,
)

# ──────────────────────────────────────────────────────────────────────────────
# 内部工具
# ──────────────────────────────────────────────────────────────────────────────

def _ganzhi_index(stem: str, branch: str) -> int:
    """60甲子序号 (甲子=0 … 癸亥=59)"""
    si = STEMS.index(stem)
    bi = BRANCHES.index(branch)
    # 甲子(0,0), 乙丑(1,1)... 五年循环干,六年循环支，60年一轮
    # 六十甲子编号 = 干序号 mod 10, 支序号 mod 12, lcm=60
    for i in range(60):
        if i % 10 == si and i % 12 == bi:
            return i
    return 0  # 不可达  # pragma: no cover


def _ganzhi_from_index(idx: int) -> tuple[str, str]:
    i = idx % 60
    return STEMS[i % 10], BRANCHES[i % 12]


# ──────────────────────────────────────────────────────────────────────────────
# 大运方向
# ──────────────────────────────────────────────────────────────────────────────

def _get_direction(
    year_stem: str,
    gender: Optional[str],           # "male" / "female" / None
) -> tuple[str, str]:
    """
    返回 (direction, basis_note)
    direction: "forward" | "backward"
    """
    _, year_yinyang = STEM_ELEMENT.get(year_stem, ("?", "?"))
    year_polarity = year_yinyang  # "yang" or "yin"

    if gender is None:
        # 兼容旧行为：阳年顺/阴年逆
        fwd = year_polarity == "yang"
        basis = "fallback_year_stem_only"
    else:
        is_male = gender.lower() in ("male", "m", "男")
        if is_male:
            fwd = year_polarity == "yang"           # 男阳顺/男阴逆
        else:
            fwd = year_polarity == "yin"            # 女阴顺/女阳逆
        basis = f"gender={gender},year_yinyang={year_polarity}"

    direction = "forward" if fwd else "backward"
    return direction, basis


# ──────────────────────────────────────────────────────────────────────────────
# 大运注释 (hint 生成)
# ──────────────────────────────────────────────────────────────────────────────

_ELEM_WEALTH_HINT: dict[str, str] = {
    "metal": "金旺财运活跃，适宜理财投资，防官非。",
    "water": "水旺流通，财来财去，宜开源节流，保持资金周转。",
    "wood": "木旺事业进取，财运通过努力可得，忌急躁冒进。",
    "fire": "火旺名利双收，财运亮丽，但需防止过度消耗。",
    "earth": "土旺稳健积累，财运平稳，宜不动产投资。",
}
_ELEM_HEALTH_HINT: dict[str, str] = {
    "metal": "金旺注意呼吸系统及肺部健康，辛金需防皮肤病。",
    "water": "水旺注意肾脏、泌尿系统，冬季格外保暖。",
    "wood": "木旺注意肝胆，眼睛，筋骨，保持情绪舒畅。",
    "fire": "火旺注意心脏、血压，避免过于激动，夏日防暑。",
    "earth": "土旺注意脾胃消化，避免过食肥甘厚腻，防湿气。",
}
_ELEM_LOVE_HINT: dict[str, str] = {
    "metal": "金运感情收敛，感情需主动争取，防凉薄之象。",
    "water": "水旺感情流动性强，有缘分，但桃花多则易散。",
    "wood": "木运感情成长，宜稳定发展，异性缘佳。",
    "fire": "火旺感情热烈，易有新邂逅；婚恋宜稳重，防冲动。",
    "earth": "土运感情稳固，宜踏实经营，缘分在实际相处中成长。",
}
_ELEM_CHILD_HINT: dict[str, str] = {
    "metal": "此运子女宜独立、性格坚毅，需给予充足鼓励。",
    "water": "此运子女聪明灵动，宜引导兴趣多方向发展。",
    "wood": "此运子女上进好学，宜培养独立思考能力。",
    "fire": "此运子女热情活泼，需关注情绪管理与专注力。",
    "earth": "此运子女踏实稳重，宜鼓励社交，避免过于保守。",
}

# ── 十神维度 hint（主键：十神名称）────────────────────────────────────────────
_TEN_GOD_WEALTH_HINT: dict[str, str] = {
    "比肩": "比肩当令，同行竞争加剧，财运需靠自身实力开拓，宜独辟蹊径、走差异化路线；防合作纠纷，资金往来须留书面凭证。",
    "劫财": "劫财大运财路起伏，破财风险上升，切忌为他人担保或轻信高息投资；若能善加利用人脉资源，转危为机者有之。",
    "食神": "食神顺运，财源由才华与口碑自然流入，适合将专业技能变现；此运饮食享受旺，偏财机遇也常借贵人引荐而来。",
    "伤官": "伤官运财路灵活多变，适合创新创业与跨界投资，但情绪波动易导致冲动决策；宜以才艺换财、远离守旧行业。",
    "正财": "正财顺运，薪资晋升与稳健收益并进，适合加薪谈判、置业理财；此运财来有节有序，细水长流，不求暴利。",
    "偏财": "偏财大运财路宽广，偏门横财与投资机遇增多，但需以纪律约束冲动；广结人脉、借助贵人引荐，财运倍增。",
    "正官": "正官运名利双进，官方资源与职场晋升同步提升财运；薪酬稳步上升，不动产与稳健理财为首选，防官非纠纷。",
    "七杀": "七杀运竞争激烈，财运大起大落，宜以胆略与执行力应对；高风险投资需设止损，防财务官非；破局后回报丰厚。",
    "正印": "正印大运财运偏于保守稳健，适合积累知识资本，靠专业声誉间接生财；不宜冒进，精进技艺与证书可带来长远收益。",
    "偏印": "偏印运财路迂回，灵感与创造力是生财之源；避免依赖单一收入，发展副业或特殊技能，以多元化对冲财运波动。",
}

_TEN_GOD_HEALTH_HINT: dict[str, str] = {
    "比肩": "比肩运体力消耗大，竞争压力易引发肌肉骨骼劳损；注意劳逸结合，防过度运动造成运动损伤，肝气需疏泄。",
    "劫财": "劫财主耗泄，体力与免疫易受损；需防意外外伤与手术风险，饮食不规律需警惕脾胃功能下降。",
    "食神": "食神运饮食享受旺，需防过食肥甘、体重增加；脾胃功能活跃，适合养生调理，精神状态普遍好转。",
    "伤官": "伤官运神经系统敏感，焦虑与睡眠障碍风险上升；需防运动中急性损伤，保持情绪出口避免内耗积压。",
    "正财": "正财运身体稳健，但工作压力增加需防颈肩腰背劳损；规律作息、均衡饮食是本运健康基石。",
    "偏财": "偏财运奔波劳碌，交通出行频繁，防意外外伤与旅途疾病；肝气疏泄需到位，避免因情绪积压引发偏头痛。",
    "正官": "正官运压力较大，心脑血管与血压需重点关注；建立规律运动习惯，疏解职场压力，防止过劳诱发慢性病。",
    "七杀": "七杀运身体冲劲强但损伤风险高，防利刃外伤与高强度运动引发的急性损伤；情绪激烈时尤需保护心脏。",
    "正印": "正印运体质温和，脑力消耗大需防颈椎与眼睛疲劳；秋冬重点防肺部疾病，推荐冥想与舒缓运动养护神经。",
    "偏印": "偏印运睡眠质量不稳，多梦易醒；需警惕情绪内耗带来的免疫力下降，规律作息与户外活动有助改善。",
}

_TEN_GOD_LOVE_HINT: dict[str, str] = {
    "比肩": "比肩运独立意识强，不易示弱，感情中竞争心态需化解；同性朋友圈扩大，但与伴侣须注意主导权平衡。",
    "劫财": "劫财运感情波动较大，易有第三方介入或争执破财；交际圈广但感情浮动，婚姻中需主动沟通防止冷战升级。",
    "食神": "食神运魅力自然流露，感情生活温馨充实，桃花质量佳；已婚者宜共享美食与兴趣，增进伴侣间的亲密感。",
    "伤官": "伤官运感情刚烈，批判性强，易与伴侣产生言语摩擦；感情体验深刻但起伏大，宜学习包容性表达避免伤感情。",
    "正财": "正财运感情踏实，适合稳固现有关系或推进婚恋；男命正财代表妻星旺，女命感情多来自生活中的细水长流。",
    "偏财": "偏财运桃花活跃，异性缘旺，广交益友但需专一用情；社交场合邂逅良缘概率高，宜把握缘分主动深化关系。",
    "正官": "正官运感情趋于稳定正式，适合领证或明确关系；男命官运旺盛易受约束，女命正官为夫星，有缘定终身之象。",
    "七杀": "七杀运感情强烈且充满张力，激情与冲突并存；需防第三方介入与感情暴力，理性引导冲动可转化为深度羁绊。",
    "正印": "正印运感情内敛保守，母缘或长辈缘深厚；人际关系偏向精神层面交流，感情进展缓慢但基础牢固。",
    "偏印": "偏印运感情较为孤独敏感，艺术与精神共鸣是连接情感的纽带；防止独处过多导致感情疏远，主动表达情感为要。",
}

_TEN_GOD_CHILD_HINT: dict[str, str] = {
    "比肩": "此运子女独立性强，与兄弟姐妹或同龄人互动频繁；给予充足自主空间，引导竞争意识转化为合作共赢思维。",
    "劫财": "此运子女能量旺盛但冲动，需加强规则教育；注意子女交友圈与零花钱管理，防止受不良影响养成冒进习惯。",
    "食神": "此运子女聪明好学，兴趣广泛，饮食健康状态佳；鼓励其发展特长，才艺学习事半功倍，子女缘较为深厚。",
    "伤官": "此运子女个性突出，表现欲强，需注意情绪管理教育；内在创造力丰沛，给予表达空间而非过度约束，方大器晚成。",
    "正财": "此运子女踏实懂事，财商意识萌发较早；宜从小培养储蓄习惯与责任感，亲子关系稳健，教育回报明显。",
    "偏财": "此运子女活泼好动，社交能力强；引导其建立财务规划意识，防止大手大脚，鼓励创意与商业启蒙教育。",
    "正官": "此运子女上进守纪，学业表现稳定；给予明确规则与榜样示范，官学双旺格下子女晋升潜力大。",
    "七杀": "此运子女精力充沛、竞争性强，需引导冲动能量向体育或竞技方向转化；亲子关系需刚柔并济，防止对抗性沟通。",
    "正印": "此运子女学习力强，母子（女）缘深；鼓励阅读与文化熏陶，艺术与学术方向均有潜力，避免依赖心过强。",
    "偏印": "此运子女思维独特，直觉灵敏，兴趣偏冷门；尊重其个性，防止世俗化教育压制天赋，艺术或研究方向可重点培养。",
}

# ── 地支维度健康 hint（主键：地支）────────────────────────────────────────────
_BRANCH_HEALTH_HINT: dict[str, str] = {
    "子": "子水当令，肾脏与膀胱为重点关注部位，冬季尤需保暖防寒，睡眠深度关系肾气恢复效率。",
    "丑": "丑土寒湿，脾胃运化偏弱，需防湿邪困脾与关节风湿；饮食宜温热，避免生冷伤阳。",
    "寅": "寅木生发，肝胆功能活跃，春季情绪波动需关注；筋骨拉伸与有氧运动可疏肝助运。",
    "卯": "卯木司令，肝经当旺，双眼与筋膜需保养；防用眼过度，保持充足睡眠以养肝血。",
    "辰": "辰土湿重，脾胃与皮肤易受湿邪侵袭；祛湿饮食（薏仁、赤豆）与规律运动益处显著。",
    "巳": "巳火炎热，心脏与小肠需关注；防暑降温不可忽视，夏季注意补水与情绪平稳，防心火上炎。",
    "午": "午火最旺，心脑血管压力增大，血压与心率需定期监测；高温季节减少剧烈运动，清心降火为要。",
    "未": "未土燥热，脾胃功能失调风险上升；饮食清淡易消化，防止暑湿夹杂引发消化不良与皮肤疾患。",
    "申": "申金肃降，肺与大肠当令，呼吸道与皮肤需重点保养；秋季防风寒入侵，保持呼吸道湿润。",
    "酉": "酉金清凉，肺气收敛，需防咳嗽与皮肤干燥；秋天补充气阴，推荐百合、银耳等润肺食材。",
    "戌": "戌土燥烈，胃部与心包经需关注；防止过度焦虑引发胃溃疡，睡前放松练习有助缓解压力积累。",
    "亥": "亥水封藏，肾气内收，宜冬藏以固元气；防止熬夜耗损肾精，适度补益（枸杞、核桃）助肾气充盈。",
}


def _build_hints(
    stem: str,
    branch: str,
    day_stem: str,
) -> dict[str, str]:
    stem_elem, _ = STEM_ELEMENT.get(stem, ("?", "?"))
    # 以十神为主键，element 为备选
    ten_god = get_ten_god(day_stem, stem) if day_stem and day_stem != "?" else ""
    wealth_hint = (
        _TEN_GOD_WEALTH_HINT.get(ten_god)
        or _ELEM_WEALTH_HINT.get(stem_elem, "")
    )
    love_hint = (
        _TEN_GOD_LOVE_HINT.get(ten_god)
        or _ELEM_LOVE_HINT.get(stem_elem, "")
    )
    child_hint = (
        _TEN_GOD_CHILD_HINT.get(ten_god)
        or _ELEM_CHILD_HINT.get(stem_elem, "")
    )
    # 健康 hint：十神为主，再拼接地支脏腑补充
    tg_health = (
        _TEN_GOD_HEALTH_HINT.get(ten_god)
        or _ELEM_HEALTH_HINT.get(stem_elem, "")
    )
    branch_health = _BRANCH_HEALTH_HINT.get(branch, "")
    health_hint = f"{tg_health}　{branch_health}".strip() if branch_health else tg_health
    return {
        "wealth_hint": wealth_hint,
        "health_hint": health_hint,
        "love_hint": love_hint,
        "child_hint": child_hint,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────────────────────────────────────

def compute_dayun(
    birth_dt: datetime,           # 矫正后的出生时间（本地，UTC+8）
    year_stem: str,
    month_stem: str,
    month_branch: str,
    day_stem: str,
    gender: Optional[str] = None, # "male"/"female"/None
    count: int = 10,
    days_per_month: int = 3,
) -> dict:
    """
    计算大运列表.

    Returns dict 结构:
    {
        "direction": "forward" | "backward",
        "direction_basis": str,
        "start_age": int,           # 起运年龄（整岁）
        "start_age_months": int,    # 起运月数
        "anchor_jieqi_name": str,
        "anchor_jieqi_dt": str,
        "items": [
            {
                "start_age": int,   "start_year": int,
                "stem": str,        "branch": str,
                "ten_god": str,     "flow_wuxing": str,
                "wealth_hint": str, "health_hint": str,
                "love_hint": str,   "child_hint": str,
                "refs": list[dict],
            }, ...
        ]
    }
    """
    jie_ctx = get_jieqi_context(birth_dt)

    direction, direction_basis = _get_direction(year_stem, gender)

    if jie_ctx is None:
        return {
            "direction": direction,
            "direction_basis": direction_basis,
            "start_age": 0,
            "start_age_months": 0,
            "anchor_jieqi_name": None,
            "anchor_jieqi_dt": None,
            "items": [],
        }

    # ── P60 修复: 逆排用 prev_jie_dt，顺排用 next_jie_dt ──────────────────────
    if direction == "forward":
        anchor_dt = jie_ctx.next_jie_dt
        anchor_name = jie_ctx.next_jie_name
        delta_days = (anchor_dt - birth_dt).total_seconds() / 86400.0
    else:
        anchor_dt = jie_ctx.prev_jie_dt         # 修复: 旧代码此处错误用了 next_jie_dt
        anchor_name = jie_ctx.prev_jie_name
        delta_days = (birth_dt - anchor_dt).total_seconds() / 86400.0

    delta_days = max(delta_days, 0.0)
    start_age_months = ceil(delta_days / days_per_month)
    start_age = start_age_months // 12

    # ── 60甲子序列 ───────────────────────────────────────────────────────────
    start_idx = _ganzhi_index(month_stem, month_branch)
    step = 1 if direction == "forward" else -1
    items = []
    current_idx = (start_idx + step) % 60
    base_year = birth_dt.year + start_age

    # 大运通用引用（大运方向/用神类）
    dayun_refs = get_refs_by_tag("大运")[:2]

    for i in range(count):
        stem, branch = _ganzhi_from_index(current_idx)
        stem_elem, _ = STEM_ELEMENT.get(stem, ("?", "?"))
        ten_god = get_ten_god(day_stem, stem)
        hints = _build_hints(stem, branch, day_stem)

        # 本柱相关引用
        refs_hint = get_refs_by_tag(ten_god) if ten_god else []
        refs = (dayun_refs + refs_hint)[:3]   # 最多3条

        items.append({
            "start_age": start_age + i * 10,
            "start_year": base_year + i * 10,
            "start_age_months": start_age_months + i * 120,
            "stem": stem,
            "branch": branch,
            "ten_god": ten_god,
            "flow_wuxing": stem_elem,
            **hints,
            "refs": refs,
        })
        current_idx = (current_idx + step) % 60

    return {
        "direction": direction,
        "direction_basis": direction_basis,
        "start_age": start_age,
        "start_age_months": start_age_months,
        "anchor_jieqi_name": anchor_name,
        "anchor_jieqi_dt": anchor_dt.isoformat(),
        "items": items,
    }
