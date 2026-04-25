"""
services/ziwei_engine/decorative.py — 长生十二神 / 将前十二神 / 岁前十二神

参照 iztro decorativeStar.ts 实现。

三套十二神：
  changsheng12  — 长生十二神（本命固定星）：起点依五行局，方向依性别×年支阴阳
  jiangqian12   — 将前十二神（流年星）：起点依流年年支三合组，顺行
  suiqian12     — 岁前十二神（流年星）：起点 = 流年年支，顺行
"""
from __future__ import annotations

# ── 星名序列 ───────────────────────────────────────────────────────────────────

CHANGSHENG_12: list[str] = [
    "长生", "沐浴", "冠带", "临官", "帝旺", "衰",
    "病",   "死",   "墓",   "绝",   "胎",   "养",
]

JIANGQIAN_12: list[str] = [
    "将星", "攀鞍", "岁驿", "息神", "华盖", "劫煞",
    "灾煞", "天煞", "指背", "咸池", "月煞", "亡神",
]

SUIQIAN_12: list[str] = [
    "岁建", "晦气", "丧门", "贯索", "官符", "小耗",
    "大耗", "龙德", "白虎", "天德", "吊客", "病符",
]

# ── 长生12神起始地支（五行局 → 地支索引，子=0）────────────────────────────────
# 五行长生标准位：水→申, 木→亥, 金→巳, 土→申, 火→寅
_CHANGSHENG_START: dict[int, int] = {
    2: 8,   # 水二局 → 申(8)
    3: 11,  # 木三局 → 亥(11)
    4: 5,   # 金四局 → 巳(5)
    5: 8,   # 土五局 → 申(8)  土与水同长生
    6: 2,   # 火六局 → 寅(2)
}

# ── 将前12神起始地支（流年年支三合 → 起始地支）──────────────────────────────────
_JIANGQIAN_START_MAP: list[tuple[frozenset[int], int]] = [
    (frozenset([2, 6, 10]),  6),   # 寅午戌 → 午(6)
    (frozenset([8, 0, 4]),   0),   # 申子辰 → 子(0)
    (frozenset([5, 9, 1]),   9),   # 巳酉丑 → 酉(9)
    (frozenset([11, 3, 7]),  3),   # 亥卯未 → 卯(3)
]


def place_changsheng12(
    wuxing_ju: int,
    gender: str,
    year_branch_idx: int,
    changsheng_method: str = "standard",
) -> dict[int, str]:
    """
    布置长生十二神（本命命盘固定星）。

    参数：
        wuxing_ju         五行局（2=水二, 3=木三, 4=金四, 5=土五, 6=火六）
        gender            "男"/"女"
        year_branch_idx   出生年地支索引（子=0…亥=11）
        changsheng_method 安法流派：
            "standard"    区分阴阳顺逆（默认，全书法）
            "water_earth" 水土共长生：土五局仅依性别顺逆，不区分年支阴阳
            "fire_earth"  火土共长生：土五局起点改为寅(2)，与火六局同

    返回 {branch_idx: star_name}，恰好12个宫各对应1颗。

    顺逆规则：
      阳男阴女 → 顺行（地支递增，code forward=True）
      阴男阳女 → 逆行（地支递减，code forward=False）
    water_earth 特殊规则：
      土五局只看性别，男=顺行(递增)，女=逆行(递减)
    """
    start = _CHANGSHENG_START.get(wuxing_ju, 8)

    if changsheng_method == "fire_earth" and wuxing_ju == 5:
        # fire_earth 方式（覆盖为寅=2）
        start = 2

    year_yang = (year_branch_idx % 2 == 0)
    gender_yang = gender.upper() in ("M", "男", "MALE")

    if changsheng_method == "water_earth" and wuxing_ju == 5:
        # 水土共长生：土五局强制按性别（男=顺行=递增，女=逆行=递减）
        forward = gender_yang
    else:
        # 阳男阴女顺行(forward=True)，阴男阳女逆行(forward=False)
        forward = (gender_yang == year_yang)

    result: dict[int, str] = {}
    for i, star in enumerate(CHANGSHENG_12):
        idx = (start + i) % 12 if forward else (start - i) % 12
        result[idx] = star
    return result


def place_jiangqian12(liunian_branch_idx: int) -> dict[int, str]:
    """
    布置将前十二神（流年星）。

    起始宫由流年年支所在三合组决定，顺行12宫。
    返回 {branch_idx: star_name}
    """
    start = 6  # 默认午
    for branches, s in _JIANGQIAN_START_MAP:
        if liunian_branch_idx in branches:
            start = s
            break

    return {(start + i) % 12: star for i, star in enumerate(JIANGQIAN_12)}


def place_suiqian12(liunian_branch_idx: int) -> dict[int, str]:
    """
    布置岁前十二神（流年星）。

    起点 = 流年年支宫位，顺行12宫。
    返回 {branch_idx: star_name}
    """
    return {(liunian_branch_idx + i) % 12: star for i, star in enumerate(SUIQIAN_12)}
