"""
services/ziwei_engine/zeri_engine.py — §13 择日推荐引擎

根据命主紫微命盘信息（命宫地支、五行局、本命年支等）以及用途，
为指定年月中的每一天评分，并返回吉日推荐列表。

算法概述
--------
每天得分初始为 50 分，根据以下规则加减：

  1. 天干五行与命主五行的生克关系（±15）
  2. 日支与命宫地支的三合/六合/相冲/相刑/相害关系（±30/±20/±10）
  3. 日支与本命年支的冲克关系（额外罚分）
  4. 一年中岁破日（日支与年支相冲）大幅罚分 -40
  5. 月破日（日支与月支相冲）罚分 -25
  6. 天德/月德日（天干与当月天德/月德相符）加分 +15
  7. 用途专属加成（±10）

最终评级
--------
  大吉 ≥ 78 / 吉 ≥ 62 / 中 ≥ 45 / 凶 < 45
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from typing import Optional

import sxtwl  # type: ignore[import]

from .tables import BRANCHES, STEMS

# ─────────────────────────────────────────────────────────────
# 关系查找表
# ─────────────────────────────────────────────────────────────

# 三合局（一组三个地支彼此三合）
_SANHE: list[frozenset[int]] = [
    frozenset({8, 0, 4}),   # 申子辰（水局）
    frozenset({2, 6, 10}),  # 寅午戌（火局）
    frozenset({11, 3, 7}),  # 亥卯未（木局）
    frozenset({5, 9, 1}),   # 巳酉丑（金局）
]

# 六合对（相邻天地合化）
_LIUHE: list[frozenset[int]] = [
    frozenset({0, 1}),   # 子丑合土
    frozenset({2, 11}),  # 寅亥合木
    frozenset({3, 10}),  # 卯戌合火
    frozenset({4, 9}),   # 辰酉合金
    frozenset({5, 8}),   # 巳申合水
    frozenset({6, 7}),   # 午未合土
]

# 相冲对（六冲）
_CHONG: list[frozenset[int]] = [
    frozenset({0, 6}),   # 子午冲
    frozenset({1, 7}),   # 丑未冲
    frozenset({2, 8}),   # 寅申冲
    frozenset({3, 9}),   # 卯酉冲
    frozenset({4, 10}),  # 辰戌冲
    frozenset({5, 11}),  # 巳亥冲
]

# 相害对（六害）
_HAI: list[frozenset[int]] = [
    frozenset({0, 7}),   # 子未害
    frozenset({1, 6}),   # 丑午害
    frozenset({2, 5}),   # 寅巳害
    frozenset({3, 4}),   # 卯辰害
    frozenset({8, 11}),  # 申亥害
    frozenset({9, 10}),  # 酉戌害
]

# 相刑（仅记录有刑煞意义的对）
_XING: list[frozenset[int]] = [
    frozenset({2, 5}),   # 寅刑巳 / 巳刑寅
    frozenset({5, 8}),   # 巳刑申 / 申刑巳
    frozenset({2, 8}),   # （与上面形成三刑，也单独记录）
    frozenset({1, 7}),   # 丑刑未
    frozenset({7, 10}),  # 未刑戌
    frozenset({1, 10}),  # 戌刑丑（三刑）
    frozenset({0, 3}),   # 子卯相刑
]

# ─────────────────────────────────────────────────────────────
# 天干五行 & 五行生克
# ─────────────────────────────────────────────────────────────

# 天干索引 → 五行 (0=木,1=火,2=土,3=金,4=水)
_STEM_WX: list[int] = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]  # 甲乙=木,丙丁=火,...

# 五行生克: 生我 (sheng) → 我克 (ke) 旋转表
# 木(0)→火(1)→土(2)→金(3)→水(4)→木(0)  相生
# 木(0)克土(2), 火(1)克金(3), 土(2)克水(4), 金(3)克木(0), 水(4)克火(1)  相克

_SHENG_ME: list[int] = [4, 0, 1, 2, 3]  # 生我者：木由水生、火由木生...
_I_SHENG: list[int]  = [1, 2, 3, 4, 0]  # 我生者
_KE_ME: list[int]   = [3, 4, 0, 1, 2]  # 克我者：木被金克...
_I_KE: list[int]    = [2, 3, 4, 0, 1]  # 我克者

def _natal_wx(wuxing_ju_name: str) -> int:
    """从五行局名称解析纳音五行（0=木,1=火,2=土,3=金,4=水）。"""
    m = {"水": 4, "木": 0, "金": 3, "土": 2, "火": 1}
    for k, v in m.items():
        if k in wuxing_ju_name:
            return v
    return 2  # 默认土

def _stem_favor(stem_idx: int, natal_wx: int) -> int:
    """
    日天干五行与命主五行的关系得分：
      生我(+12) / 同我(+6) / 我生(+4) / 我克(-8) / 克我(-12)
    """
    day_wx = _STEM_WX[stem_idx]
    if day_wx == natal_wx:
        return 6
    if day_wx == _SHENG_ME[natal_wx]:
        return 12
    if day_wx == _I_SHENG[natal_wx]:
        return 4
    if day_wx == _KE_ME[natal_wx]:
        return -12
    if day_wx == _I_KE[natal_wx]:
        return -8
    return 0

# ─────────────────────────────────────────────────────────────
# 地支关系得分
# ─────────────────────────────────────────────────────────────

def _branch_rel_score(b1: int, b2: int) -> tuple[int, str]:
    """
    两地支关系评分。返回 (得分, 关系描述)。
      三合+22, 六合+16, 相冲-30, 相刑-18, 相害-10, 无关系 0
    """
    pair = frozenset({b1, b2})
    for g in _SANHE:
        if b1 in g and b2 in g:
            return 22, "三合"
    for g in _LIUHE:
        if pair == g:
            return 16, "六合"
    for g in _CHONG:
        if pair == g:
            return -30, "相冲"
    for g in _XING:
        if pair == g:
            return -18, "相刑"
    for g in _HAI:
        if pair == g:
            return -10, "相害"
    return 0, ""

# ─────────────────────────────────────────────────────────────
# 天德/月德 查找表（月支→天干索引）
# ─────────────────────────────────────────────────────────────

# 月支 branch_idx → 天德天干索引
# 寅月(2)→丁(3), 卯(3)→申 (branch, not stem - 特殊), ...
# 注：天德除卯月(申)和酉月(寅)外均为天干；简化：只处理天干匹配
_TIANDE: dict[int, str] = {
    2:  "3",   # 正月寅→天德丁
    3:  "stem_申",  # 二月卯→天德申（地支，略过天干匹配）
    4:  "8",   # 三月辰→天德壬
    5:  "7",   # 四月巳→天德辛
    6:  "branch_亥",  # 五月午→天德亥（地支）
    7:  "0",   # 六月未→天德甲
    8:  "9",   # 七月申→天德癸
    9:  "branch_寅",  # 八月酉→天德寅（地支）
    10: "2",   # 九月戌→天德丙
    11: "1",   # 十月亥→天德乙
    0:  "branch_巳",  # 十一月子→天德巳（地支）
    1:  "6",   # 十二月丑→天德庚
}

# 月德：寅午戌月→丙, 申子辰月→壬, 亥卯未月→甲, 巳酉丑月→庚
_YUEDE_STEM: dict[int, int] = {}
for _b in (2, 6, 10):  # 寅午戌
    _YUEDE_STEM[_b] = STEMS.index("丙")
for _b in (8, 0, 4):   # 申子辰
    _YUEDE_STEM[_b] = STEMS.index("壬")
for _b in (11, 3, 7):  # 亥卯未
    _YUEDE_STEM[_b] = STEMS.index("甲")
for _b in (5, 9, 1):   # 巳酉丑
    _YUEDE_STEM[_b] = STEMS.index("庚")


def _virtue_score(day_stem_idx: int, day_branch_idx: int, month_branch_idx: int) -> tuple[int, list[str]]:
    """检查当天是否为天德/月德日，返回加分和描述列表。"""
    bonus = 0
    labels: list[str] = []

    td = _TIANDE.get(month_branch_idx, "")
    if td.isdigit():
        if day_stem_idx == int(td):
            bonus += 15
            labels.append(f"天德日（{STEMS[day_stem_idx]}）")
    elif td.startswith("stem_"):
        pass  # 地支型天德：暂不处理
    elif td.startswith("branch_"):
        pass

    yd_stem = _YUEDE_STEM.get(month_branch_idx)
    if yd_stem is not None and day_stem_idx == yd_stem:
        bonus += 10
        labels.append(f"月德日（{STEMS[day_stem_idx]}）")

    return bonus, labels

# ─────────────────────────────────────────────────────────────
# 用途名称
# ─────────────────────────────────────────────────────────────

PURPOSES: dict[str, str] = {
    "marriage":  "婚嫁/感情",
    "business":  "商业/财务",
    "travel":    "出行",
    "medical":   "求医/健康",
    "move":      "搬家/入宅",
    "career":    "事业/求职",
    "general":   "通用",
}

# ─────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────

@dataclass
class ZeriDayResult:
    """单日择日评分结果。"""
    date: str              # "2026-04-01"
    weekday: str           # 日/一/二/三/四/五/六
    day_gz: str            # 干支，如"乙巳"
    day_stem: str          # 天干
    day_branch: str        # 地支
    lunar_info: str        # 农历简要（如"三月初五"）
    score: int             # 0-100
    level: str             # 大吉/吉/中/凶
    level_css: str         # daji/ji/zhong/xiong
    evidence: list[str]    # 得分依据说明
    is_break: bool         # 是否岁破/月破日（凶日标记）
    is_virtue: bool        # 是否天德/月德日


@dataclass
class ZeriMonthResult:
    """一整月择日结果。"""
    year: int
    month: int
    purpose: str
    purpose_label: str
    year_gz: str
    month_gz: str
    days: list[ZeriDayResult] = field(default_factory=list)
    top_days: list[str] = field(default_factory=list)  # 推荐日期列表


# ─────────────────────────────────────────────────────────────
# 主计算函数
# ─────────────────────────────────────────────────────────────

_WEEKDAY_ZH = ["一", "二", "三", "四", "五", "六", "日"]


def recommend_month(
    year: int,
    month: int,
    life_palace_branch: str,
    wuxing_ju_name: str,
    natal_year_branch: str = "",
    purpose: str = "general",
) -> ZeriMonthResult:
    """
    为指定年月生成逐日择日评分。

    参数
    ----
    year, month           : 公历年月（如 2026, 4）
    life_palace_branch    : 命宫地支（如 "子"）
    wuxing_ju_name        : 五行局名（如 "水二局"）
    natal_year_branch     : 本命年支（如 "午"），空则不加/减本命冲
    purpose               : "marriage"/"business"/"travel"/"medical"/"move"/"career"/"general"
    """
    # ── 解析基础参数
    life_b = BRANCHES.index(life_palace_branch) if life_palace_branch in BRANCHES else -1
    natal_b = BRANCHES.index(natal_year_branch) if natal_year_branch in BRANCHES else -1
    natal_wx = _natal_wx(wuxing_ju_name)
    purpose_label = PURPOSES.get(purpose, "通用")

    # ── 获取年/月干支（以月1日为基准）
    ref_day = sxtwl.fromSolar(year, month, 1)
    year_gz_obj = ref_day.getYearGZ()
    year_stem_idx  = year_gz_obj.tg
    year_branch_idx = year_gz_obj.dz
    year_gz_str = STEMS[year_stem_idx] + BRANCHES[year_branch_idx]

    month_gz_obj = ref_day.getMonthGZ()
    month_stem_idx   = month_gz_obj.tg
    month_branch_idx = month_gz_obj.dz
    month_gz_str = STEMS[month_stem_idx] + BRANCHES[month_branch_idx]

    # 月破 = 与月支相冲的地支
    month_break_b = (month_branch_idx + 6) % 12
    # 岁破 = 与年支相冲的地支
    year_break_b  = (year_branch_idx + 6) % 12

    # ── 遍历当月所有天
    _, days_in_month = calendar.monthrange(year, month)
    day_results: list[ZeriDayResult] = []

    for day_num in range(1, days_in_month + 1):
        day_obj = sxtwl.fromSolar(year, month, day_num)
        day_gz_obj   = day_obj.getDayGZ()
        day_stem_idx = day_gz_obj.tg
        day_b_idx    = day_gz_obj.dz

        day_gz_str  = STEMS[day_stem_idx] + BRANCHES[day_b_idx]
        date_str    = f"{year:04d}-{month:02d}-{day_num:02d}"
        import datetime
        weekday_idx = datetime.date(year, month, day_num).weekday()
        weekday_str = _WEEKDAY_ZH[weekday_idx]

        # 农历
        l_month = day_obj.getLunarMonth()
        l_day   = day_obj.getLunarDay()
        lunar_str = _lunar_day_str(l_month, l_day)

        evidence: list[str] = []
        score = 50

        # 1. 日天干五行与命主五行
        stem_sc = _stem_favor(day_stem_idx, natal_wx)
        if stem_sc > 0:
            evidence.append(f"日天干{STEMS[day_stem_idx]}五行利命（+{stem_sc}）")
        elif stem_sc < 0:
            evidence.append(f"日天干{STEMS[day_stem_idx]}五行不利命（{stem_sc}）")
        score += stem_sc

        # 2. 日支与命宫地支关系
        if life_b >= 0:
            b_sc, b_rel = _branch_rel_score(day_b_idx, life_b)
            if b_rel:
                direction = "利" if b_sc > 0 else "不利"
                evidence.append(
                    f"日支{BRANCHES[day_b_idx]}与命宫地支{life_palace_branch}"
                    f"【{b_rel}】，{direction}命主（{'+' if b_sc>0 else ''}{b_sc}）"
                )
            score += b_sc

        # 3. 日支与本命年支冲克
        if natal_b >= 0:
            nb_sc, nb_rel = _branch_rel_score(day_b_idx, natal_b)
            # 仅保留凶性（不重复加吉性），避免过度叠加
            if nb_sc < 0:
                penalty = nb_sc // 2  # 本命年支影响权重折半
                evidence.append(
                    f"日支{BRANCHES[day_b_idx]}与本命年支{natal_year_branch}"
                    f"【{nb_rel}】，冲本命（{penalty}）"
                )
                score += penalty

        # 4. 岁破日
        is_break = False
        if day_b_idx == year_break_b:
            score -= 40
            evidence.append(f"⚠ 岁破日（日支{BRANCHES[day_b_idx]}冲年支{BRANCHES[year_branch_idx]}，-40）")
            is_break = True
        elif day_b_idx == month_break_b:
            score -= 25
            evidence.append(f"⚠ 月破日（日支{BRANCHES[day_b_idx]}冲月支{BRANCHES[month_branch_idx]}，-25）")
            is_break = True

        # 5. 天德/月德加成
        virt_sc, virt_labels = _virtue_score(day_stem_idx, day_b_idx, month_branch_idx)
        if virt_sc > 0:
            evidence.extend([f"✨ {l}" for l in virt_labels])
            score += virt_sc
        is_virtue = virt_sc > 0

        # 6. 用途专属加成
        purpose_sc, purpose_ev = _purpose_bonus(
            purpose, day_b_idx, life_b, natal_b, natal_wx, day_stem_idx
        )
        if purpose_sc != 0:
            evidence.append(purpose_ev)
            score += purpose_sc

        # 规整到 0-100 区间
        score = max(0, min(100, score))

        # 评级
        if score >= 78:
            level, css = "大吉", "daji"
        elif score >= 62:
            level, css = "吉", "ji"
        elif score >= 45:
            level, css = "中", "zhong"
        else:
            level, css = "凶", "xiong"

        day_results.append(ZeriDayResult(
            date=date_str,
            weekday=weekday_str,
            day_gz=day_gz_str,
            day_stem=STEMS[day_stem_idx],
            day_branch=BRANCHES[day_b_idx],
            lunar_info=lunar_str,
            score=score,
            level=level,
            level_css=css,
            evidence=evidence,
            is_break=is_break,
            is_virtue=is_virtue,
        ))

    # 推荐日：评级为大吉/吉 的前 8 天
    top = [d.date for d in sorted(day_results, key=lambda x: -x.score) if d.level in ("大吉", "吉")][:8]

    return ZeriMonthResult(
        year=year,
        month=month,
        purpose=purpose,
        purpose_label=purpose_label,
        year_gz=year_gz_str,
        month_gz=month_gz_str,
        days=day_results,
        top_days=top,
    )


# ─────────────────────────────────────────────────────────────
# 用途加成
# ─────────────────────────────────────────────────────────────

def _purpose_bonus(
    purpose: str,
    day_b: int,
    life_b: int,
    natal_b: int,
    natal_wx: int,
    day_stem: int,
) -> tuple[int, str]:
    """
    根据用途计算附加得分。

    Returns
    -------
    (score_delta, description)
    """
    if purpose == "marriage":
        # 婚嫁：日支与命宫六合 extra bonus
        if life_b >= 0 and frozenset({day_b, life_b}) in _LIUHE:
            return 10, f"婚嫁吉：日支{BRANCHES[day_b]}与命宫六合（+10）"
        if life_b >= 0:
            for g in _SANHE:
                if day_b in g and life_b in g:
                    return 8, f"婚嫁吉：日支{BRANCHES[day_b]}与命宫三合（+8）"

    elif purpose == "business":
        # 商业/财务：日天干五行为 生我/同我 额外加成
        day_wx = _STEM_WX[day_stem]
        if day_wx == natal_wx or day_wx == _SHENG_ME[natal_wx]:
            return 10, f"财运吉：日天干五行生旺命主（+10）"

    elif purpose == "travel":
        # 出行：避冲 - 若日支冲命宫，已在主逻辑中计分，此处不重复；否则轻微加分于六合日
        if life_b >= 0 and frozenset({day_b, life_b}) in _LIUHE:
            return 8, f"出行吉：日支与命宫六合，宜动（+8）"

    elif purpose == "medical":
        # 求医：天德日已在 virtue 处理；此处对日天干为水（壬癸）有益
        day_wx = _STEM_WX[day_stem]
        if day_wx == 4:  # 水：主智慧与调养
            return 6, f"求医吉：壬癸水日，利养生调理（+6）"

    elif purpose == "move":
        # 搬家/入宅：避三煞（与年支特定三个地支）
        _sansha_map: dict[int, set[int]] = {
            # 年支→三煞地支集合（每个地支方位的三煞）
            2: {8, 9, 10},   # 寅年：申酉戌
            6: {4, 5, 6},    # 午年：辰巳午
            10: {0, 1, 11},  # 戌年：亥子丑
            3: {5, 6, 7},    # 卯年：巳午未
            7: {1, 2, 3},    # 未年：丑寅卯
            11: {9, 10, 11}, # 亥年：酉戌亥
            0: {2, 3, 4},    # 子年：寅卯辰
            4: {6, 7, 8},    # 辰年：午未申
            8: {10, 11, 0},  # 申年：戌亥子
            1: {3, 4, 5},    # 丑年：卯辰巳
            5: {7, 8, 9},    # 巳年：未申酉
            9: {11, 0, 1},   # 酉年：亥子丑
        }
        # 用年支（从 life_b 附近推导；此处简化：用 day_b）
        # 实际应传入 year_branch，但为简化 API 参数，用 natal_b 代替年支
        if natal_b >= 0:
            sha = _sansha_map.get(natal_b, set())
            if day_b in sha:
                return -12, f"搬迁不吉：日支{BRANCHES[day_b]}犯三煞（-12）"

    elif purpose == "career":
        # 事业：与官禄宫（命宫顺数8宫）三合加成
        if life_b >= 0:
            guan_b = (BRANCHES.index(BRANCHES[life_b]) + 8) % 12
            for g in _SANHE:
                if day_b in g and guan_b in g:
                    return 8, f"事业吉：日支与官禄宫三合（+8）"

    return 0, ""


# ─────────────────────────────────────────────────────────────
# 农历日期显示辅助
# ─────────────────────────────────────────────────────────────

_LUNAR_MONTH_ZH = ["", "正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
_LUNAR_DAY_ZH = [
    "", "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十",
]


def _lunar_day_str(l_month: int, l_day: int) -> str:
    """返回农历日期简要，如"三月初五"。"""
    m = abs(l_month)
    mz = _LUNAR_MONTH_ZH[m] if 1 <= m <= 12 else str(m)
    dz = _LUNAR_DAY_ZH[l_day] if 1 <= l_day <= 30 else str(l_day)
    prefix = "闰" if l_month < 0 else ""
    return f"{prefix}{mz}月{dz}"
