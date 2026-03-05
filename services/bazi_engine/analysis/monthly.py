"""
services/bazi_engine/analysis/monthly.py — 月运引擎 (M2 任务 2.07)

算法规格: §4.11-G
"""
from __future__ import annotations

from app.schemas.analysis import MonthlyFortuneModel

# 月份→月支（阴历月，1月=寅）
_MONTH_BRANCH: list[str] = [
    "寅", "卯", "辰", "巳", "午", "未",
    "申", "酉", "戌", "亥", "子", "丑",
]

# 地支六冲
_BRANCH_CHONG: dict[str, str] = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}

# 地支三刑（部分关键）
_BRANCH_XING: dict[str, set[str]] = {
    "寅": {"寅", "巳"},  # 寅巳申三刑（无恩之刑）
    "巳": {"巳", "申"},
    "申": {"申", "寅"},
    "丑": {"丑", "戌"},  # 丑戌未三刑（持势之刑）
    "戌": {"戌", "未"},
    "未": {"未", "丑"},
    "子": {"子", "卯"},  # 子卯刑
    "卯": {"卯", "子"},
    "辰": {"辰"},        # 辰午酉亥自刑（partial）
    "午": {"午"},
    "酉": {"酉"},
    "亥": {"亥"},
}

# 地支六合
_BRANCH_HE: dict[str, str] = {
    "子": "丑", "丑": "子",
    "寅": "亥", "亥": "寅",
    "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰",
    "巳": "申", "申": "巳",
    "午": "未", "未": "午",
}

# 地支五行
_BRANCH_ELEMENT: dict[str, str] = {
    "子": "water", "亥": "water",
    "寅": "wood",  "卯": "wood",
    "巳": "fire",  "午": "fire",
    "申": "metal", "酉": "metal",
    "丑": "earth", "辰": "earth", "未": "earth", "戌": "earth",
}

# 相生
_SHENG: dict[str, str] = {
    "wood": "fire", "fire": "earth", "earth": "metal",
    "metal": "water", "water": "wood",
}

# 相克
_KE: dict[str, str] = {
    "wood": "earth", "earth": "water", "water": "fire",
    "fire": "metal", "metal": "wood",
}

# 五行中文
_ELEMENT_CN: dict[str, str] = {
    "metal": "金", "wood": "木", "water": "水", "fire": "火", "earth": "土",
}

# lucky_color hint — CSS 十六进制（按吉凶等级，规格 P0-15）
_LUCK_COLOR: dict[str, str] = {
    "吉": "#2E8B57",
    "平": "#888888",
    "凶": "#C0392B",
}


def compute_monthly(
    day_branch: str,               # 日支
    yongshen_favor: list[str],     # 用神五行（英文）
    yongshen_avoid: list[str],     # 忌神五行（英文）
    year_branch: str = "",         # 流年地支（可选）
    mode: str = "dual",            # "dual" | "single"
    month_ganzhis: list[str] | None = None,  # 12个月干支，如["甲寅","乙卯",...]
    current_dayun_stem: str | None = None,   # 当前大运天干
    day_stem: str | None = None,             # 日主天干，用于计算十神关系（N2.03）
) -> list[MonthlyFortuneModel]:
    """
    §4.11-G 月运引擎

    Parameters:
        day_branch:         日支（配偶宫同时是月运基准）
        yongshen_favor:     用神五行列表
        yongshen_avoid:     忌神五行列表
        year_branch:        流年干支中的地支
        mode:               "dual"=双身份完整推算; "single"=全部降级为"平"
        month_ganzhis:      长度12的月干支列表，如["甲寅","乙卯",...]；None则不填充
        current_dayun_stem: 当前大运天干，如"甲"；None则不填充
        day_stem:           日主天干，用于计算月干对日主十神关系（N2.03）

    Returns:
        list[MonthlyFortuneModel] — 长度恰好 12
    """
    from services.bazi_engine.tables import get_ten_god as _gtg
    results: list[MonthlyFortuneModel] = []

    for month_idx in range(12):
        # 节气偏移：寅月（正月）从立春（约2月4日）起，故1月对应丑月（上一周期末）
        # month_idx=0(Jan)→丑(11), month_idx=1(Feb)→寅(0), ..., month_idx=11(Dec)→子(10)
        _chi_idx = (month_idx - 1) % 12
        mb = _MONTH_BRANCH[_chi_idx]
        month_num = month_idx + 1

        # 十神关系：该月天干对日主天干的十神
        _mgz = month_ganzhis[_chi_idx] if month_ganzhis else None
        _month_stem = _mgz[0] if _mgz and len(_mgz) >= 1 else ""
        _relation = None
        if day_stem and _month_stem:
            try:
                _relation = _gtg(day_stem, _month_stem)
            except Exception:
                _relation = None

        if mode == "single":
            # 单用户模式：全部降级为"平"
            results.append(MonthlyFortuneModel(
                month=month_num,
                month_dizhi=mb,
                luck_level="平",
                color_hint=_LUCK_COLOR["平"],
                tip="本月平稳，顺势而为。",
                clash_with=None,
                month_ganzhi=_mgz,
                dayun_stem=current_dayun_stem,
                relation_to_rizhu=_relation,
            ))
            continue

        # ── dual 模式 ── 完整推算 ──────────────────────────────────────
        luck_level = "平"
        tip = ""
        clash_with: str | None = None

        mb_element = _BRANCH_ELEMENT.get(mb, "")

        # 1. 月支冲日支 → 凶
        if _BRANCH_CHONG.get(mb) == day_branch:
            luck_level = "凶"
            clash_with = day_branch
            tip = f"本月{mb}冲{day_branch}，注意人际与健康摩擦，低调行事。"

        # 2. 月支与用神五行同气/生 → 吉
        elif mb_element and yongshen_favor and (
            mb_element in yongshen_favor
            or _SHENG.get(mb_element) in yongshen_favor
        ):
            luck_level = "吉"
            el_cn = _ELEMENT_CN.get(mb_element, mb_element)
            tip = f"本月{mb}（{el_cn}）有助用神，财运/事业有正向进展。"

        # 3. 月支与忌神相克 → 凶
        elif mb_element and yongshen_avoid and (
            mb_element in yongshen_avoid
            or _KE.get(mb_element) in yongshen_avoid
        ):
            luck_level = "凶"
            tip = f"本月{mb}触动忌神，需谨慎决策，避免冲动行事。"

        # 4. 三刑 → 凶
        elif day_branch in _BRANCH_XING.get(mb, set()):
            luck_level = "凶"
            tip = f"本月{mb}与日支{day_branch}存在三刑，健康与人际需注意。"

        # 5. 其余 → 平
        else:
            luck_level = "平"
            if year_branch and _BRANCH_HE.get(mb) == year_branch:
                tip = f"本月与流年地支{year_branch}六合，整体较为顺遂。"
            else:
                tip = f"本月{mb}平稳，正常作息，稳步推进计划。"

        # color_hint — 根据 luck_level 返回 CSS 十六进制颜色（P0-15）
        color_hint = _LUCK_COLOR.get(luck_level, "#888888")

        results.append(MonthlyFortuneModel(
            month=month_num,
            month_dizhi=mb,
            luck_level=luck_level,
            color_hint=color_hint,
            tip=tip,
            clash_with=clash_with,
            month_ganzhi=_mgz,
            dayun_stem=current_dayun_stem,
            relation_to_rizhu=_relation,
        ))

    return results
