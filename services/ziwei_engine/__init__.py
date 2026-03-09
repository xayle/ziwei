"""
services/ziwei_engine/__init__.py — 紫微斗数引擎入口

公开接口：
  ziwei_full(year, month, day, hour, minute, gender) → ZiweiChart
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .lunar import solar_to_lunar, LunarInfo
from .palaces import calc_palaces, PalaceLayout
from .stars_main import place_main_stars, StarPosition
from .stars_aux import place_aux_stars
from .transforms import apply_sihua, STEMS
from .dayun import calc_dayun, DayunResult
from .liunian import calc_liunian, LiunianInfo, calc_liuyue_list
from .flying import calc_flying, FlyingStarChart
from .analysis import (
    generate_palace_analysis,
    generate_palace_tags,
    generate_full_analysis,
    generate_summary,
)
from .tables import PALACE_NAMES, BRANCHES


# ──────────────────────────────────────────────────────────────
# 数据结构
# ──────────────────────────────────────────────────────────────

@dataclass
class PalaceInfo:
    """一个宫位的完整信息。"""
    index: int               # 0=命宫，1=兄弟宫，…，11=父母宫
    name: str                # 宫位名称
    branch_idx: int          # 地支索引
    branch: str              # 地支文字
    stem_idx: int            # 宫干天干索引
    stem: str                # 宫干天干文字
    main_stars: list[dict]   # [{name, brightness, brightness_val, transforms}]
    aux_stars: list[str]     # 辅星/杂曜名称列表
    flying_out: dict[str, str] = field(default_factory=dict)
    analysis: str = ""
    analysis_tags: list[str] = field(default_factory=list)


@dataclass
class ZiweiChart:
    """完整紫微命盘。"""
    # ── 基本信息 ──────────────────────────────────────────────
    birth_solar: str        # 公历生日（ISO格式）
    gender: str

    # ── 农历信息 ──────────────────────────────────────────────
    lunar: LunarInfo

    # ── 命盘格局 ──────────────────────────────────────────────
    palaces: list[PalaceInfo]

    # 命宫/身宫
    life_palace_branch: int
    life_palace_stem_idx: int
    life_palace_gz: str      # 干支
    body_palace_branch: int
    body_palace_gz: str
    wuxing_ju: int           # 五行局数
    wuxing_ju_name: str      # 水二局/木三局/…

    # ── 大运 ──────────────────────────────────────────────────
    dayun: DayunResult

    # ── 流年（默认当年）────────────────────────────────────────
    liunian: Optional[LiunianInfo] = None

    # ── 飞星盘 ────────────────────────────────────────────────
    flying: Optional[FlyingStarChart] = None

    # ── 流月列表（12项） ──────────────────────────────────────
    liuyue_data: list[dict] = field(default_factory=list)

    # ── 文字摘要 ─────────────────────────────────────────────
    summary: str = ""
    analysis: dict[str, str] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────
# 宫干序列（从命宫天干顺数十二宫）
# ──────────────────────────────────────────────────────────────
def _palace_stems_list(life_stem_idx: int) -> list[int]:
    return [(life_stem_idx + i) % 10 for i in range(12)]


# ──────────────────────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────────────────────
def ziwei_full(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    gender: str,
    liunian_year: Optional[int] = None,
) -> ZiweiChart:
    """
    计算完整紫微斗数命盘。

    参数：
      year, month, day : 公历出生日期
      hour, minute     : 24小时制出生时间
      gender           : "男" / "女"
      liunian_year     : 流年（默认为当年）

    返回 ZiweiChart 数据对象。
    """
    import datetime
    if liunian_year is None:
        liunian_year = datetime.date.today().year

    # 1. 农历信息
    lunar = solar_to_lunar(year, month, day, hour, minute)

    # 2. 命宫/身宫/五行局
    layout = calc_palaces(lunar)

    lp_b  = layout.life_branch_idx    # 命宫地支
    lp_s  = layout.life_stem_idx      # 命宫天干
    bp_b  = layout.body_branch_idx    # 身宫地支

    # 3. 十四主星
    main_stars = place_main_stars(lunar.lunar_day, layout.wuxing_ju)

    # 4. 辅星/杂曜
    aux_stars = place_aux_stars(lunar)

    # 补充天才（命宫同支）
    aux_stars["天才"] = lp_b
    del aux_stars["天才_placeholder"]

    # 5. 本命四化（年干）
    year_sihua = apply_sihua(
        {name: pos.branch_idx for name, pos in main_stars.items()},
        STEMS[lunar.year_stem_idx],
    )
    # 将四化信息写入主星
    for star_name, hua_text in year_sihua.items():
        if star_name in main_stars:
            main_stars[star_name].transforms.append(hua_text)

    # 6. 宫干序列
    pal_stems = _palace_stems_list(lp_s)

    # 7. 构建12宫信息
    palaces_info: list[PalaceInfo] = []
    for i in range(12):
        b = (lp_b - i) % 12          # 该宫地支索引
        s = pal_stems[i]              # 该宫天干

        # 该宫内主星
        ms_list = [
            {
                "name": pos.name,
                "brightness": pos.brightness,
                "brightness_val": pos.brightness_val,
                "transforms": pos.transforms[:],
            }
            for pos in main_stars.values()
            if pos.branch_idx == b
        ]
        # 该宫内辅星（排除占位键）
        ax_list = [
            name for name, ab in aux_stars.items()
            if ab == b and not name.endswith("placeholder")
        ]

        # 宫干四化（飞出）（对应飞星体系）
        pal_sihua = apply_sihua(
            {name: pos.branch_idx for name, pos in main_stars.items()},
            STEMS[s],
        )
        fly_out = {star: f"化{hua.replace('化','')}" for star, hua in pal_sihua.items()}

        pa = PalaceInfo(
            index=i,
            name=PALACE_NAMES[i],
            branch_idx=b,
            branch=BRANCHES[b],
            stem_idx=s,
            stem=STEMS[s],
            main_stars=ms_list,
            aux_stars=ax_list,
            flying_out=fly_out,
        )
        palaces_info.append(pa)

    # 8. 大运
    dayun = calc_dayun(lunar, gender, year, month, day)

    # 9. 流年
    liunian = calc_liunian(liunian_year, year, lp_b)
    # 流年四化追加到流年对象
    from .transforms import SIHUA_TABLE
    ln_sihua_raw = SIHUA_TABLE.get(STEMS[liunian.year_stem_idx], {})
    liunian.sihua = {star: f"化{hua}" for hua, star in ln_sihua_raw.items()}

    # 10. 飞星盘
    all_branches = {name: pos.branch_idx for name, pos in main_stars.items()}
    all_branches.update(aux_stars)
    flying = calc_flying(lp_b, lp_s, all_branches)

    # 11. 宫位解读
    analysis_texts = generate_full_analysis(
        main_stars, aux_stars,
        lp_b, STEMS[lp_s] + BRANCHES[lp_b],
        bp_b, layout.wuxing_ju, layout.wuxing_ju_name,
        gender,
    )
    summary = generate_summary(main_stars, aux_stars, lp_b)

    # 写入宫位解读 + 标签
    for pa in palaces_info:
        pa.analysis = analysis_texts.get(pa.name, "")
        pa.analysis_tags = generate_palace_tags(pa.branch_idx, main_stars, aux_stars)

    # 12. 流月列表
    branch_to_name = {pa.branch_idx: pa.name for pa in palaces_info}
    liuyue_data = calc_liuyue_list(liunian, branch_to_name)

    return ZiweiChart(
        birth_solar=f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}",
        gender=gender,
        lunar=lunar,
        palaces=palaces_info,
        life_palace_branch=lp_b,
        life_palace_stem_idx=lp_s,
        life_palace_gz=layout.life_ganzhi,
        body_palace_branch=bp_b,
        body_palace_gz=layout.body_ganzhi,
        wuxing_ju=layout.wuxing_ju,
        wuxing_ju_name=layout.wuxing_ju_name,
        dayun=dayun,
        liunian=liunian,
        flying=flying,
        liuyue_data=liuyue_data,
        summary=summary,
        analysis=analysis_texts,
    )
