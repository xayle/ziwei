"""
services/bazi_engine/milestones.py — 人生里程碑引擎 (M2.5 任务 2.56)

识别关键年份：犯太岁、岁运并临、大运交接、社会节点。
"""

from __future__ import annotations

import datetime

from app.schemas.analysis import MilestoneModel

# 地支六冲
_BRANCH_CHONG: dict[str, str] = {
    "子": "午",
    "午": "子",
    "丑": "未",
    "未": "丑",
    "寅": "申",
    "申": "寅",
    "卯": "酉",
    "酉": "卯",
    "辰": "戌",
    "戌": "辰",
    "巳": "亥",
    "亥": "巳",
}

# 地支六刑（三刑/自刑简化）
_BRANCH_XING: dict[str, set[str]] = {
    "寅": {"巳", "申"},
    "巳": {"寅", "申"},
    "申": {"寅", "巳"},
    "丑": {"戌", "未"},
    "戌": {"丑", "未"},
    "未": {"丑", "戌"},
    "子": {"卯"},
    "卯": {"子"},
    "辰": {"辰"},
    "午": {"午"},
    "酉": {"酉"},
    "亥": {"亥"},  # 自刑
}

# 大运交接标准社会节点
_SOCIAL_CHECKPOINTS: dict[int, str] = {
    18: "高考/升学节点",
    22: "毕业就业节点",
    25: "职业第一次跃升",
    28: "婚育节点",
    30: "三十而立，事业关键期",
    35: "中年晋升窗口",
    40: "不惑，转型与守成",
    45: "企业中坚，家庭责任高峰",
    50: "五十知天命，财富与健康转折",
    60: "花甲，退休与传承节点",
}


def compute_milestones(
    birth_year: int,
    day_branch: str,
    year_branch: str,  # 出生年支（用于太岁冲克）
    dayun_list: list[dict],  # 大运列表（含start_age/end_age/ganzhi/branch）
    liunian_list: list[dict],  # 流年列表（含year/ganzhi/branch）
    yongshen_favor: list[str],
    yongshen_avoid: list[str],
    current_year: int | None = None,
) -> list[MilestoneModel]:
    """
    生成人生里程碑列表（不超过15条，按年龄/年份排序）。
    """
    if current_year is None:
        current_year = datetime.date.today().year

    milestones: list[MilestoneModel] = []
    seen_years: set[int] = set()

    def add(age: int, year: int, mtype: str, context: str, desc: str, risk: str, advice: str) -> None:
        if year in seen_years:
            return
        seen_years.add(year)
        milestones.append(
            MilestoneModel(
                age=age,
                year=year,
                milestone_type=mtype,  # type: ignore[arg-type]
                ganzhi_context=context,
                description=desc,
                risk_level=risk,  # type: ignore[arg-type]
                advice=advice,
            )
        )

    # ─── 1. 犯太岁（流年地支=出生年支，或相冲） ──────────────────────────
    for lny in liunian_list:
        ly_branch = lny.get("branch", "")
        ly_year = lny.get("year", 0)
        ly_gz = lny.get("ganzhi", "")
        age = ly_year - birth_year
        if 0 < age < 100:
            if ly_branch == year_branch:
                add(
                    age,
                    ly_year,
                    "犯太岁",
                    ly_gz,
                    f"流年{ly_gz}与出生年支{year_branch}相同，犯本命太岁。",
                    "高",
                    "本命年宜低调行事，避免大动作决策；可佩戴化解吉祥物。",
                )
            elif _BRANCH_CHONG.get(ly_branch) == year_branch:
                add(
                    age,
                    ly_year,
                    "犯太岁",
                    ly_gz,
                    f"流年{ly_gz}冲本命年支{year_branch}，犯冲太岁。",
                    "中",
                    "此年注意健康及变动，谨慎行事，可增加化煞布置。",
                )

    # ─── 2. 大运交接（每10年节点 ± 1年） ────────────────────────────────
    for dyun in dayun_list:
        start_age = dyun.get("start_age", 0)
        dy_gz = dyun.get("ganzhi", "")
        change_year = birth_year + start_age
        if 0 < start_age < 100:
            add(
                start_age,
                change_year,
                "大运交接",
                dy_gz,
                f"进入{dy_gz}大运，命运方向发生转变。",
                "中",
                "大运交接3年内宜审时度势，积极迎接新方向带来的机遇与挑战。",
            )

    # ─── 3. 岁运并临（流年与大运干支相同/相生） ──────────────────────────
    for lny in liunian_list:
        ly_branch = lny.get("branch", "")
        ly_stem = lny.get("stem", "")
        ly_year = lny.get("year", 0)
        ly_gz = lny.get("ganzhi", "")
        age = ly_year - birth_year
        # 对应大运
        dy_gz_match = None
        for dyun in dayun_list:
            s, e = dyun.get("start_age", 0), dyun.get("end_age", 0)
            if s <= age <= e:
                dy_gz_match = dyun.get("ganzhi", "")
                break
        if dy_gz_match and ly_gz and 0 < age < 100:
            # 简化：流年干/支出现在大运干支中 → 岁运并临
            if ly_stem and ly_stem in dy_gz_match:
                add(
                    age,
                    ly_year,
                    "岁运并临",
                    f"流年{ly_gz}×大运{dy_gz_match}",
                    f"流年天干{ly_stem}与大运相同，岁运并临，力量加倍。",
                    "中",
                    "此年运势放大，宜把握机遇；若为忌神则需特别防范风险。",
                )

    # ─── 4. 社会节点 ─────────────────────────────────────────────────────
    for age, desc in _SOCIAL_CHECKPOINTS.items():
        yr = birth_year + age
        if yr not in seen_years and 0 < age < 100:
            add(age, yr, "社会节点", f"虚岁{age}岁", desc, "低", "社会普遍节点，结合个人大运判断最佳决策时机。")

    # 排序 & 限制数量
    milestones.sort(key=lambda m: m.year)
    return milestones[:15]
