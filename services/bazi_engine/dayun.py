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


def _build_hints(
    stem: str,
    branch: str,
    day_stem: str,
) -> dict[str, str]:
    stem_elem, _ = STEM_ELEMENT.get(stem, ("?", "?"))
    return {
        "wealth_hint": _ELEM_WEALTH_HINT.get(stem_elem, ""),
        "health_hint": _ELEM_HEALTH_HINT.get(stem_elem, ""),
        "love_hint": _ELEM_LOVE_HINT.get(stem_elem, ""),
        "child_hint": _ELEM_CHILD_HINT.get(stem_elem, ""),
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
