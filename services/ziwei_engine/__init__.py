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
    generate_palace_structured,
)
from .forecast import generate_forecast, ForecastResult
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
    xiaoxian_ages: list[int] = field(default_factory=list)  # 该宫小限所对应的年龄列表
    opposition_name: str = ""      # 对宫名称（+6宫）
    # N7.05 pyright: structured analysis fields (generate_palace_structured output)
    conclusion: str = ""
    explanation: str = ""
    suggestion: str = ""
    tooltip: str = ""


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

    # ── 命主/身主 ─────────────────────────────────────────────
    life_ruler_star: str = ""   # 命主（六星循环法）
    body_ruler_star: str = ""   # 身主（年支查表法）

    # ── 真太阳时 ─────────────────────────────────────────────
    true_solar_time: str = ""   # "" = 未修正；"HH:MM" = 已修正真太阳时
    # ── 运势预测 ───────────────────────────────────────────────
    forecast: Optional[ForecastResult] = None   # 年运+月运预测

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
    longitude: Optional[float] = None,
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
    import datetime as _dt
    if liunian_year is None:
        liunian_year = _dt.date.today().year

    # ── 真太阳时修正 ──────────────────────────────────────────
    _true_solar_time = ""
    _calc_hour, _calc_minute = hour, minute
    if longitude is not None:
        try:
            from services.bazi_engine.solar_time_v2 import apply_solar_correction
            _corrected = apply_solar_correction(
                _dt.datetime(year, month, day, hour, minute), longitude
            )
            _calc_hour   = _corrected.hour
            _calc_minute = _corrected.minute
            _true_solar_time = f"{_corrected.hour:02d}:{_corrected.minute:02d}"
        except Exception:
            pass

    # 1. 农历信息
    lunar = solar_to_lunar(year, month, day, _calc_hour, _calc_minute)

    # 2. 命宫/身宫/五行局
    layout = calc_palaces(lunar)

    lp_b  = layout.life_branch_idx    # 命宫地支
    lp_s  = layout.life_stem_idx      # 命宫天干
    bp_b  = layout.body_branch_idx    # 身宫地支

    # 3. 十四主星
    main_stars = place_main_stars(lunar.lunar_day, layout.wuxing_ju)

    # ── 命主/身主 ──────────────────────────────────────────────
    # 命主：贪狼宫起顺数到命宫，按六星周期 [贪狼巨门禄存文曲廉贞武曲] 定星
    _LIFE_RULER_CYCLE = ["贪狼", "巨门", "禄存", "文曲", "廉贞", "武曲"]
    # 身主：年支查表 子/午→火星 丑/未→天相 寅/申→天梁 卯/酉→天同 辰/戌→文昌 巳/亥→武曲
    _BODY_RULER_TABLE = [
        "火星", "天相", "天梁", "天同", "文昌", "武曲",
        "火星", "天相", "天梁", "天同", "文昌", "武曲",
    ]
    _tanlang_b = main_stars["贪狼"].branch_idx
    _life_steps = (lp_b - _tanlang_b) % 12
    _life_ruler = _LIFE_RULER_CYCLE[_life_steps % 6]
    _body_ruler = _BODY_RULER_TABLE[lunar.year_branch_idx]

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

    # ── 小限（每宫对应年龄列表，男顺女逆，由年支三合决定起宫）────────────
    # 三合火 寅午戌(2,6,10)：男起寅(2)，女起申(8)
    # 三合水 申子辰(8,0,4)：男起申(8)，女起寅(2)
    # 三合金 巳酉丑(5,9,1)：男起巳(5)，女起亥(11)
    # 三合木 亥卯未(11,3,7)：男起亥(11)，女起巳(5)
    _XIAOXIAN_GROUPS = [
        (frozenset([2, 6, 10]),  2,  8),
        (frozenset([8, 0, 4]),   8,  2),
        (frozenset([5, 9, 1]),   5, 11),
        (frozenset([11, 3, 7]), 11,  5),
    ]
    _is_male = gender.upper() in ("M", "男", "MALE")
    _xx_start = 2
    for _grp, _ms, _fs in _XIAOXIAN_GROUPS:
        if lunar.year_branch_idx in _grp:
            _xx_start = _ms if _is_male else _fs
            break
    _xx_dir = 1 if _is_male else -1
    _xx_by_branch: dict[int, list[int]] = {i: [] for i in range(12)}
    for _age in range(1, 121):
        _b = (_xx_start + (_age - 1) * _xx_dir) % 12
        _xx_by_branch[_b].append(_age)

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
            xiaoxian_ages=_xx_by_branch.get(b, []),
            opposition_name=PALACE_NAMES[(i + 6) % 12],
        )
        palaces_info.append(pa)

    # 8. 大运
    dayun = calc_dayun(lunar, gender, year, month, day)

    # ── 大运四化 + 博士十二流曜 ──────────────────────────────
    # 博士在大运干对应的禄存宫，阳干顺数，阴干逆数，共12曜
    # 四化解析同时纳入辅星（文昌文曲左辅右弼等可参与四化）
    _star_branches_map = {nm: pos.branch_idx for nm, pos in main_stars.items()}
    _star_branches_map.update({
        nm: b for nm, b in aux_stars.items()
        if not nm.endswith("placeholder")
    })
    _LUZUN_B = [2, 3, 5, 5, 7, 7, 8, 9, 11, 0]  # 甲乙丙丁戊己庚辛壬癸 禄存地支
    _BOSHI_12 = ["博士", "力士", "青龙", "小耗", "将军", "奏书",
                 "飞廉", "喜神", "病符", "大耗", "伏兵", "官府"]
    for _item in dayun.items:
        _item.sihua = apply_sihua(_star_branches_map, STEMS[_item.stem_idx])
        _luzun_b = _LUZUN_B[_item.stem_idx]
        _yang_dy = (_item.stem_idx % 2 == 0)
        _boshi: dict[str, str] = {}
        for _i, _sn in enumerate(_BOSHI_12):
            _bi = (_luzun_b + _i) % 12 if _yang_dy else (_luzun_b - _i) % 12
            _boshi[_sn] = BRANCHES[_bi]
        _item.boshi_stars = _boshi

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
        pa.conclusion, pa.explanation, pa.suggestion, pa.tooltip = \
            generate_palace_structured(pa.index, pa.branch_idx, main_stars, aux_stars)

    # 12. 流月列表
    branch_to_name = {pa.branch_idx: pa.name for pa in palaces_info}
    liuyue_data = calc_liuyue_list(liunian, branch_to_name)

    # 13. 先构建 chart，再计算运势预测（forecast 需要完整 chart 对象）
    chart = ZiweiChart(
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
        life_ruler_star=_life_ruler,
        body_ruler_star=_body_ruler,
        true_solar_time=_true_solar_time,
    )
    chart.forecast = generate_forecast(chart, liunian_year)
    return chart
