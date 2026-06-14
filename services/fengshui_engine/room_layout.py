"""
services/fengshui_engine/room_layout.py — v8.8.0 风水房间布局评估

基于八宅法命卦，对用户提供的九宫格房间布局方案进行吉凶评估：
  · 每个方位（N/NE/E/SE/S/SW/W/NW）可分配一个房间类型
  · 根据吉凶标签（生气/天医/延年/伏位/绝命/五鬼/六煞/祸害）评估匹配度
  · 返回单区分数、整体评分、等级与改善建议

免责声明：本模块仅供参考，不构成专业风水建议。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .bagua import calc_bagua

# ─────────────────────────────────────────────────────────────
# 房间类型定义
# ─────────────────────────────────────────────────────────────

ROOM_TYPE_ZH: dict[str, str] = {
    "empty": "不设置",
    "master_bedroom": "主卧",
    "bedroom": "次卧",
    "study": "书房",
    "child_room": "儿童房",
    "living_room": "客厅",
    "entrance": "玄关/入口",
    "dining_room": "餐厅",
    "kitchen": "厨房",
    "bathroom": "卫生间",
    "storage": "储藏室/杂物间",
}

# 吉方标签集
_AUSPICIOUS_LABELS = {"生气", "天医", "延年", "伏位"}
_TOP_AUSPICIOUS = {"生气", "天医", "延年"}
_SEVERE_BAD = {"绝命", "五鬼"}
_MILD_BAD = {"六煞", "祸害"}

# 每种房间类型的评分规则
# best_labels: 首选吉标签 → excellent (100)
# ok_labels:   次选标签   → good (75)
# needs_good:  True = 应放于吉方；False = 中性
# neutralizes: True = 应放于凶方（化煞）
_ROOM_RULES: dict[str, dict] = {
    "empty": {"skip": True},
    "master_bedroom": {
        "needs_good": True,
        "best_labels": {"生气", "天医", "延年"},
        "ok_labels": {"伏位"},
    },
    "bedroom": {
        "needs_good": True,
        "best_labels": {"天医", "延年", "生气"},
        "ok_labels": {"伏位"},
    },
    "study": {
        "needs_good": True,
        "best_labels": {"天医", "生气"},
        "ok_labels": {"延年", "伏位"},
    },
    "child_room": {
        "needs_good": True,
        "best_labels": {"生气", "天医"},
        "ok_labels": {"延年"},
    },
    "living_room": {
        "needs_good": True,
        "best_labels": {"生气", "延年"},
        "ok_labels": {"天医", "伏位"},
    },
    "entrance": {
        "needs_good": True,
        "best_labels": {"生气", "延年"},
        "ok_labels": {"天医"},
    },
    "dining_room": {
        "needs_good": False,
        "best_labels": {"天医", "伏位"},
        "ok_labels": {"生气", "延年"},
    },
    "kitchen": {
        "neutralizes": True,  # 炉火克凶，放于凶方为宜
        "needs_good": False,
    },
    "bathroom": {
        "neutralizes": True,  # 水+排水克凶
        "needs_good": False,
    },
    "storage": {
        "neutralizes": True,
        "needs_good": False,
    },
}


# ─────────────────────────────────────────────────────────────
# 单区评估
# ─────────────────────────────────────────────────────────────


@dataclass
class ZoneAssessment:
    direction: str
    direction_zh: str
    label: str  # 风水标签（生气/天医/…/绝命）
    level_css: str  # 吉凶样式（ji1~ji4, xiong1~xiong4）
    room_type: str  # 房间类型英文
    room_zh: str  # 房间类型中文
    assess_level: str  # excellent / good / ok / caution / warning / skip
    assess_score: int  # 0~100
    assess_note: str  # 评估说明


def _assess_zone(
    direction: str,
    direction_zh: str,
    label: str,
    level_css: str,
    room_type: str,
) -> ZoneAssessment:
    """对单个方位的房间分配进行评估。"""
    room_zh = ROOM_TYPE_ZH.get(room_type, room_type)
    rules = _ROOM_RULES.get(room_type, {})

    if rules.get("skip"):
        return ZoneAssessment(
            direction=direction,
            direction_zh=direction_zh,
            label=label,
            level_css=level_css,
            room_type=room_type,
            room_zh=room_zh,
            assess_level="skip",
            assess_score=0,
            assess_note="",
        )

    is_auspicious = label in _AUSPICIOUS_LABELS

    if rules.get("neutralizes"):
        # 化煞房间（厨/卫/储）
        if not is_auspicious:
            note = f"{room_zh}置于「{label}」方（凶方），炉火/排水可化解煞气，符合八宅原则。"
            score, level = 90, "excellent"
        elif label == "伏位":
            note = f"{room_zh}置于「{label}」方，略浪费吉气，可考虑与凶方房间互换。"
            score, level = 55, "ok"
        else:
            note = f"{room_zh}置于「{label}」吉方，占用了旺气，建议与凶方房间对调。"
            score, level = 35, "caution"
        return ZoneAssessment(
            direction=direction,
            direction_zh=direction_zh,
            label=label,
            level_css=level_css,
            room_type=room_type,
            room_zh=room_zh,
            assess_level=level,
            assess_score=score,
            assess_note=note,
        )

    best = rules.get("best_labels", set())
    ok = rules.get("ok_labels", set())

    if label in best:
        note = f"{room_zh}置于「{label}」方，与命卦最为相合，能量加持最佳。"
        score, level = 100, "excellent"
    elif label in ok:
        note = f"{room_zh}置于「{label}」方，方位适合，效果尚佳。"
        score, level = 75, "good"
    elif is_auspicious:
        note = f"{room_zh}置于「{label}」方，勉强可用，非最优选择。"
        score, level = 55, "ok"
    elif label in _MILD_BAD:
        note = f"{room_zh}置于「{label}」凶方，有一定不利影响，建议调整至吉方。"
        score, level = 30, "caution"
    elif label == "五鬼":
        note = f"{room_zh}置于「{label}」方，影响较重，强烈建议调整。"
        score, level = 15, "warning"
    else:  # 绝命
        note = f"{room_zh}置于「{label}」方，为最凶位，应尽快调整至吉方。"
        score, level = 5, "warning"

    return ZoneAssessment(
        direction=direction,
        direction_zh=direction_zh,
        label=label,
        level_css=level_css,
        room_type=room_type,
        room_zh=room_zh,
        assess_level=level,
        assess_score=score,
        assess_note=note,
    )


# ─────────────────────────────────────────────────────────────
# 整体评估
# ─────────────────────────────────────────────────────────────


@dataclass
class RoomLayoutResult:
    life_gua: int
    gua_name: str
    score: int  # 0~100 加权平均
    grade: str  # 优秀/良好/一般/较差/待改善
    grade_css: str  # excellent/good/ok/caution/warning
    cells: list[ZoneAssessment] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    disclaimer: str = ""


# 各房间类型的评估权重（主卧权重最高）
_WEIGHT: dict[str, int] = {
    "master_bedroom": 5,
    "bedroom": 4,
    "study": 3,
    "child_room": 4,
    "living_room": 3,
    "entrance": 2,
    "dining_room": 2,
    "kitchen": 2,
    "bathroom": 2,
    "storage": 1,
    "empty": 0,
}


def assess_room_layout(
    birth_year: int,
    gender: str,
    rooms: dict[str, str],  # direction → room_type
    house_facing: str | None = None,
) -> RoomLayoutResult:
    """
    对用户提交的房间布局进行完整评估。

    参数
    ----
    birth_year   : 出生公历年份
    gender       : "男" 或 "女"
    rooms        : 方位→房间类型映射，如 {"N": "kitchen", "E": "master_bedroom"}
    house_facing : 可选，房屋朝向（仅影响相合备注）
    """
    bagua = calc_bagua(birth_year=birth_year, gender=gender, house_facing=house_facing)

    # 构建方位→吉凶信息映射
    dir_info: dict[str, tuple[str, str]] = {}  # direction → (label, level_css)
    for item in bagua.auspicious + bagua.inauspicious:
        dir_info[item.direction] = (item.label, item.level_css)

    from .bagua import DIRECTIONS_ZH

    cells: list[ZoneAssessment] = []
    total_score = 0
    total_weight = 0
    suggestions: list[str] = []

    for direction, room_type in rooms.items():
        if direction not in dir_info:
            continue
        label, level_css = dir_info[direction]
        direction_zh = DIRECTIONS_ZH.get(direction, direction)
        cell = _assess_zone(direction, direction_zh, label, level_css, room_type)
        cells.append(cell)

        w = _WEIGHT.get(room_type, 1)
        if room_type != "empty":
            total_score += cell.assess_score * w
            total_weight += w

    # 整体评分
    score = round(total_score / total_weight) if total_weight else 0

    # 等级
    if score >= 90:
        grade, grade_css = "优秀", "excellent"
    elif score >= 75:
        grade, grade_css = "良好", "good"
    elif score >= 55:
        grade, grade_css = "一般", "ok"
    elif score >= 35:
        grade, grade_css = "较差", "caution"
    else:
        grade, grade_css = "待改善", "warning"

    # 自动建议：找出评分低的有意义房间
    bad_cells = [c for c in cells if c.assess_level in ("caution", "warning") and c.room_type != "empty"]
    for c in sorted(bad_cells, key=lambda x: x.assess_score):
        # 找到该房间最适合的方位（本命卦中未被占用的最佳吉方）
        best_label_for_room = next(iter(_ROOM_RULES.get(c.room_type, {}).get("best_labels", set()) or {"生气"}), "生气")
        best_dir = next(
            (
                d
                for item in bagua.auspicious
                if item.label == best_label_for_room
                for d in [item.direction]
                if d not in rooms or rooms[d] in ("empty", "")
            ),
            None,
        )
        hint = f"建议将「{c.room_zh}」从 {c.direction_zh} ({c.label}) 方调整至{best_dir + '方（' + best_label_for_room + '）' if best_dir else '吉方'}，可提升居住品质。"
        suggestions.append(hint)

    if not suggestions and score >= 75:
        suggestions.append("当前布局与命卦基本相合，整体方位选择合理。")

    disclaimer = (
        "以上评估仅供参考，依据八宅明镜派风水原则。"
        "实际居住布局受多种因素影响，如需专业指导请咨询风水师。"
        "涉及结构改动请务必咨询专业建筑人士。"
    )

    return RoomLayoutResult(
        life_gua=bagua.life_gua,
        gua_name=bagua.gua_name,
        score=score,
        grade=grade,
        grade_css=grade_css,
        cells=cells,
        suggestions=suggestions,
        disclaimer=disclaimer,
    )
