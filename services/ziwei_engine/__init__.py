"""
services/ziwei_engine/__init__.py — 紫微斗数引擎入口

公开接口：
  ziwei_full(year, month, day, hour, minute, gender) → ZiweiChart
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .analysis import (
    generate_full_analysis,
    generate_palace_analysis,
    generate_palace_structured,
    generate_palace_tags,
    generate_summary,
)
from .dayun import DayunResult, calc_dayun
from .decorative import place_changsheng12, place_jiangqian12, place_suiqian12
from .flying import FlyingStarChart, calc_flying
from .forecast import ForecastResult, generate_forecast
from .life_suggestions import LifeSuggestion, calc_life_suggestions
from .liunian import LiunianInfo, calc_liunian, calc_liuyue_list
from .lunar import LunarInfo, solar_to_lunar
from .palaces import PalaceLayout, calc_palaces
from .patterns import PatternResult, detect_patterns
from .remedies import RemedyResult, calc_remedies
from .stars_aux import place_aux_stars
from .stars_main import StarPosition, place_main_stars
from .tables import BRANCHES, PALACE_NAMES, WUHU_M1_STEM, get_aux_brightness
from .transforms import STEMS, apply_sihua, build_sihua_table

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
    dayun_boshi: list[str] = field(default_factory=list)  # 当前大运博士十二流曜（落在该宫的星名列表）
    changsheng: str = ""         # 长生十二神（本命盘固定星）
    jiangqian_star: str = ""     # 将前十二神（流年星）
    suiqian_star: str = ""       # 岁前十二神（流年星）

    @property
    def aux_names(self) -> frozenset[str]:
        """辅星名称集合，供成员查找和 set 运算使用。

        aux_stars 元素可以是 str（辅星名）或 dict（含 name 键）。
        """
        return frozenset(
            s if isinstance(s, str) else s["name"]
            for s in self.aux_stars
        )


@dataclass
class ZiweiChart:
    """完整紫微命盘。"""
    # ── 基本信息 ──────────────────────────────────────────────
    birth_solar: str        # 公历生日（ISO格式）
    gender: str
    lunar: LunarInfo
    palaces: list[PalaceInfo]
    life_palace_branch: int
    life_palace_stem_idx: int
    life_palace_gz: str      # 干支
    body_palace_branch: int
    body_palace_gz: str
    wuxing_ju: int           # 五行局数
    wuxing_ju_name: str      # 水二局/木三局/…
    dayun: DayunResult
    body_palace_branch_name: str = ""  # 身宫地支汉字

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
    laiyin_palace: str = ""     # 来因宫：生年天干所在宫位

    # ── 真太阳时 ─────────────────────────────────────────────
    true_solar_time: str = ""   # "" = 未修正；"HH:MM" = 已修正真太阳时

    # ── 运势预测 ───────────────────────────────────────────────
    forecast: Optional[ForecastResult] = None   # 年运+月运预测

    # ── 格局检测 ───────────────────────────────────────────────
    patterns: list[PatternResult] = field(default_factory=list)

    # ── 破局建议 ───────────────────────────────────────────────
    remedies: list[RemedyResult] = field(default_factory=list)

    # ── 生活化建议 ─────────────────────────────────────────────
    life_suggestions: list[LifeSuggestion] = field(default_factory=list)
# 宫干序列（从命宫天干顺数十二宫）
# ──────────────────────────────────────────────────────────────
def _palace_stems_list(year_stem_idx: int, life_branch_idx: int) -> list[int]:
    """根据年干五虎遁和各宫地支计算十二宫天干序列。

    每个宫位的天干由其地支通过五虎遁公式决定：
      stem = (寅位天干 + (地支 - 寅) mod 12) mod 10
    """
    wuhu_base = WUHU_M1_STEM[year_stem_idx]
    stems: list[int] = []
    for i in range(12):
        branch = (life_branch_idx - i) % 12
        stem = (wuhu_base + (branch - 2 + 12) % 12) % 10
        stems.append(stem)
    return stems


# ── O4: ziwei_full() TTL 缓存 ────────────────────────────────────────
import hashlib as _hashlib
import threading as _threading

from cachetools import TTLCache as _TTLCache

_ZIWEI_CACHE: _TTLCache = _TTLCache(maxsize=200, ttl=3600)
_ZIWEI_CACHE_LOCK = _threading.Lock()


def clear_ziwei_cache() -> None:
    """清空紫微计算缓存（代码更新或算法切换后调用）。"""
    with _ZIWEI_CACHE_LOCK:
        _ZIWEI_CACHE.clear()


def _ziwei_cache_key(
    year: int, month: int, day: int,
    hour: int, minute: int, gender: str,
    liunian_year: "int | None", longitude: "float | None",
    late_zishi: bool,
    sihua_stem_indices: "dict[str, int] | None",
    leap_month_method: str,
    kuiyue_method: str,
    tianma_method: str,
    tiankong_method: str,
    brightness_method: str,
    jiukong_method: str,
    tianshang_method: str,
    mingzhu_method: str,
    liunian_sihua_method: str,
    changsheng_method: str,
) -> str:
    si_str = str(sorted(sihua_stem_indices.items())) if sihua_stem_indices else ""
    raw = (
        f"{year}|{month}|{day}|{hour}|{minute}|{gender}|{liunian_year}|{longitude}"
        f"|{late_zishi}|{si_str}|{leap_month_method}|{kuiyue_method}"
        f"|{tianma_method}|{tiankong_method}|{brightness_method}|{jiukong_method}"
        f"|{tianshang_method}|{mingzhu_method}|{liunian_sihua_method}|{changsheng_method}"
    )
    return _hashlib.sha256(raw.encode()).hexdigest()


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
    # ── 算法设置 ──────────────────────────────────────────────
    late_zishi: bool = True,
    sihua_stem_indices: "Optional[dict[str, int]]" = None,
    leap_month_method: str = "mid",
    kuiyue_method: str = "standard",
    # ── A1-A8 新增安星方法 ────────────────────────────────────
    tianma_method: str = "year",           # 天马：year(年支)/month(月支)
    tiankong_method: str = "standard",     # 天空：standard/shun(顺加生时)
    brightness_method: str = "standard",   # 亮度：standard/zhongzhou/mod1/mod2
    jiukong_method: str = "dual",          # 截空旬空：dual/single/zhanyan
    tianshang_method: str = "standard",    # 天使天伤：standard/zhongzhou
    mingzhu_method: str = "quanshu",       # 命主：quanshu/zhongzhou
    liunian_sihua_method: str = "year_stem",  # 流年四化：year_stem/life_palace_stem
    changsheng_method: str = "standard",   # 长生十二神：standard/water_earth/fire_earth
) -> ZiweiChart:
    """
    计算完整紫微斗数命盘。

    参数：
      year, month, day    : 公历出生日期
      hour, minute        : 24小时制出生时间
      gender              : "男" / "女"
      liunian_year        : 流年（默认为当年）
      late_zishi          : 晚子时(23:00~00:00)视为次日（默认True）
      sihua_stem_indices  : 四化表流派，{天干: 方案索引}，缺省=标准
      leap_month_method   : 闰月处理 'mid'(默认)/,'next','same'
      kuiyue_method       : 天魁天钺安法（默认'standard'=六辛逢虎马）
      tianma_method       : 天马安法 year/month
      tiankong_method     : 天空安法 standard/shun
      brightness_method   : 亮度流派 standard/zhongzhou/mod1/mod2
      jiukong_method      : 截空旬空安法 dual/single/zhanyan
      tianshang_method    : 天使天伤安法 standard/zhongzhou
      mingzhu_method      : 命主安法 quanshu/zhongzhou
      liunian_sihua_method: 流年四化来源 year_stem/life_palace_stem
      changsheng_method   : 长生十二神安法 standard/water_earth/fire_earth

    返回 ZiweiChart 数据对象。
    """
    import datetime as _dt
    from zoneinfo import ZoneInfo as _ZI
    if liunian_year is None:
        liunian_year = _dt.datetime.now(_ZI("Asia/Shanghai")).year
    # O4: TTL 缓存检查
    _ck = _ziwei_cache_key(year, month, day, hour, minute, gender, liunian_year, longitude,
                           late_zishi, sihua_stem_indices, leap_month_method, kuiyue_method,
                           tianma_method, tiankong_method, brightness_method, jiukong_method,
                           tianshang_method, mingzhu_method, liunian_sihua_method, changsheng_method)
    with _ZIWEI_CACHE_LOCK:
        if _ck in _ZIWEI_CACHE:
            return _ZIWEI_CACHE[_ck]

    # ── 晚子时处理 ─────────────────────────────────────────────
    # 若 late_zishi=True 且出生时间在 23:00~23:59，日期进为次日
    _calc_year, _calc_month, _calc_day = year, month, day
    if late_zishi and hour == 23:
        _next_day = _dt.date(year, month, day) + _dt.timedelta(days=1)
        _calc_year, _calc_month, _calc_day = _next_day.year, _next_day.month, _next_day.day
    # ── 真太阳时修正 ──────────────────────────────────────────
    _true_solar_time = ""
    _apply_hour, _apply_minute = hour, minute
    if longitude is not None:
        try:
            from services.bazi_engine.solar_time_v2 import apply_solar_correction
            _corrected = apply_solar_correction(
                _dt.datetime(_calc_year, _calc_month, _calc_day, hour, minute), longitude
            )
            _apply_hour   = _corrected.hour
            _apply_minute = _corrected.minute
            _true_solar_time = f"{_corrected.hour:02d}:{_corrected.minute:02d}"
        except Exception:
            pass

    # 四化表：构建（支持per-stem方案覆盖）
    _sihua_table = build_sihua_table(sihua_stem_indices)

    # 1. 农历信息（传入 leap_month_method 及晚子时修正后的日期）
    lunar = solar_to_lunar(_calc_year, _calc_month, _calc_day,
                           _apply_hour, _apply_minute,
                           leap_month_method=leap_month_method)

    # 2. 命宫/身宫/五行局
    layout = calc_palaces(lunar)

    lp_b  = layout.life_branch_idx    # 命宫地支
    lp_s  = layout.life_stem_idx      # 命宫天干
    bp_b  = layout.body_branch_idx    # 身宫地支

    # 3. 十四主星（传入亮度流派）
    main_stars = place_main_stars(lunar.lunar_day, layout.wuxing_ju, brightness_method)

    # ── 命主/身主 ──────────────────────────────────────────────
    # 命主安法两种：
    #   quanshu (全书): 贪狼宫起顺数到命宫，按六星循环定星
    #   zhongzhou (中州): 年支查固定表
    _LIFE_RULER_CYCLE = ["贪狼", "巨门", "禄存", "文曲", "廉贞", "武曲"]
    _MINGZHU_ZHONGZHOU = [
        "贪狼", "巨门", "天相", "天梁", "七杀", "天同",
        "武曲", "太阳", "破军", "廉贞", "紫微", "天机",
    ]  # 子→贪狼,丑→巨门,寅→天相,卯→天梁,辰→七杀,巳→天同
       # 午→武曲,未→太阳,申→破军,酉→廉贞,戌→紫微,亥→天机
    # 身主：年支查表 子/午→火星 丑/未→天相 寅/申→天梁 卯/酉→天同 辰/戌→文昌 巳/亥→武曲
    _BODY_RULER_TABLE = [
        "火星", "天相", "天梁", "天同", "文昌", "武曲",
        "火星", "天相", "天梁", "天同", "文昌", "武曲",
    ]
    _tanlang_b = main_stars["贪狼"].branch_idx
    _life_steps = (lp_b - _tanlang_b) % 12
    if mingzhu_method == "zhongzhou":
        _life_ruler = _MINGZHU_ZHONGZHOU[lunar.year_branch_idx]
    else:
        _life_ruler = _LIFE_RULER_CYCLE[_life_steps % 6]
    _body_ruler = _BODY_RULER_TABLE[lunar.year_branch_idx]

    # 4. 辅星/杂曜（传入所有安星方法参数）
    aux_stars = place_aux_stars(
        lunar,
        lp_b=lp_b,
        kuiyue_method=kuiyue_method,
        tianma_method=tianma_method,
        tiankong_method=tiankong_method,
        jiukong_method=jiukong_method,
        tianshang_method=tianshang_method,
    )

    # 补充天才（命宫同支）
    aux_stars["天才"] = lp_b
    del aux_stars["天才_placeholder"]

    # 5. 本命四化（年干）
    year_sihua = apply_sihua(
        {name: pos.branch_idx for name, pos in main_stars.items()},
        STEMS[lunar.year_stem_idx],
        sihua_table=_sihua_table,
    )
    # 将四化信息写入主星
    for star_name, hua_text in year_sihua.items():
        if star_name in main_stars:
            main_stars[star_name].transforms.append(hua_text)

    # 6. 宫干序列
    pal_stems = _palace_stems_list(lunar.year_stem_idx, lp_b)

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
        # 该宫内辅星（排除占位键），附带亮度数据
        ax_list = []
        for _aux_name, _aux_b in aux_stars.items():
            if _aux_b == b and not _aux_name.endswith("placeholder"):
                _bv, _bn = get_aux_brightness(_aux_name, b)
                ax_list.append({
                    "name": _aux_name,
                    "brightness": _bn,
                    "brightness_val": _bv,
                    "transforms": [],
                })

        # 宫干四化（飞出）（对应飞星体系）
        pal_sihua = apply_sihua(
            {name: pos.branch_idx for name, pos in main_stars.items()},
            STEMS[s],
            sihua_table=_sihua_table,
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

    # 来因宫：生年天干所在宫位（宫干天干与年干相同的宫位）
    _laiyin_palace_name = ""
    for _pa in palaces_info:
        if _pa.stem_idx == lunar.year_stem_idx:
            _laiyin_palace_name = _pa.name
            break

    # 8. 大运
    dayun = calc_dayun(lunar, gender, year, month, day,
                       birth_hour=hour, birth_minute=minute,
                       wuxing_ju=layout.wuxing_ju,
                       life_branch_idx=lp_b,
                       life_stem_idx=lp_s)

    # ── 大运四化 + 博士十二流曜 ──────────────────────────────
    # 博士在大运干对应的禄存宫，阳干顺数，阴干逆数，共12曜
    # 四化解析同时纳入辅星（文昌文曲左辅右弼等可参与四化）
    _star_branches_map = {nm: pos.branch_idx for nm, pos in main_stars.items()}
    _star_branches_map.update({
        nm: b for nm, b in aux_stars.items()
        if not nm.endswith("placeholder")
    })
    _LUZUN_B = [2, 3, 5, 6, 5, 6, 8, 9, 11, 0]  # 甲乙丙丁戊己庚辛壬癸 禄存地支（丁→午6，戊→巳5，己→午6）
    _BOSHI_12 = ["博士", "力士", "青龙", "小耗", "将军", "奏书",
                 "飞廉", "喜神", "病符", "大耗", "伏兵", "官府"]
    for _item in dayun.items:
        _item.sihua = apply_sihua(_star_branches_map, STEMS[_item.stem_idx], sihua_table=_sihua_table)
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
    # liunian_sihua_method:
    #   "year_stem"        使用流年天干（默认）
    #   "life_palace_stem" 使用流年命宫天干（命宫落到哪宫就用该宫的宫干）
    if liunian_sihua_method == "life_palace_stem":
        # 找流年命宫所在宫位的宫干
        _ln_lp_stem_idx = liunian.year_stem_idx  # fallback
        for _pa in palaces_info:
            if _pa.branch_idx == liunian.life_palace_branch:
                _ln_lp_stem_idx = _pa.stem_idx
                break
        _ln_stem_name = STEMS[_ln_lp_stem_idx]
    else:
        _ln_stem_name = STEMS[liunian.year_stem_idx]
    # 使用 apply_sihua 过滤，仅纳入命盘实际存在的星（_star_branches_map 已含主星+辅星）
    liunian.sihua = apply_sihua(_star_branches_map, _ln_stem_name, sihua_table=_sihua_table)

    # 10. 飞星盘
    all_branches = {name: pos.branch_idx for name, pos in main_stars.items()}
    all_branches.update(aux_stars)
    flying = calc_flying(lp_b, lp_s, all_branches)

    # 自化方向注解：为星曜 transforms 添加 ↓（离心自化）和 ↑（向心自化）标记
    _b2palace_local = {pa.branch_idx: pa for pa in palaces_info}
    for _fly_p in flying.palaces:
        _this_pa_local = _b2palace_local[_fly_p.branch_idx]
        _sihua_this_local = _sihua_table.get(_fly_p.stem_name, {})
        # 离心自化 ↓: 本宫宫干飞化的星落回本宫
        for _hua_t_l, _tstar_l in _sihua_this_local.items():
            _tb_l = _star_branches_map.get(_tstar_l)
            if _tb_l is not None and _tb_l == _fly_p.branch_idx:
                for _s in _this_pa_local.main_stars + _this_pa_local.aux_stars:
                    if _s["name"] == _tstar_l and f"↓化{_hua_t_l}" not in _s["transforms"]:
                        _s["transforms"].append(f"↓化{_hua_t_l}")
        # 向心自化 ↑: 对宫宫干飞化的星落入本宫
        _opp_fly_local = flying.palaces[(_fly_p.palace_idx + 6) % 12]
        _sihua_opp_local = _sihua_table.get(_opp_fly_local.stem_name, {})
        for _hua_t_l, _tstar_l in _sihua_opp_local.items():
            _tb_l = _star_branches_map.get(_tstar_l)
            if _tb_l is not None and _tb_l == _fly_p.branch_idx:
                for _s in _this_pa_local.main_stars + _this_pa_local.aux_stars:
                    if _s["name"] == _tstar_l and f"↑化{_hua_t_l}" not in _s["transforms"]:
                        _s["transforms"].append(f"↑化{_hua_t_l}")

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

    # ── 博士十二流曜宫格化：找当前大运，分配博士星至各宫 ───────────────
    _current_age = liunian_year - year + 1  # 流年对应虚岁（近似）
    _current_dayun_item = None
    for _di in dayun.items:
        if _di.start_age <= _current_age < _di.start_age + 10:
            _current_dayun_item = _di
            break
    if _current_dayun_item is None and dayun.items:
        # 流年超过所有大运：用最后一柱
        if _current_age >= dayun.items[-1].start_age:
            _current_dayun_item = dayun.items[-1]
        # else: 起运前，不分配
    if _current_dayun_item is not None:
        for _pa in palaces_info:
            _pa.dayun_boshi = [
                _sn for _sn, _b_name in _current_dayun_item.boshi_stars.items()
                if _b_name == BRANCHES[_pa.branch_idx]
            ]

    # 11b. 三套十二神：长生十二神（本命固定）+ 将前/岁前十二神（流年）
    _changsheng12_map = place_changsheng12(
        layout.wuxing_ju, gender, lunar.year_branch_idx,
        changsheng_method=changsheng_method,
    )
    _liunian_b = liunian.year_branch_idx if liunian is not None else lunar.year_branch_idx
    _jiangqian12_map = place_jiangqian12(_liunian_b)
    _suiqian12_map = place_suiqian12(_liunian_b)
    for _pa in palaces_info:
        _pa.changsheng = _changsheng12_map.get(_pa.branch_idx, "")
        _pa.jiangqian_star = _jiangqian12_map.get(_pa.branch_idx, "")
        _pa.suiqian_star = _suiqian12_map.get(_pa.branch_idx, "")

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
        body_palace_branch_name=BRANCHES[bp_b],
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
        laiyin_palace=_laiyin_palace_name,
    )
    chart.forecast = generate_forecast(chart, liunian_year)
    chart.patterns = detect_patterns(palaces_info)
    chart.remedies = calc_remedies(chart)
    chart.life_suggestions = calc_life_suggestions(chart)
    # O4: 写入缓存
    with _ZIWEI_CACHE_LOCK:
        _ZIWEI_CACHE[_ck] = chart
    return chart
