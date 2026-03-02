"""
services/bazi_engine/palace.py — 命宫、身宫、十二宫（M1 任务 1.11）

命宫（胎元宫）:
  起虎寅月，以寅月为正月（建寅），逆数到出生月，
  以出生时辰顺起，于寅月前/后依生时定宫支。

  公式（子平术）:
    命宫支 = (月支序号 + 时支序号 - 2) mod 12
    其中 寅=0, 卯=1, ...; 子时=0, 丑时=1, ...

  *注：不同流派略有差异；本实现采用主流子平寅起法*

身宫（年宫）:
  以年支为基础，依命宫法取身宫
  (年支序号 + 时支序号 - (寅月序号=2)) mod 12

  公式（各家不同；此处采用简化甲子法）:
    身宫支 = (年支序号 + 月支序号引起之冲) mod 12
  *简化实现: 身宫 = 年支对宫（六冲）的宫支*

十二宫（长生/沐浴/.../胎/养）:
  以日主五行的长生起点，按地支顺序排列12宫。

  长生起点（阳干顺/阴干逆）:
    甲/乙: 亥(长生阳)/午(长生阴)
    丙/戊: 寅(阳)/酉(阴)
    丁/己: 酉(阳)/寅(阴)
    庚/辛: 巳(阳)/子(阴)
    壬/癸: 申(阳)/卯(阴)

十二宫名: 长生/沐浴/冠带/临官(建禄)/帝旺/衰/病/死/墓/绝/胎/养
"""
from __future__ import annotations

from services.bazi_engine.tables import BRANCHES, STEM_ELEMENT

# ──────────────────────────────────────────────────────────────────────────────
# 命宫表（主流寅起法，寅月子时 = 命宫为寅）
# ──────────────────────────────────────────────────────────────────────────────

# 地支月份序（寅=1月，卯=2月...丑=12月）
_MONTH_BRANCH_IDX: dict[str, int] = {
    "寅": 1, "卯": 2, "辰": 3, "巳": 4, "午": 5, "未": 6,
    "申": 7, "酉": 8, "戌": 9, "亥": 10, "子": 11, "丑": 12,
}
# 时支序（子=0...亥=11）
_HOUR_BRANCH_IDX: dict[str, int] = {b: i for i, b in enumerate(BRANCHES)}

# 命宫公式（寅起顺布时辰）
# 《三命通会》: 寅月子时起寅，顺数时辰 → 子时+0, 丑时+1, ...
# 公式: branch_idx = (2 - (m-1) + h) % 12 = (3 - m + h) % 12
# 验证: 寅月(m=1)子时(h=0)→(3-1+0)%12=2→寅 ✓
#       卯月(m=2)子时(h=0)→(3-2+0)%12=1→丑 ✓
#       未月(m=6)午时(h=6)→(3-6+6)%12=3→卯 ✓
def _ming_gong_branch(month_branch: str, hour_branch: str) -> str:
    m = _MONTH_BRANCH_IDX.get(month_branch, 1)
    h = _HOUR_BRANCH_IDX.get(hour_branch, 0)
    # 顺布: 时支加，月份(寅起)减
    branch_idx = (3 - m + h) % 12
    return BRANCHES[branch_idx]


# ──────────────────────────────────────────────────────────────────────────────
# 十二长生宫
# ──────────────────────────────────────────────────────────────────────────────

TWELVE_PALACE_NAMES: list[str] = [
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰", "病", "死", "墓", "绝", "胎", "养",
]

# 阳干长生起点地支
_YANG_START: dict[str, str] = {
    "甲": "亥", "丙": "寅", "戊": "寅",
    "庚": "巳", "壬": "申",
}
# 阴干长生起点地支（逆行）
_YIN_START: dict[str, str] = {
    "乙": "午", "丁": "酉", "己": "酉",
    "辛": "子", "癸": "卯",
}


def compute_twelve_palaces(day_stem: str) -> dict[str, str]:
    """
    返回日主十二宫: {宫名: 地支}
    阳干顺行，阴干逆行.
    """
    _, yinyang = STEM_ELEMENT.get(day_stem, ("?", "yang"))
    is_yang = yinyang == "yang"

    if is_yang:
        start_branch = _YANG_START.get(day_stem)
    else:
        start_branch = _YIN_START.get(day_stem)

    if not start_branch:
        return {}

    start_idx = BRANCHES.index(start_branch)
    step = 1 if is_yang else -1

    result: dict[str, str] = {}
    for i, palace_name in enumerate(TWELVE_PALACE_NAMES):
        branch_idx = (start_idx + step * i) % 12
        result[palace_name] = BRANCHES[branch_idx]
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 身宫
# ──────────────────────────────────────────────────────────────────────────────

def _shen_gong_branch(year_branch: str, hour_branch: str) -> str:
    """
    身宫（以年支起）:
    身宫支 = (3 - 年支月序 + 时支序号) mod 12
    即与命宫法相同，但以年支替换月支（顺数时辰）。
    """
    y = _MONTH_BRANCH_IDX.get(year_branch, 1)  # 年支当月序
    h = _HOUR_BRANCH_IDX.get(hour_branch, 0)
    branch_idx = (3 - y + h) % 12
    return BRANCHES[branch_idx]


# ──────────────────────────────────────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────────────────────────────────────

def compute_palace(
    year_branch: str,
    month_branch: str,
    day_stem: str,
    day_branch: str,
    hour_branch: str,
) -> dict:
    """
    计算命宫、身宫、十二宫.

    Returns:
    {
        "ming_gong": str,                    # 命宫地支
        "shen_gong": str,                    # 身宫地支
        "day_palace": str,                   # 日主当前宫（在十二宫中的宫名）
        "twelve_palaces": dict[str, str],    # {宫名: 地支}（以日主为准）
        "day_branch_palace": str,            # 日支在十二宫中的宫名（日主强弱参考）
    }
    """
    ming_gong = _ming_gong_branch(month_branch, hour_branch)
    shen_gong = _shen_gong_branch(year_branch, hour_branch)
    twelve = compute_twelve_palaces(day_stem)

    # 日支在十二宫中的位置
    day_branch_palace = next(
        (name for name, br in twelve.items() if br == day_branch),
        "未知"
    )

    return {
        "ming_gong": ming_gong,
        "shen_gong": shen_gong,
        "day_palace": day_branch_palace,
        "twelve_palaces": twelve,
        "day_branch_palace": day_branch_palace,
    }
