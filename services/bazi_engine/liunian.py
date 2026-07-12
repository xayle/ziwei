"""
services/bazi_engine/liunian.py — 流年排盘（M1 任务 1.08）

功能:
  - 给定大运柱（stem/branch）及起止年份, 枚举每个流年的干支、十神
  - 计算流年与命局的六大关系（值太岁/冲太岁/刑/害/破/合太岁）
  - 返回标准化 dict 列表，可直接填充 LiuNianItemModel

犯太岁关系判断顺序（优先级高→低）:
  1. 值太岁  (流年支 = 命局日支)
  2. 冲太岁  (流年支与日支 BRANCH_CHONG)
  3. 刑太岁  (流年支与日支 SAN_XING)
  4. 害太岁  (六害 LIU_HAI)
  5. 破太岁  (六破 LIU_PO)
  6. 合太岁  (六合 LIU_HE)
  7. None   (无特殊关系)
"""

from __future__ import annotations

from services.bazi_engine.shensha import compute_flow_shensha_items
from services.bazi_engine.tables import (
    BRANCH_CHONG,
    BRANCH_HIDDEN_STEMS,
    BRANCHES,
    LIU_HE,
    NAYIN,
    STEM_ELEMENT,
    STEMS,
    get_kongwang,
    get_ten_god,
)

_ELEM_CN: dict[str, str] = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
_PILLAR_NAMES = ("year", "month", "day", "hour")


def overlay_palace_map(
    year_branch: str,
    month_branch: str,
    day_branch: str,
    hour_branch: str,
    flow_branch: str,
) -> dict[str, str]:
    """
    叠宫映射：流年/流月地支 → 对应本命柱位（B-05 / 叠宫引擎）。

    Returns:
        {flow_branch: pillar_name} 及反向 {pillar_name: flow_branch}
    """
    pm = {
        "year": year_branch,
        "month": month_branch,
        "day": day_branch,
        "hour": hour_branch,
    }
    result: dict[str, str] = {}
    for pname, br in pm.items():
        result[pname] = flow_branch if br == flow_branch else ""
        if br == flow_branch:
            result[flow_branch] = pname
    if flow_branch not in result:
        result[flow_branch] = "none"
    return result


def _liunian_yongshen_shift(stem_elem: str, yongshen_favor: list[str], yongshen_avoid: list[str]) -> str:
    if not yongshen_favor:
        return "neutral"
    if stem_elem in yongshen_favor:
        return "forward"
    if stem_elem in yongshen_avoid:
        return "backward"
    return "neutral"


# ──────────────────────────────────────────────────────────────────────────────
# 刑、害、破 — 补充关系表
# ──────────────────────────────────────────────────────────────────────────────

# 六害: branch → 与其相害的branch
LIU_HAI: dict[str, str] = {
    "子": "未",
    "未": "子",
    "丑": "午",
    "午": "丑",
    "寅": "巳",
    "巳": "寅",
    "卯": "辰",
    "辰": "卯",
    "申": "亥",
    "亥": "申",
    "酉": "戌",
    "戌": "酉",
}

# 六破: branch → 与其相破的branch
LIU_PO: dict[str, str] = {
    "子": "酉",
    "酉": "子",
    "丑": "辰",
    "辰": "丑",
    "寅": "亥",
    "亥": "寅",
    "卯": "午",
    "午": "卯",
    "巳": "申",
    "申": "巳",
    "未": "戌",
    "戌": "未",
}

# 三刑: branch → set(与其相刑的branch)
SAN_XING: dict[str, set[str]] = {
    "寅": {"申", "巳"},  # 寅刑申(无礼之刑)部分; 实际寅申巳三刑
    "巳": {"申", "寅"},
    "申": {"寅", "巳"},
    "丑": {"戌", "未"},  # 丑戌未三刑
    "戌": {"丑", "未"},
    "未": {"丑", "戌"},
    "子": {"卯"},  # 子卯相刑（无礼之刑）
    "卯": {"子"},
    "辰": {"辰"},  # 辰午酉亥自刑
    "午": {"午"},
    "酉": {"酉"},
    "亥": {"亥"},
}

_STAGE_NAMES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
_STAGE_START: dict[str, str] = {
    "甲": "亥",
    "乙": "午",
    "丙": "寅",
    "丁": "酉",
    "戊": "寅",
    "己": "酉",
    "庚": "巳",
    "辛": "子",
    "壬": "申",
    "癸": "卯",
}


# ──────────────────────────────────────────────────────────────────────────────
# 干支工具
# ──────────────────────────────────────────────────────────────────────────────


def _ganzhi_of_year(year: int) -> tuple[str, str]:
    """给定公历年份返回干支 (甲子=1984年为基准)"""
    # 1984年=甲子年 → (0, 0) in STEMS/BRANCHES
    base = 1924  # 甲子年(0号)在公历的基准年
    idx = (year - base) % 60
    return STEMS[idx % 10], BRANCHES[idx % 12]


# ──────────────────────────────────────────────────────────────────────────────
# 流年与日柱关系
# ──────────────────────────────────────────────────────────────────────────────


def _liunian_day_relation(liunian_branch: str, day_branch: str) -> str | None:
    """判断流年支与日支的犯太岁关系"""
    if liunian_branch == day_branch:
        return "值太岁"
    if BRANCH_CHONG.get(liunian_branch) == day_branch:
        return "冲太岁"
    if day_branch in SAN_XING.get(liunian_branch, set()):
        return "刑太岁"
    if LIU_HAI.get(liunian_branch) == day_branch:
        return "害太岁"
    if LIU_PO.get(liunian_branch) == day_branch:
        return "破太岁"
    if LIU_HE.get(liunian_branch) == day_branch:
        return "合太岁"
    return None


def _pillar_xingyun(day_stem: str, branch: str | None) -> str | None:
    if not day_stem or not branch:
        return None
    start_branch = _STAGE_START.get(day_stem)
    if not start_branch:
        return None
    try:
        start_idx = BRANCHES.index(start_branch)
        branch_idx = BRANCHES.index(branch)
    except ValueError:
        return None
    is_yang = day_stem in {"甲", "丙", "戊", "庚", "壬"}
    offset = (branch_idx - start_idx + 12) % 12 if is_yang else (start_idx - branch_idx + 12) % 12
    return _STAGE_NAMES[offset] if 0 <= offset < len(_STAGE_NAMES) else None


def _build_hidden_stems(branch: str, day_stem: str) -> list[dict]:
    items: list[dict] = []
    for hidden_stem, weight in BRANCH_HIDDEN_STEMS.get(branch, []):
        elem, _ = STEM_ELEMENT.get(hidden_stem, (None, None))
        items.append(
            {
                "stem": hidden_stem,
                "weight": weight,
                "element": {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}.get(
                    elem or "", None
                ),
                "ten_god": get_ten_god(day_stem, hidden_stem) if day_stem else None,
            }
        )
    return items


# ──────────────────────────────────────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────────────────────────────────────


def compute_liunian(
    day_stem: str,
    day_branch: str,
    start_year: int,
    end_year: int,
    month_stem: str | None = None,
    month_branch: str | None = None,
    hour_stem: str | None = None,
    hour_branch: str | None = None,
    year_branch: str | None = None,
    flow_label: str = "liunian",
    yongshen_favor: list[str] | None = None,
    yongshen_avoid: list[str] | None = None,
    geju_name: str = "",
    geju_po: dict | None = None,
) -> list[dict]:
    """
    计算流年列表.

    Parameters:
        day_stem:    日主天干（用于十神关系）
        day_branch:  日主地支（用于犯太岁判断）
        start_year:  起始公历年
        end_year:    截止公历年（含）

    Returns 每条 dict:
        {
            "year": int,
            "stem": str,
            "branch": str,
            "ten_god": str,
            "flow_wuxing": str,
            "clash": str | None,   # 犯太岁关系
        }
    """
    results = []
    for year in range(start_year, end_year + 1):
        stem, branch = _ganzhi_of_year(year)
        ten_god = get_ten_god(day_stem, stem)
        stem_elem, _ = STEM_ELEMENT.get(stem, ("?", "?"))
        clash = _liunian_day_relation(branch, day_branch)
        kongwang = list(get_kongwang(stem, branch))
        po_jiu = (geju_po or {}).get("po_jiu") if geju_po else None
        results.append(
            {
                "year": year,
                "stem": stem,
                "branch": branch,
                "ten_god": ten_god,
                "yongshen_shift": _liunian_yongshen_shift(
                    stem_elem if stem_elem != "?" else "",
                    yongshen_favor or [],
                    yongshen_avoid or [],
                ),
                "geju_po_jiu": po_jiu,
                "overlay_palace_map": overlay_palace_map(
                    year_branch or "",
                    month_branch or "",
                    day_branch,
                    hour_branch or "",
                    branch,
                ),
                "hidden_stems": _build_hidden_stems(branch, day_stem),
                "xingyun": _pillar_xingyun(day_stem, branch),
                "self_seat": _pillar_xingyun(stem, branch),
                "self_seat_source": f"{stem}坐{branch}十二长生" if stem and branch else None,
                "kongwang": kongwang,
                "kongwang_hit": branch in kongwang,
                "nayin": NAYIN.get(f"{stem}{branch}"),
                "shensha": compute_flow_shensha_items(
                    flow_label=flow_label,
                    flow_stem=stem,
                    flow_branch=branch,
                    day_stem=day_stem,
                    day_branch=day_branch,
                    month_stem=month_stem,
                    month_branch=month_branch,
                    hour_stem=hour_stem,
                    hour_branch=hour_branch,
                ),
                "wuxing": {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}.get(
                    stem_elem, None
                ),
                "yin_yang": STEM_ELEMENT.get(stem, (None, None))[1] == "yang" and "阳" or "阴",
                "flow_wuxing": stem_elem,
                "clash": clash,
            }
        )
    return results


def compute_liunian_for_dayun(
    day_stem: str,
    day_branch: str,
    dayun_start_age: int,
    dayun_start_year: int,
    span: int = 10,
) -> list[dict]:
    """
    计算某大运柱内的流年（默认10年）.
    """
    return compute_liunian(
        day_stem=day_stem,
        day_branch=day_branch,
        start_year=dayun_start_year,
        end_year=dayun_start_year + span - 1,
    )
