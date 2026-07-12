"""
services/ziwei_engine/stars_aux.py — 辅星/杂曜布局

来源：《紫微斗数全书》诸星安法
"""

from __future__ import annotations

from .lunar import LunarInfo

# ─────────────────────────────────────────────────────────────────────────────
# 天魁天钺安法表（多流派）
# ─────────────────────────────────────────────────────────────────────────────
# 方法说明（按年干查魁/钺落支索引）：
#   standard / liuxin_huima   = 六辛逢虎马（默认，《全书》）
#     甲戊庚→魁丑(1)钺未(7)  乙己→魁子(0)钺申(8)  丙丁→魁亥(11)钺酉(9)
#     壬癸→魁卯(3)钺巳(5)    辛→魁午(6)钺寅(2)
#   gengxin_mahu              = 庚辛逢马虎
#     同standard，但庚辛同组→魁午(6)钺寅(2)
#   gengxin_huima             = 庚辛逢虎马
#     同standard，但庚辛同组→魁寅(2)钺午(6)  NB:虎=寅,马=午
#   liuxin_mahu               = 六辛逢马虎
#     同standard，但辛→魁寅(2)钺午(6)（虎马互换）
# ─────────────────────────────────────────────────────────────────────────────
_KUIYUE_TABLES: dict[str, tuple[list[int], list[int]]] = {
    # (天魁表[10], 天钺表[10])  索引 = 年天干(甲=0…癸=9)
    # 六辛逢虎马（标准, 《紫微斗数全书》）
    "standard": ([1, 0, 11, 11, 1, 0, 1, 6, 3, 3], [7, 8, 9, 9, 7, 8, 7, 2, 5, 5]),
    # 庚辛逢马虎 — 庚辛同属马虎组：魁午(6), 钺寅(2)
    "gengxin_mahu": ([1, 0, 11, 11, 1, 0, 6, 6, 3, 3], [7, 8, 9, 9, 7, 8, 2, 2, 5, 5]),
    # 庚辛逢虎马 — 庚辛同属虎马组：魁寅(2), 钺午(6)
    "gengxin_huima": ([1, 0, 11, 11, 1, 0, 2, 2, 3, 3], [7, 8, 9, 9, 7, 8, 6, 6, 5, 5]),
    # 六辛逢马虎 — 辛单独但虎马互换：魁寅(2), 钺午(6)
    "liuxin_mahu": ([1, 0, 11, 11, 1, 0, 1, 2, 3, 3], [7, 8, 9, 9, 7, 8, 7, 6, 5, 5]),
}


def place_aux_stars(
    info: LunarInfo,
    lp_b: int = 0,
    kuiyue_method: str = "standard",
    tianma_method: str = "year",
    tiankong_method: str = "standard",
    jiukong_method: str = "dual",
    tianshang_method: str = "standard",
    wenchang_method: str = "hour",
    youbi_method: str = "month",
) -> dict[str, int]:
    """
    布局辅星/杂曜，返回 {星名: branch_idx}。

    参数：
        info              : LunarInfo
        lp_b              : 命宫地支索引（供天使天伤使用）
        kuiyue_method     : 天魁天钺安法
            "standard"      六辛逢虎马（默认，《全书》）
            "gengxin_mahu"  庚辛逢马虎
            "gengxin_huima" 庚辛逢虎马
            "liuxin_mahu"   六辛逢马虎
        tianma_method     : 天马安法
            "year"   依据年支（默认，三合查表）
            "month"  依据月支（同查表但以月支为准）
        tiankong_method   : 天空安法
            "standard"  常规排法：戌(10)起子年顺 → (10+yb)%12
            "shun"      顺加生时 → (yb+hb)%12
        jiukong_method    : 截空旬空安法
            "dual"      正副双星法（默认，返回截空1+截空2）
            "single"    常规单星法（仅返回截空，挑主空亡一支）
            "zhanyan"   占验派排法（截路空亡：以时支双支推算）
        tianshang_method  : 天使天伤安法
            "standard"  常规：天伤=迁移宫支，天使=疾厄宫支
            "zhongzhou" 中州派：天伤=交友宫支，天使=父母宫支

    ── 六吉星 ──
    文昌/文曲：默认按时辰（戌起子时逆/辰起子时顺）
    天魁/天钺：年干查表
    左辅：农历月（辰起正月顺）
    右弼：默认按月（戌起正月逆）；legacy 按时辰

    ── 六煞星 ──
    擎羊：年干 → 查表（禄前一位）
    陀罗：年干 → 查表（禄后一位）
    火星：年支安法 + 时支（双变量）→ 查表
    铃星：年支安法 + 时支（双变量）→ 查表
    地空：时支安法  地空 = (12 - hour_branch) % 12  (亥起子时，逆)
    地劫：时支安法  地劫 = hour_branch              (亥(11)+1=子? 从亥起子时顺)
          实际：亥(11)起子时顺布
          地劫 = (11 + hour_branch) % 12  → 子时=11=亥?
          经典：地空亥起子时逆，地劫亥起子时顺
          地空 = (11 - hour_branch + 12) % 12
          地劫 = (11 + hour_branch) % 12

    ── 杂曜 ──
    禄存：年干 → 查表
    天马：年支/月支 → 三合查表（寅申巳亥 四马之地的轮转）
    天空：年支/时支 → 方法决定
    天官：年干 → 查表
    天福：年干 → 查表
    天厨：年干 → 查表
    红鸾：年支 → 卯(3)起子年逆数  红鸾 = (3 - year_branch + 12) % 12
    天喜：年支 → 酉(9)起子年逆数  天喜 = (9 - year_branch + 12) % 12
    截空：旬空两支（正副双星法）或单星法或占验截路空亡
    天伤：命宫对宫（迁移宫支）
    天使：疾厄宫支
    """
    ys = info.year_stem_idx  # 年天干 甲=0
    yb = info.year_branch_idx  # 年地支 子=0
    m = info.calc_lunar_month  # 计算用月份（闰月已+1），左辅布局使用
    hb = info.hour_branch_idx  # 子=0

    result: dict[str, int] = {}

    # ──── 六吉星 ────────────────────────────────────────
    if wenchang_method == "hour":
        # 子时戌上起文昌逆，辰上起文曲顺
        result["文昌"] = (10 - hb) % 12
        result["文曲"] = (4 + hb) % 12
    else:
        # legacy: 年支安法
        result["文昌"] = (9 - yb) % 12
        result["文曲"] = (4 + yb) % 12

    # 天魁天钺：年干查表（依安法）
    _kui_tbl, _yue_tbl = _KUIYUE_TABLES.get(kuiyue_method, _KUIYUE_TABLES["standard"])
    result["天魁"] = _kui_tbl[ys]
    result["天钺"] = _yue_tbl[ys]

    # 左辅：辰(4)起正月，顺数 → 左辅 = (3 + m) % 12
    result["左辅"] = (3 + m) % 12

    if youbi_method == "month":
        # 戌(10)起正月逆数
        result["右弼"] = (10 - m + 12) % 12
    else:
        # legacy: 戌起子时逆数
        result["右弼"] = (10 - hb) % 12

    # ──── 六煞星 ────────────────────────────────────────
    # 禄存/擎羊/陀罗查表（年干）
    # 禄存所在地支：甲寅乙卯丙戊巳丁己午庚申辛酉壬亥癸子
    LUZUN_TABLE: list[int] = [2, 3, 5, 6, 5, 6, 8, 9, 11, 0]  # 甲寅乙卯丙巳丁午戊巳己午庚申辛酉壬亥癸子
    luzun_b = LUZUN_TABLE[ys]
    result["禄存"] = luzun_b
    result["擎羊"] = (luzun_b + 1) % 12  # 禄前一位
    result["陀罗"] = (luzun_b - 1) % 12  # 禄后一位

    # 火星：年支+时支双变量查表
    # 来源：《斗数宣微》火星铃星安法
    # 行1: 年支 寅午戌 → 丑(1)起子时顺
    # 行2: 年支 申子辰 → 寅(2)起子时顺
    # 行3: 年支 巳酉丑 → 卯(3)起子时顺
    # 行4: 年支 亥卯未 → 酉(9)起子时顺
    HUOXING_BASE: dict[tuple[int, ...], int] = {
        (2, 6, 10): 1,  # 寅午戌 → 丑起
        (8, 0, 4): 2,  # 申子辰 → 寅起
        (5, 9, 1): 3,  # 巳酉丑 → 卯起
        (11, 3, 7): 9,  # 亥卯未 → 酉起
    }
    huo_base = 2  # 默认
    for grp, base in HUOXING_BASE.items():
        if yb in grp:
            huo_base = base
            break
    result["火星"] = (huo_base + hb) % 12

    # 铃星：年支+时支
    # 行1: 年支 寅午戌 → 卯(3)起子时顺
    # 行2: 年支 申子辰 → 戌(10)起子时顺
    # 行3: 年支 巳酉丑 → 戌(10)起子时顺 (分歧，取通行版)
    # 行4: 年支 亥卯未 → 戌(10)起子时顺
    LINGXING_BASE: dict[tuple[int, ...], int] = {
        (2, 6, 10): 3,  # 寅午戌 → 卯起
        (8, 0, 4): 10,  # 申子辰 → 戌起
        (5, 9, 1): 10,  # 巳酉丑 → 戌起
        (11, 3, 7): 10,  # 亥卯未 → 戌起
    }
    ling_base = 10
    for grp, base in LINGXING_BASE.items():
        if yb in grp:
            ling_base = base
            break
    result["铃星"] = (ling_base + hb) % 12

    # 地空：亥(11)起子时逆 → 地空 = (11 - hb) % 12
    result["地空"] = (11 - hb) % 12

    # 地劫：亥(11)起子时顺 → 地劫 = (11 + hb) % 12
    result["地劫"] = (11 + hb) % 12

    # ──── 杂曜 ────────────────────────────────────────────
    # 天马：三合查表（申子辰→寅, 寅午戌→申, 巳酉丑→亥, 亥卯未→巳）
    # tianma_method = "year"（依据年支，默认）/ "month"（依据月支）
    TIANMA_BY_BRANCH: dict[tuple[int, ...], int] = {
        (8, 0, 4): 2,  # 申子辰 → 寅(2)
        (2, 6, 10): 8,  # 寅午戌 → 申(8)
        (5, 9, 1): 11,  # 巳酉丑 → 亥(11)
        (11, 3, 7): 5,  # 亥卯未 → 巳(5)
    }
    if tianma_method == "month":
        # 月支索引：正月=寅(2), 二月=卯(3), …, 十二月=丑(1)
        _mb = (m + 1) % 12  # 正月(1)→寅(2), 二月(2)→卯(3) …
        tianma_b = 2
        for grp, base in TIANMA_BY_BRANCH.items():
            if _mb in grp:
                tianma_b = base
                break
    else:
        tianma_b = 2
        for grp, base in TIANMA_BY_BRANCH.items():
            if yb in grp:
                tianma_b = base
                break
    result["天马"] = tianma_b

    # 天空：新增星曜
    # tiankong_method = "standard"（戌10起子年顺 → (10+yb)%12）
    #                   "shun"（顺加生时 → (yb+hb)%12）
    if tiankong_method == "shun":
        result["天空"] = (yb + hb) % 12
    else:
        result["天空"] = (10 + yb) % 12

    # 红鸾：卯(3)起子年逆 → (3 - yb) % 12
    result["红鸾"] = (3 - yb) % 12

    # 天喜：酉(9)起子年逆（红鸾对宫）→ (9 - yb) % 12
    result["天喜"] = (9 - yb) % 12

    # 天官：年干查表 (甲→未, 乙→辰, 丙→巳, 丁→寅, 戊→卯, 己→酉, 庚→亥, 辛→酉, 壬→戌, 癸→午)
    TIANGUAN_TABLE: list[int] = [7, 4, 5, 2, 3, 9, 11, 9, 10, 6]
    result["天官"] = TIANGUAN_TABLE[ys]

    # 天福：年干查表 (甲→酉, 乙→申, 丙→子, 丁→亥, 戊→卯, 己→寅, 庚→午, 辛→巳, 壬→寅, 癸→卯)
    TIANFU_MISC_TABLE: list[int] = [9, 8, 0, 11, 3, 2, 6, 5, 2, 3]
    result["天福"] = TIANFU_MISC_TABLE[ys]

    # 截空（旬空）安法：jiukong_method 决定输出形式
    # 旬空两支：由年干支所在旬首推算
    # 甲子旬→戌亥空, 甲戌旬→申酉空, 甲申旬→午未空, 甲午旬→辰巳空, 甲辰旬→寅卯空, 甲寅旬→子丑空
    year_jiazi = (6 * ys - 5 * yb) % 60
    xun = (year_jiazi // 10) * 10
    xunkong1 = (int(xun) % 12 + 10) % 12  # 旬尾第一支（主空亡）
    xunkong2 = (int(xun) % 12 + 11) % 12  # 旬尾第二支（副空亡）

    if jiukong_method == "single":
        # 常规单星法：仅保留主空亡
        result["截空"] = xunkong1
    elif jiukong_method == "zhanyan":
        # 占验派截路空亡：以时支双支为准
        # 子丑时→午未空, 寅卯时→申酉空, 辰巳时→戌亥空
        # 午未时→子丑空, 申酉时→寅卯空, 戌亥时→辰巳空
        _zk1 = (hb // 2 * 2 + 6) % 12
        _zk2 = (_zk1 + 1) % 12
        result["截空1"] = _zk1
        result["截空2"] = _zk2
    else:
        # 正副双星法（默认）：同时输出两支
        result["截空1"] = xunkong1
        result["截空2"] = xunkong2

    # 天使天伤安法：tianshang_method 决定落宫
    # standard  常规：天伤=迁移宫支(lp_b-6), 天使=疾厄宫支(lp_b-5)
    # zhongzhou 中州：天伤=交友宫支(lp_b-7), 天使=父母宫支(lp_b-11)
    if tianshang_method == "zhongzhou":
        result["天伤"] = (lp_b - 7) % 12  # 交友宫支
        result["天使"] = (lp_b - 11) % 12  # 父母宫支
    else:
        result["天伤"] = (lp_b - 6) % 12  # 迁移宫支
        result["天使"] = (lp_b - 5) % 12  # 疾厄宫支

    # 天寿：年支  天寿 = yb
    result["天寿"] = yb

    # 天才：命宫支 (由外层传入时追加，这里先占位为0)
    result["天才_placeholder"] = 0  # 在__init__.py中会更新

    # 孤辰：年支查表 (寅午戌→巳, 申子辰→亥, 巳酉丑→寅, 亥卯未→申)
    GUCHEN: dict[tuple[int, ...], int] = {(2, 6, 10): 5, (8, 0, 4): 11, (5, 9, 1): 2, (11, 3, 7): 8}
    gc_b = 2
    for grp, base in GUCHEN.items():
        if yb in grp:
            gc_b = base
            break
    result["孤辰"] = gc_b

    # 寡宿：年支查表 (寅午戌→丑, 申子辰→戌, 巳酉丑→辰, 亥卯未→未)
    GUASU: dict[tuple[int, ...], int] = {(2, 6, 10): 1, (8, 0, 4): 10, (5, 9, 1): 4, (11, 3, 7): 7}
    gs_b = 1
    for grp, base in GUASU.items():
        if yb in grp:
            gs_b = base
            break
    result["寡宿"] = gs_b

    # 博士十二流曜：由 dayun + ziwei_full 按大运天干计算（见 __init__.py），
    # 不在本命杂曜层重复安星。
    # 天德/月德（紫微斗数全书·安天德月德解神诀）
    # 天德：酉宫起子顺数至生年太岁；月德：子宫起子顺数至生年太岁
    result["天德"] = (9 + yb) % 12
    result["月德"] = yb % 12

    # ──── 缺失杂曜星补充 ─────────────────────────────
    # 天刑：酉(9)起正月顺数 → (9 + m) % 12
    result["天刑"] = (9 + m) % 12

    # 天姚：丑(1)起正月顺数 → (m) % 12
    result["天姚"] = m % 12

    # 天厨：年干查表（甲→卯, 乙→巳, 丙→巳, 丁→未, 戊→酉, 己→酉, 庚→亥, 辛→亥, 壬→丑, 癸→丑）
    TIANCHU_TABLE = [3, 5, 5, 7, 9, 9, 11, 11, 1, 1]
    result["天厨"] = TIANCHU_TABLE[ys]

    # 台辅：午(6)起正月顺数 → (5 + m) % 12
    result["台辅"] = (5 + m) % 12

    # 封诰：午(6)起正月逆数 → (7 - m + 12) % 12
    result["封诰"] = (7 - m + 12) % 12

    # 三台：左辅 + 日数（日支）
    day_branch = info.day_branch_idx
    result["三台"] = (result["左辅"] + day_branch) % 12

    # 八座：右弼 - 日数（日支）
    result["八座"] = (result["右弼"] - day_branch + 12) % 12

    # 恩光：文昌 + 日数
    result["恩光"] = (result["文昌"] + day_branch) % 12

    # 天贵：文曲 + 日数
    result["天贵"] = (result["文曲"] + day_branch) % 12

    # 龙池：辰(4)起子年顺数 → (4 + yb) % 12
    result["龙池"] = (4 + yb) % 12

    # 凤阁：戌(10)起子年逆数 → (10 - yb + 12) % 12
    result["凤阁"] = (10 - yb + 12) % 12

    # 天巫：年支查表（巳酉丑→巳(5)，亥卯未→巳(5)，寅午戌→亥(11)，申子辰→亥(11)）
    TIANWU_TABLE = {(5, 9, 1): 5, (11, 3, 7): 5, (2, 6, 10): 11, (8, 0, 4): 11}
    tw_b = 5
    for grp, base in TIANWU_TABLE.items():
        if yb in grp:
            tw_b = base
            break
    result["天巫"] = tw_b

    # 解神：年支查表（寅午戌→酉(9)，申子辰→卯(3)，巳酉丑→未(7)，亥卯未→丑(1)）
    JIEXHEN_TABLE = {(2, 6, 10): 9, (8, 0, 4): 3, (5, 9, 1): 7, (11, 3, 7): 1}
    js_b = 9
    for grp, base in JIEXHEN_TABLE.items():
        if yb in grp:
            js_b = base
            break
    result["解神"] = js_b

    # 天哭：午(6)起子年顺数 → (6 + yb) % 12
    result["天哭"] = (6 + yb) % 12

    # 天虚：午(6)起子年逆数 → (6 - yb + 12) % 12
    result["天虚"] = (6 - yb + 12) % 12

    # 阴煞：年支查表（寅午戌→巳(5)，申子辰→酉(9)，巳酉丑→丑(1)，亥卯未→未(7)）
    YINSHA_TABLE = {(2, 6, 10): 5, (8, 0, 4): 9, (5, 9, 1): 1, (11, 3, 7): 7}
    ys_b = 5
    for grp, base in YINSHA_TABLE.items():
        if yb in grp:
            ys_b = base
            break
    result["阴煞"] = ys_b

    # 破碎：年支查表（寅午戌→申(8)，申子辰→寅(2)，巳酉丑→巳(5)，亥卯未→亥(11)）
    POSHUI_TABLE = {(2, 6, 10): 8, (8, 0, 4): 2, (5, 9, 1): 5, (11, 3, 7): 11}
    ps_b = 8
    for grp, base in POSHUI_TABLE.items():
        if yb in grp:
            ps_b = base
            break
    result["破碎"] = ps_b

    # 蜚廉：年支查表（寅午戌→子(0)，申子辰→午(6)，巳酉丑→卯(3)，亥卯未→酉(9)）
    FEILIAN_TABLE = {(2, 6, 10): 0, (8, 0, 4): 6, (5, 9, 1): 3, (11, 3, 7): 9}
    fl_b = 0
    for grp, base in FEILIAN_TABLE.items():
        if yb in grp:
            fl_b = base
            break
    result["蜚廉"] = fl_b

    # 咸池：年支查表（寅午戌→午(6)，申子辰→子(0)，巳酉丑→酉(9)，亥卯未→卯(3)）
    XIANCHI_TABLE = {(2, 6, 10): 6, (8, 0, 4): 0, (5, 9, 1): 9, (11, 3, 7): 3}
    xc_b = 6
    for grp, base in XIANCHI_TABLE.items():
        if yb in grp:
            xc_b = base
            break
    result["咸池"] = xc_b
    return result
