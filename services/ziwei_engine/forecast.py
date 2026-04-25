"""
services/ziwei_engine/forecast.py — 综合运势预测与事件分析引擎

将本命盘 × 大运 × 流年 × 流月 整合为可读运势报告：
  - 年运：流年命宫宫位主题 + 大运叠加 + 四化分析
  - 月运：12个流月各自的宫位主题与四化
  - 事件标签：桃花/姻缘、灾祸/健康、财运、事业/官运、变动/迁移、贵人/助力、口舌是非
  - 各维度详解：感情/财运/事业/健康
  - 行动建议：针对强等级事件给出具体建议
  - 评分：1-100 综合运势评估
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from . import ZiweiChart
    from .dayun import DayunItem

from .tables import PALACE_NAMES, BRANCHES, STEMS

# ──────────────────────────────────────────────────────────────
# 触发规则常量
# ──────────────────────────────────────────────────────────────

# 桃花/姻缘相关星（本命任意宫位有这些星都增加桃花分）
_PEACH_STARS   = {"贪狼", "廉贞", "天姚", "咸池", "红鸾", "天喜"}
# 煞星（本命宫位有这些增加灾祸风险）
_SHA_STARS     = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}
# 贵人星
_GUI_STARS     = {"天魁", "天钺", "左辅", "右弼"}
# 宫位分类
_WEALTH_PALACES = {"财帛宫", "田宅宫", "命宫"}
_CAREER_PALACES = {"官禄宫", "命宫", "迁移宫"}
_HEALTH_PALACES = {"命宫", "疾厄宫"}


# ──────────────────────────────────────────────────────────────
# 流年/月命宫所在本命宫位 → 年度/月度主题（短版）
# ──────────────────────────────────────────────────────────────
_PALACE_THEME: dict[str, str] = {
    "命宫":  "自身运势活跃，处于精力充沛、变化较多的阶段，凡事宜主动把握",
    "兄弟宫": "人际与合作为重点，与兄弟、朋友关系有起伏，贵在团结协作",
    "夫妻宫": "感情婚姻是本期轴心，感情运有明显变化，宜关注伴侣互动",
    "子女宫": "与子女、部属或创作项目相关，宜关注后辈与启发性工作",
    "财帛宫": "财运为重点，进财机会增多，适合积极开拓财源",
    "疾厄宫": "健康为核心关注点，宜注意身体状况，避免过劳与冒险",
    "迁移宫": "外部环境变动较大，宜出行、移动，变则通、守则滞",
    "交友宫": "人际关系复杂，贵人小人并现，宜广结善缘、防小人",
    "官禄宫": "事业是本期重心，升职创业机遇较多，宜把握时机积极出击",
    "田宅宫": "家宅、房产或家庭事务活跃，家庭关系有变化宜关注",
    "福德宫": "精神享受与个人爱好偏旺，桃花有机会，内心充实",
    "父母宫": "长辈健康或文书事务为重心，代际关系与健康值得关注",
}

_PALACE_THEME_SHORT: dict[str, str] = {
    "命宫":  "自身运势活跃，变化较多",
    "兄弟宫": "人际合作为重点，贵在协作",
    "夫妻宫": "感情婚姻为期间主轴",
    "子女宫": "涉及部属与创作事务",
    "财帛宫": "财运为重，进财机会多",
    "疾厄宫": "健康为核心，宜注重保养",
    "迁移宫": "变动强，宜出行拓展",
    "交友宫": "人际复杂，广结善缘防小人",
    "官禄宫": "事业是重心，宜把握升迁机遇",
    "田宅宫": "家宅与房产事务有变",
    "福德宫": "精神享受充实，桃花有机会",
    "父母宫": "长辈事务与文书为重",
}


# ──────────────────────────────────────────────────────────────
# 数据结构
# ──────────────────────────────────────────────────────────────

@dataclass
class EventTag:
    """单个运势事件/警示标签。"""
    category: str    # 桃花/姻缘、灾祸/健康、财运、事业/官运、变动/迁移、贵人/助力、口舌是非
    level: str       # 强 / 中 / 弱
    description: str  # 人类可读的事件描述
    source: str       # 触发依据（星曜/宫位/四化）


@dataclass
class PeriodForecast:
    """一个时间段（年/月）的完整运势摘要。"""
    period: str              # 如 "2026年" / "2026年正月(寅)"
    ganzhi: str              # 干支，如 "壬午"
    palace_name: str         # 流年/月命宫对应本命宫位名
    overall: str             # 综合一句话说明
    details: dict[str, str]  # 各维度详解 {感情/财运/事业/健康: 文字}
    events: list[EventTag]   # 事件标签列表
    advice: str              # 行动建议
    score: int               # 综合运势 1-100


@dataclass
class ForecastResult:
    """完整运势预测结果，挂载于 ZiweiChart.forecast。"""
    year: int
    yearly: PeriodForecast               # 年运
    monthly: list[PeriodForecast]        # 12个流月
    current_month: PeriodForecast        # 当前月（或正月）


# ──────────────────────────────────────────────────────────────
# 内部辅助函数
# ──────────────────────────────────────────────────────────────

def _get_current_dayun(chart: 'ZiweiChart', year: int) -> Optional['DayunItem']:
    """返回 year 对应的当前大运项（找不到则取最后一柱）。"""
    for d in chart.dayun.items:
        if d.start_year <= year < d.start_year + 10:
            return d
    return chart.dayun.items[-1] if chart.dayun.items else None


def _branch_to_natal_palace(life_palace_branch: int, target_branch: int) -> str:
    """给定本命命宫地支索引和目标地支索引，返回对应本命宫位名。"""
    offset = (life_palace_branch - target_branch) % 12
    return PALACE_NAMES[offset]


def _stars_in_palace(chart: 'ZiweiChart', palace_name: str) -> tuple[list[str], list[str]]:
    """返回宫位中的 (主星名列表, 辅星名列表)。"""
    for p in chart.palaces:
        if p.name == palace_name:
            return [s["name"] for s in p.main_stars], list(p.aux_stars)
    return [], []


def _sihua_to_palace_map(
    sihua: dict[str, str],    # {星名: "化禄"/"化权"/"化科"/"化忌"}
    chart: 'ZiweiChart',
) -> dict[str, str]:
    """
    将四化 {星名: 化xxx} 转为 {化xxx: 落宫宫名}，
    通过找该星在本命命盘哪个宫位来实现。
    例：{"武曲": "化禄"} → {"化禄": "官禄宫"}
    """
    result: dict[str, str] = {}
    for star, hua_text in sihua.items():
        for p in chart.palaces:
            if (any(s["name"] == star for s in p.main_stars)
                    or star in p.aux_stars):
                result[hua_text] = p.name
                break
    return result


# ──────────────────────────────────────────────────────────────
# 核心事件检测
# ──────────────────────────────────────────────────────────────

def _detect_events(
    chart: 'ZiweiChart',
    life_palace_name: str,      # 流年/月命宫在本命哪个宫
    sihua: dict[str, str],      # 流年/月四化 {星名: 化xxx}
    dy_sihua: dict[str, str],   # 大运四化
    period_label: str,          # 用于描述文字，如"流年"/"正月"
) -> tuple[list[EventTag], int]:
    """
    检测运势事件，返回 (事件列表, 评分增量)。
    评分增量正=吉，负=凶。综合评分基准=60。
    """
    events: list[EventTag] = []
    score_delta = 0

    # 四化落宫映射
    hua_pal = _sihua_to_palace_map(sihua, chart)
    dy_pal  = _sihua_to_palace_map(dy_sihua, chart)

    # ════════════════════════════════════
    # 1. 桃花 / 姻缘
    # ════════════════════════════════════
    pts = 0
    srcs: list[str] = []

    # 流年/月命宫走到感情相关宫位
    if life_palace_name == "夫妻宫":
        pts += 4; srcs.append(f"{period_label}命宫走入本命夫妻宫")
    elif life_palace_name == "福德宫":
        pts += 2; srcs.append(f"{period_label}命宫走入本命福德宫")

    # 本命桃花宫有桃花星
    for pname in ("命宫", "夫妻宫", "福德宫"):
        mains, auxes = _stars_in_palace(chart, pname)
        hit = _PEACH_STARS & (set(mains) | set(auxes))
        if hit:
            pts += 1; srcs.append(f"本命{pname}有{'、'.join(sorted(hit))}")

    # 化禄/化科飞入夫妻宫
    for hua_type in ("化禄", "化科"):
        if hua_pal.get(hua_type) == "夫妻宫":
            pts += 3; srcs.append(f"{period_label}{hua_type}入夫妻宫")
        if dy_pal.get(hua_type) == "夫妻宫":
            pts += 2; srcs.append(f"大运{hua_type}入夫妻宫")

    # 化忌入夫妻宫 → 减分（感情波折）
    if hua_pal.get("化忌") == "夫妻宫":
        pts -= 3; srcs.append(f"{period_label}化忌入夫妻宫，感情有阻")

    if pts >= 6:
        events.append(EventTag("桃花/姻缘", "强",
            "感情机遇极佳，桃花旺盛，单身者有缘分出现，已婚者感情升温",
            "；".join(srcs) or "无"))
        score_delta += 10
    elif pts >= 3:
        events.append(EventTag("桃花/姻缘", "中",
            "感情有一定发展机遇，人际互动活跃，宜自然把握",
            "；".join(srcs) or "无"))
        score_delta += 5
    elif pts >= 1:
        events.append(EventTag("桃花/姻缘", "弱",
            "感情上有小动向，异性缘略有增加，留意身边人际变化",
            "；".join(srcs) or "无"))
        score_delta += 2
    elif pts <= -2:
        events.append(EventTag("感情波折", "中",
            "感情关系有摩擦或阻碍，已婚者宜耐心沟通，暂缓重大感情决定",
            "；".join(srcs) or "无"))
        score_delta -= 5

    # ════════════════════════════════════
    # 2. 灾祸 / 健康
    # ════════════════════════════════════
    pts = 0
    srcs = []

    # 流年/月命宫走到疾厄宫
    if life_palace_name == "疾厄宫":
        pts += 3; srcs.append(f"{period_label}命宫走入本命疾厄宫，健康为重点")

    # 化忌落健康宫位
    for pname in _HEALTH_PALACES:
        if hua_pal.get("化忌") == pname:
            pts += 5; srcs.append(f"{period_label}化忌入{pname}")
        if dy_pal.get("化忌") == pname:
            pts += 3; srcs.append(f"大运化忌入{pname}")

    # 双忌叠加（大运+流年化忌同落一宫）
    if (hua_pal.get("化忌")
            and dy_pal.get("化忌") == hua_pal.get("化忌")):
        pts += 4
        srcs.append(f"大运+{period_label}双忌同落{hua_pal['化忌']}，凶象加重")

    # 本命疾厄/命宫有煞星
    for pname in _HEALTH_PALACES:
        _, auxes = _stars_in_palace(chart, pname)
        sha_here = _SHA_STARS & set(auxes)
        if sha_here:
            pts += 1; srcs.append(f"本命{pname}煞星{'、'.join(sorted(sha_here))}")

    if pts >= 8:
        events.append(EventTag("灾祸/健康", "强",
            "健康与安全风险极高，需特别谨慎，建议全面体检、避开高风险活动，防血光之灾",
            "；".join(srcs) or "无"))
        score_delta -= 18
    elif pts >= 4:
        events.append(EventTag("灾祸/健康", "中",
            "健康或安全有一定隐患，注意劳逸结合，定期检查，避免冒险",
            "；".join(srcs) or "无"))
        score_delta -= 10
    elif pts >= 2:
        events.append(EventTag("灾祸/健康", "弱",
            "有轻微健康波动或小风险，注意作息规律，适当养生",
            "；".join(srcs) or "无"))
        score_delta -= 4

    # ════════════════════════════════════
    # 3. 财运
    # ════════════════════════════════════
    pts = 0
    srcs = []

    if hua_pal.get("化禄") in _WEALTH_PALACES:
        pts += 5; srcs.append(f"{period_label}化禄入{hua_pal['化禄']}")
    if dy_pal.get("化禄") in _WEALTH_PALACES:
        pts += 3; srcs.append(f"大运化禄入{dy_pal['化禄']}")
    if hua_pal.get("化权") == "财帛宫":
        pts += 3; srcs.append(f"{period_label}化权入财帛宫")
    if life_palace_name in _WEALTH_PALACES:
        pts += 2; srcs.append(f"{period_label}命宫走入本命{life_palace_name}")

    # 化忌入财帛宫/田宅宫 → 破财
    if hua_pal.get("化忌") in {"财帛宫", "田宅宫"}:
        pts -= 4; srcs.append(f"{period_label}化忌入{hua_pal['化忌']}，防破财损耗")
    if dy_pal.get("化忌") == "财帛宫":
        pts -= 3; srcs.append("大运化忌入财帛宫")

    if pts >= 6:
        events.append(EventTag("财运", "强",
            "财运旺盛，进财机会大，适合主动拓展财源，可进行稳健投资",
            "；".join(srcs) or "无"))
        score_delta += 12
    elif pts >= 3:
        events.append(EventTag("财运", "中",
            "财运平稳偏好，有小利可期，稳健理财为宜",
            "；".join(srcs) or "无"))
        score_delta += 6
    elif pts <= -4:
        events.append(EventTag("财运波折", "强",
            "财运有明显阻碍，破财风险高，暂缓大额投资，以守为主",
            "；".join(srcs) or "无"))
        score_delta -= 10
    elif pts < 0:
        events.append(EventTag("财运波折", "弱",
            "财运有小波折，注意日常开销与支出管控",
            "；".join(srcs) or "无"))
        score_delta -= 4

    # ════════════════════════════════════
    # 4. 事业 / 官运
    # ════════════════════════════════════
    pts = 0
    srcs = []

    if life_palace_name == "官禄宫":
        pts += 4; srcs.append(f"{period_label}命宫走入本命官禄宫")
    if hua_pal.get("化权") in _CAREER_PALACES:
        pts += 4; srcs.append(f"{period_label}化权入{hua_pal['化权']}")
    if dy_pal.get("化权") in _CAREER_PALACES:
        pts += 3; srcs.append(f"大运化权入{dy_pal['化权']}")
    if hua_pal.get("化禄") == "官禄宫":
        pts += 3; srcs.append(f"{period_label}化禄入官禄宫")
    if hua_pal.get("化科") in _CAREER_PALACES:
        pts += 2; srcs.append(f"{period_label}化科入{hua_pal['化科']}")

    # 化忌入官禄/迁移 → 事业阻
    if hua_pal.get("化忌") in _CAREER_PALACES:
        pts -= 3; srcs.append(f"{period_label}化忌入{hua_pal['化忌']}，事业有阻")
    if dy_pal.get("化忌") == "官禄宫":
        pts -= 2; srcs.append("大运化忌入官禄宫")

    if pts >= 8:
        events.append(EventTag("事业/官运", "强",
            "事业运极佳，有升迁创业重大机遇，宜主动争取、积极表现",
            "；".join(srcs) or "无"))
        score_delta += 14
    elif pts >= 4:
        events.append(EventTag("事业/官运", "中",
            "事业稳步发展，有晋升或拓展机遇，积极表现可获认可",
            "；".join(srcs) or "无"))
        score_delta += 7
    elif pts <= -3:
        events.append(EventTag("事业挫折", "中",
            "事业有阻滞或口舌是非，宜低调行事，韬光养晦",
            "；".join(srcs) or "无"))
        score_delta -= 8
    elif pts < 0:
        events.append(EventTag("事业挫折", "弱",
            "事业有小阻力，注意职场人际，避免正面冲突",
            "；".join(srcs) or "无"))
        score_delta -= 3

    # ════════════════════════════════════
    # 5. 贵人 / 助力
    # ════════════════════════════════════
    pts = 0
    srcs = []

    _, life_auxes = _stars_in_palace(chart, "命宫")
    gui = _GUI_STARS & set(life_auxes)
    if gui:
        pts += 2; srcs.append(f"本命命宫有{'、'.join(sorted(gui))}")

    if hua_pal.get("化科") in {"命宫", "官禄宫", "交友宫"}:
        pts += 3; srcs.append(f"{period_label}化科入{hua_pal['化科']}")
    if dy_pal.get("化科") in {"命宫", "官禄宫"}:
        pts += 2; srcs.append(f"大运化科入{dy_pal['化科']}")
    if hua_pal.get("化禄") in {"交友宫", "命宫"}:
        pts += 2; srcs.append(f"{period_label}化禄入{hua_pal['化禄']}，贵人助力")

    if pts >= 5:
        events.append(EventTag("贵人/助力", "强",
            "贵人运强，有重要贵人相助，人际关系顺畅，宜借势而为",
            "；".join(srcs) or "无"))
        score_delta += 8
    elif pts >= 2:
        events.append(EventTag("贵人/助力", "中",
            "有一定贵人助力，善用人脉可事半功倍",
            "；".join(srcs) or "无"))
        score_delta += 4

    # ════════════════════════════════════
    # 6. 变动 / 迁移
    # ════════════════════════════════════
    pts = 0
    srcs = []

    if life_palace_name == "迁移宫":
        pts += 4; srcs.append(f"{period_label}命宫走入本命迁移宫")

    for p in chart.palaces:
        if "天马" in p.aux_stars and p.name in {"迁移宫", "命宫"}:
            pts += 2; srcs.append(f"本命{p.name}有天马")

    for hua_type in ("化禄", "化权"):
        if hua_pal.get(hua_type) == "迁移宫":
            pts += 2; srcs.append(f"{period_label}{hua_type}入迁移宫")

    if pts >= 4:
        events.append(EventTag("变动/迁移", "强",
            "变动性大，宜出行或移居，守旧难行，主动出击则柳暗花明",
            "；".join(srcs) or "无"))
        score_delta += 3
    elif pts >= 2:
        events.append(EventTag("变动/迁移", "中",
            "有一定变动倾向，可能涉及出行或工作地点变化，随缘应对",
            "；".join(srcs) or "无"))
        score_delta += 1

    # ════════════════════════════════════
    # 7. 口舌 / 是非
    # ════════════════════════════════════
    pts = 0
    srcs = []

    # 化忌入迁移宫/交友宫 → 口舌是非
    for pname in ("迁移宫", "交友宫", "父母宫"):
        if hua_pal.get("化忌") == pname:
            pts += 3; srcs.append(f"{period_label}化忌入{pname}")
        if dy_pal.get("化忌") == pname:
            pts += 2; srcs.append(f"大运化忌入{pname}")

    # 本命交友/迁移有煞星
    for pname in ("交友宫", "迁移宫"):
        _, auxes = _stars_in_palace(chart, pname)
        sha = _SHA_STARS & set(auxes)
        if sha:
            pts += 1; srcs.append(f"本命{pname}有煞星{'、'.join(sorted(sha))}")

    if pts >= 4:
        events.append(EventTag("口舌/是非", "中",
            "人际关系易生是非，言行宜低调，防小人中伤",
            "；".join(srcs) or "无"))
        score_delta -= 4
    elif pts >= 2:
        events.append(EventTag("口舌/是非", "弱",
            "口舌小是非有机会出现，避免不必要争论",
            "；".join(srcs) or "无"))
        score_delta -= 2

    return events, score_delta


# ──────────────────────────────────────────────────────────────
# 各维度详解生成
# ──────────────────────────────────────────────────────────────

def _build_details(
    hua_pal: dict[str, str],   # {化xxx: 宫位名}
    dy_pal: dict[str, str],
    life_palace_name: str,
    period_label: str,
) -> dict[str, str]:
    """生成感情/财运/事业/健康 四维度详解文字。"""
    details: dict[str, str] = {}

    # ── 感情 ────────────────────────────────────────────────
    love_lu = hua_pal.get("化禄") == "夫妻宫"
    love_ke = hua_pal.get("化科") == "夫妻宫"
    love_ji = hua_pal.get("化忌") == "夫妻宫"
    dy_love_lu = dy_pal.get("化禄") == "夫妻宫"
    if love_lu and dy_love_lu:
        details["感情"] = (
            f"{period_label}与大运双禄入夫妻宫，感情缘分强力叠加，"
            "感情婚恋时机极佳，单身者宜主动把握，伴侣感情大幅升温"
        )
    elif love_lu:
        details["感情"] = (
            f"{period_label}化禄飞入夫妻宫，感情运佳，"
            "有缘分出现或感情深化，适合婚恋进展与表白"
        )
    elif love_ke:
        details["感情"] = (
            f"{period_label}化科飞入夫妻宫，感情名声有助，"
            "相处和谐，易得到认可与欣赏"
        )
    elif love_ji:
        details["感情"] = (
            f"{period_label}化忌飞入夫妻宫，感情有摩擦或阻碍，"
            "宜耐心沟通，暂缓重大感情决定，注意情感纠葛"
        )
    elif life_palace_name == "夫妻宫":
        details["感情"] = (
            f"{period_label}命宫走入夫妻宫，感情婚姻为本期主题，有明显起伏变化，宜用心经营"
        )
    else:
        details["感情"] = "感情运势相对平稳，以维护现有关系为主，无特别大变化"

    # ── 财运 ────────────────────────────────────────────────
    wealth_lu_palace = hua_pal.get("化禄", "")
    dy_wealth_lu = dy_pal.get("化禄", "") in _WEALTH_PALACES
    wealth_ji = hua_pal.get("化忌") in {"财帛宫", "田宅宫"}
    if wealth_lu_palace in _WEALTH_PALACES and dy_wealth_lu:
        details["财运"] = (
            f"{period_label}化禄入{wealth_lu_palace}，与大运禄星同步，"
            "财运双重加持，进财机会多，适合稳健投资与开拓收入渠道"
        )
    elif wealth_lu_palace in _WEALTH_PALACES:
        details["财运"] = (
            f"{period_label}化禄飞入{wealth_lu_palace}，财运活跃，"
            "进财机会增多，宜积极开源"
        )
    elif wealth_ji:
        details["财运"] = (
            f"{period_label}化忌入{hua_pal.get('化忌')}，财运有阻，"
            "需防破财损耗，暂缓大额投资，以守为主"
        )
    elif life_palace_name in _WEALTH_PALACES:
        details["财运"] = (
            f"{period_label}命宫走入{life_palace_name}，财运为本期重点，"
            "宜把握时机，开拓多元收入"
        )
    else:
        details["财运"] = "财运平稳，日常收支正常，持续耕耘可期稳定收益"

    # ── 事业 ────────────────────────────────────────────────
    career_quan = hua_pal.get("化权", "") in _CAREER_PALACES
    career_lu = hua_pal.get("化禄") == "官禄宫"
    career_ji = hua_pal.get("化忌", "") in _CAREER_PALACES
    dy_career = dy_pal.get("化权", "") in _CAREER_PALACES or dy_pal.get("化禄") == "官禄宫"
    if career_quan and dy_career:
        details["事业"] = (
            f"{period_label}化权与大运叠加入{hua_pal['化权']}，"
            "事业运最旺，升职或重大突破极可能，宜全力出击"
        )
    elif career_quan:
        details["事业"] = (
            f"{period_label}化权入{hua_pal['化权']}，事业运强，"
            "有升职或拓展机会，积极争取可获认可"
        )
    elif career_lu:
        details["事业"] = (
            f"{period_label}化禄入官禄宫，事业顺遂，"
            "工作上有机会拓展，财官并见"
        )
    elif career_ji:
        details["事业"] = (
            f"{period_label}化忌入{hua_pal['化忌']}，事业有一定阻滞，"
            "宜低调行事，韬光养晦，避免与上级正面冲突"
        )
    elif life_palace_name == "官禄宫":
        details["事业"] = (
            f"{period_label}命宫走入官禄宫，事业为本期重心，宜积极把握升迁机遇"
        )
    else:
        details["事业"] = "事业运势稳定，专注本职工作，循序渐进"

    # ── 健康 ────────────────────────────────────────────────
    health_ji = (hua_pal.get("化忌") in _HEALTH_PALACES
                 or dy_pal.get("化忌") in _HEALTH_PALACES)
    if life_palace_name == "疾厄宫":
        details["健康"] = (
            f"{period_label}命宫走入疾厄宫，健康为重心，"
            "宜积极养生保健，定期体检，避免过劳"
        )
    elif hua_pal.get("化忌") == "命宫" and dy_pal.get("化忌") == "命宫":
        details["健康"] = (
            "大运与流年双忌同落命宫，身心压力较大，务必重视健康管理，防大病"
        )
    elif health_ji:
        details["健康"] = (
            "化忌涉及健康宫位，注意身体状况，避免透支体力，"
            "有旧患者尤需留意"
        )
    else:
        details["健康"] = "健康状况相对平稳，注意日常作息调养，保持规律运动"

    return details


# ──────────────────────────────────────────────────────────────
# 行动建议生成
# ──────────────────────────────────────────────────────────────

def _build_advice(events: list[EventTag], palace_name: str) -> str:
    """根据事件列表及宫位主题生成综合行动建议。"""
    strong_bad  = [e for e in events if e.level == "强" and
                   any(k in e.category for k in ("灾祸", "挫折", "波折"))]
    strong_good = [e for e in events if e.level == "强" and
                   any(k in e.category for k in ("财运", "事业", "官运", "桃花", "贵人"))]
    medium_events = [e for e in events if e.level in ("强", "中")]

    parts: list[str] = []

    # 强凶优先提示
    if strong_bad:
        cats = "、".join(e.category for e in strong_bad)
        parts.append(f"❗{cats}风险显著，建议降低冒险行为，谨慎决策，可考虑行善积德以化解煞气")

    # 强吉着重把握
    if strong_good:
        cats = "、".join(e.category for e in strong_good)
        parts.append(f"✅{cats}机遇突出，宜主动出击，善加利用这段有利时机")

    # 中等提示
    mid_bad = [e for e in medium_events if
               any(k in e.category for k in ("灾祸", "挫折", "波折", "口舌", "是非"))]
    if mid_bad:
        cats = "、".join(set(e.category for e in mid_bad))
        parts.append(f"⚠ 注意{cats}，言行谨慎，避免无谓争端")

    # 宫位主题建议
    if not parts:
        theme_advice = {
            "命宫":  "整体运势平稳，以稳健进取为宜",
            "夫妻宫": "重视感情经营，多沟通多陪伴",
            "财帛宫": "积极理财，管控开销，寻找稳健的收益机会",
            "疾厄宫": "健康第一，规律作息，避免透支",
            "官禄宫": "把握事业机遇，积极表现，建立专业形象",
            "迁移宫": "顺应变化，灵活应对，可考虑出行或地理移动",
            "交友宫": "广结善缘，防小人，发展有益人脉",
            "福德宫": "享受当下，保持积极心态，丰富精神生活",
        }
        advice = theme_advice.get(palace_name, f"关注{palace_name}相关事务，以稳为主")
        parts.append(advice)

    return "；".join(parts) + "。"


# ──────────────────────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────────────────────

def generate_forecast(
    chart: 'ZiweiChart',
    liunian_year: int,
    current_month: int = 0,
) -> ForecastResult:
    """
    生成完整运势预测。

    chart         : 完整命盘对象（ZiweiChart，需已计算 liunian / liuyue_data）
    liunian_year  : 流年（公历年份）
    current_month : 当前月份（1-12），0=自动取今日月份
    """
    if current_month <= 0:
        from zoneinfo import ZoneInfo as _ZI
        current_month = datetime.datetime.now(_ZI("Asia/Shanghai")).month

    # ── 当前大运 ─────────────────────────────────────────────
    dy_item   = _get_current_dayun(chart, liunian_year)
    dy_sihua  = dy_item.sihua if dy_item else {}
    dy_label  = f"大运{dy_item.ganzhi}" if dy_item else "未入大运"

    # ── 流年信息（始终按 liunian_year 重算，不依赖 chart.liunian）─
    from .liunian import calc_liunian
    from .transforms import SIHUA_TABLE
    liunian = calc_liunian(liunian_year, 0, chart.life_palace_branch)
    stem_idx = (liunian_year - 4) % 10
    raw = SIHUA_TABLE.get(STEMS[stem_idx], {})
    liunian.sihua = {star: f"化{hua}" for hua, star in raw.items()}

    ln_life_palace = _branch_to_natal_palace(
        chart.life_palace_branch, liunian.life_palace_branch
    )
    ln_events, ln_score_delta = _detect_events(
        chart, ln_life_palace, liunian.sihua, dy_sihua, "流年"
    )
    ln_hua_pal = _sihua_to_palace_map(liunian.sihua, chart)
    dy_hua_pal = _sihua_to_palace_map(dy_sihua, chart)

    ln_details = _build_details(ln_hua_pal, dy_hua_pal, ln_life_palace, "流年")
    ln_advice  = _build_advice(ln_events, ln_life_palace)
    ln_theme   = _PALACE_THEME.get(ln_life_palace, "")
    ln_overall = (
        f"{liunian.year_gz}年，流年命宫走入本命{ln_life_palace}（{dy_label}）。"
        f"{ln_theme}"
    )
    ln_score = max(1, min(100, 60 + ln_score_delta))

    yearly = PeriodForecast(
        period=f"{liunian_year}年",
        ganzhi=liunian.year_gz,
        palace_name=ln_life_palace,
        overall=ln_overall,
        details=ln_details,
        events=ln_events,
        advice=ln_advice,
        score=ln_score,
    )

    # ── 流月（12个月，始终按 liunian 重算）─────────────────────
    from .liunian import calc_liuyue_list
    branch_to_name = {p.branch_idx: p.name for p in chart.palaces}
    liuyue_data = calc_liuyue_list(liunian, branch_to_name)

    monthly_forecasts: list[PeriodForecast] = []
    cur_month_forecast: Optional[PeriodForecast] = None

    for d in liuyue_data:
        mo_num   = d['month']
        mo_life_palace = _branch_to_natal_palace(
            chart.life_palace_branch, d['life_palace_branch']
        )
        mo_sihua  = d.get('sihua', {})
        mo_events, mo_score_delta = _detect_events(
            chart, mo_life_palace, mo_sihua, dy_sihua, d['month_name']
        )
        mo_hua_pal = _sihua_to_palace_map(mo_sihua, chart)
        mo_details = _build_details(mo_hua_pal, dy_hua_pal, mo_life_palace, d['month_name'])
        mo_advice  = _build_advice(mo_events, mo_life_palace)

        mo_theme_short = _PALACE_THEME_SHORT.get(mo_life_palace, "")
        mo_overall = (
            f"{d['month_name']}（{d['month_gz']}），"
            f"流月命宫走入{mo_life_palace}。{mo_theme_short}"
        )
        # 月评分：年运基准(一半) + 月运增量
        mo_score = max(1, min(100, 60 + ln_score_delta // 2 + mo_score_delta))

        mf = PeriodForecast(
            period=f"{liunian_year}年{d['month_name']}",
            ganzhi=d['month_gz'],
            palace_name=mo_life_palace,
            overall=mo_overall,
            details=mo_details,
            events=mo_events,
            advice=mo_advice,
            score=mo_score,
        )
        monthly_forecasts.append(mf)
        if mo_num == current_month:
            cur_month_forecast = mf

    if cur_month_forecast is None:
        cur_month_forecast = monthly_forecasts[0] if monthly_forecasts else yearly

    return ForecastResult(
        year=liunian_year,
        yearly=yearly,
        monthly=monthly_forecasts,
        current_month=cur_month_forecast,
    )
