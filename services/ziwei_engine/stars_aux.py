"""
services/ziwei_engine/stars_aux.py — 辅星/杂曜布局

来源：《紫微斗数全书》诸星安法
"""
from __future__ import annotations

from .tables import BRANCHES
from .lunar import LunarInfo


def place_aux_stars(info: LunarInfo) -> dict[str, int]:
    """
    布局辅星/杂曜，返回 {星名: branch_idx}。

    ── 六吉星 ──
    文昌：年支安法 (酉起，逆数)  →  文昌 = (9  - year_branch) % 12
    文曲：年支安法 (辰起，顺数)  →  文曲 = (4  + year_branch) % 12
          通行版：辰(4)起子年顺布
    天魁：年干安法 (查表)
    天钺：年干安法 (查表)
    左辅：月支安法  左辅 = (2 + lunar_month) % 12   (辰=4起正月)
          正月辰、二月巳、… 正月(1)→辰(4): (3+lunar_month) mod 12
    右弼：时支安法  右弼 = (10 - hour_branch) % 12  (戌起子时)

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
    天马：年支 → 查表（寅申巳亥 四马之地的轮转）
    天官：年干 → 查表
    天福：年干 → 查表
    天厨：年干 → 查表
    红鸾：年支 → 卯(3)起子年逆数  红鸾 = (3 - year_branch + 12) % 12
    天喜：年支 → 酉(9)起子年逆数  天喜 = (9 - year_branch + 12) % 12
          实际：红鸾 = (3 - year_branch) % 12, 天喜 = (9 - year_branch) % 12
    截空：年支双数 → 查表
    旬空：由年干支起旬确定
    """
    ys = info.year_stem_idx     # 年天干 甲=0
    yb = info.year_branch_idx   # 年地支 子=0
    m  = info.lunar_month       # 1-12
    hb = info.hour_branch_idx   # 子=0

    result: dict[str, int] = {}

    # ──── 六吉星 ────────────────────────────────────────
    # 文昌：酉(9)起子年逆 → 文昌 = (9 - yb) % 12
    result["文昌"] = (9 - yb) % 12

    # 文曲：辰(4)起子年顺 → 文曲 = (4 + yb) % 12
    # 通行版（《紫微斗数全书》）：辰宫起子年，顺数十二支
    result["文曲"] = (4 + yb) % 12

    # 天魁天钺：年干查表 (来源：《紫微斗数全书》)
    # 甲戊庚 → 魁丑钺未
    # 乙己年 → 魁子钺申
    # 丙丁年 → 魁亥钺酉
    # 壬癸年 → 魁卯钺巳
    # 辛年   → 魁午钺寅
    TIANkui_TABLE: list[int] = [1, 0, 11, 11, 1, 0, 1, 6, 3, 3]  # 地支索引
    TIANYUE_TABLE: list[int] = [7, 8,  9,  9, 7, 8, 7, 2, 5, 5]
    result["天魁"] = TIANkui_TABLE[ys]
    result["天钺"] = TIANYUE_TABLE[ys]

    # 左辅：辰(4)起正月，顺数 → 左辅 = (3 + m) % 12
    result["左辅"] = (3 + m) % 12

    # 右弼：戌(10)起子时，逆数 → 右弼 = (10 - hb) % 12
    result["右弼"] = (10 - hb) % 12

    # ──── 六煞星 ────────────────────────────────────────
    # 禄存/擎羊/陀罗查表（年干）
    # 禄存所在地支：甲寅乙卯丙戊巳丁己午庚申辛酉壬亥癸子
    LUZUN_TABLE: list[int] = [2, 3, 5, 5, 7, 7, 8, 9, 11, 0]
    luzun_b = LUZUN_TABLE[ys]
    result["禄存"] = luzun_b
    result["擎羊"] = (luzun_b + 1) % 12   # 禄前一位
    result["陀罗"] = (luzun_b - 1) % 12   # 禄后一位

    # 火星：年支+时支双变量查表
    # 来源：《斗数宣微》火星铃星安法
    # 行1: 年支 寅午戌 → 丑(1)起子时顺
    # 行2: 年支 申子辰 → 寅(2)起子时顺
    # 行3: 年支 巳酉丑 → 卯(3)起子时顺
    # 行4: 年支 亥卯未 → 酉(9)起子时顺
    HUOXING_BASE: dict[tuple[int,...], int] = {
        (2, 6, 10): 1,   # 寅午戌 → 丑起
        (8, 0, 4):  2,   # 申子辰 → 寅起
        (5, 9, 1):  3,   # 巳酉丑 → 卯起
        (11, 3, 7): 9,   # 亥卯未 → 酉起
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
    LINGXING_BASE: dict[tuple[int,...], int] = {
        (2, 6, 10):  3,   # 寅午戌 → 卯起
        (8, 0, 4):  10,   # 申子辰 → 戌起
        (5, 9, 1):  10,   # 巳酉丑 → 戌起
        (11, 3, 7): 10,   # 亥卯未 → 戌起
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
    # 天马：年支查表
    # 寅(2)申(8):午(6), 巳(5)亥(11):申(8), 申(8)寅(2):寅(2), 亥(11)巳(5):亥(11)
    # 四马地 = 寅申巳亥，天马在三合对冲
    TIANMA_TABLE: list[int] = [8, 11, 6, 8, 6, 11, 8, 11, 2, 8, 2, 2]
    # 子(0)=申, 丑(1)=亥, 寅(2)=午, 卯(3)=寅? 
    # 通行版：子午卯酉年天马在寅，寅申巳亥年天马在申，辰戌丑未年天马在巳
    TIANMA_SIMPLE: list[int] = [2, 5, 8, 11, 2, 5, 8, 11, 2, 5, 8, 11]
    # 实际查表：
    # 申子辰年 → 寅(2)，寅午戌年 → 申(8)，巳酉丑年 → 亥(11)，亥卯未年 → 巳(5)
    TIANMA_BY_BRANCH: dict[tuple[int,...], int] = {
        (8, 0, 4):   2,   # 申子辰 → 寅
        (2, 6, 10):  8,   # 寅午戌 → 申
        (5, 9, 1):  11,   # 巳酉丑 → 亥
        (11, 3, 7):  5,   # 亥卯未 → 巳
    }
    tianma_b = 2
    for grp, base in TIANMA_BY_BRANCH.items():
        if yb in grp:
            tianma_b = base
            break
    result["天马"] = tianma_b

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

    # 截空（旬空）：年干支确定旬首，空亡在旬尾两支
    # 甲子旬→戌亥空, 甲戌旬→申酉空, 甲申旬→午未空,
    # 甲午旬→辰巳空, 甲辰旬→寅卯空, 甲寅旬→子丑空
    # 旬首 = 该60甲子的旬第一位，jiazi_idx // 10 * 10 → 0,10,20,30,40,50
    year_jiazi = (6 * ys - 5 * yb) % 60
    xun = (year_jiazi // 10) * 10
    # 旬空=旬尾两位 = 旬首 branch + 10, +11
    xunkong1 = (int(xun) % 12 + 10) % 12
    xunkong2 = (int(xun) % 12 + 11) % 12
    result["截空1"] = xunkong1
    result["截空2"] = xunkong2

    # 天寿：年支  天寿 = yb
    result["天寿"] = yb

    # 天才：命宫支 (由外层传入时追加，这里先占位为0)
    result["天才_placeholder"] = 0   # 在__init__.py中会更新

    # 孤辰：年支查表 (寅午戌→巳, 申子辰→亥, 巳酉丑→寅, 亥卯未→申)
    GUCHEN: dict[tuple[int,...], int] = {(2,6,10):5, (8,0,4):11, (5,9,1):2, (11,3,7):8}
    gc_b = 2
    for grp, base in GUCHEN.items():
        if yb in grp: gc_b = base; break
    result["孤辰"] = gc_b

    # 寡宿：年支查表 (寅午戌→丑, 申子辰→戌, 巳酉丑→辰, 亥卯未→未)
    GUASU: dict[tuple[int,...], int] = {(2,6,10):1, (8,0,4):10, (5,9,1):4, (11,3,7):7}
    gs_b = 1
    for grp, base in GUASU.items():
        if yb in grp: gs_b = base; break
    result["寡宿"] = gs_b

    # 博士流曜 (取代表性几个)：大运天干确定，此处暂不实现，占位
    # 月德：月支 → 固定表 (暂从略，影响较小)

    return result
