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

from typing import Optional

from services.bazi_engine.tables import (
    STEMS,
    BRANCHES,
    STEM_ELEMENT,
    BRANCH_CHONG,
    LIU_HE,
    get_ten_god,
)

# ──────────────────────────────────────────────────────────────────────────────
# 刑、害、破 — 补充关系表
# ──────────────────────────────────────────────────────────────────────────────

# 六害: branch → 与其相害的branch
LIU_HAI: dict[str, str] = {
    "子": "未", "未": "子",
    "丑": "午", "午": "丑",
    "寅": "巳", "巳": "寅",
    "卯": "辰", "辰": "卯",
    "申": "亥", "亥": "申",
    "酉": "戌", "戌": "酉",
}

# 六破: branch → 与其相破的branch
LIU_PO: dict[str, str] = {
    "子": "酉", "酉": "子",
    "丑": "辰", "辰": "丑",
    "寅": "亥", "亥": "寅",
    "卯": "午", "午": "卯",
    "巳": "申", "申": "巳",
    "未": "戌", "戌": "未",
}

# 三刑: branch → set(与其相刑的branch)
SAN_XING: dict[str, set[str]] = {
    "寅": {"申", "巳"},   # 寅刑申(无礼之刑)部分; 实际寅申巳三刑
    "巳": {"申", "寅"},
    "申": {"寅", "巳"},
    "丑": {"戌", "未"},   # 丑戌未三刑
    "戌": {"丑", "未"},
    "未": {"丑", "戌"},
    "子": {"卯"},          # 子卯相刑（无礼之刑）
    "卯": {"子"},
    "辰": {"辰"},          # 辰午酉亥自刑
    "午": {"午"},
    "酉": {"酉"},
    "亥": {"亥"},
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

def _liunian_day_relation(liunian_branch: str, day_branch: str) -> Optional[str]:
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


# ──────────────────────────────────────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────────────────────────────────────

def compute_liunian(
    day_stem: str,
    day_branch: str,
    start_year: int,
    end_year: int,
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
        results.append({
            "year": year,
            "stem": stem,
            "branch": branch,
            "ten_god": ten_god,
            "flow_wuxing": stem_elem,
            "clash": clash,
        })
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
