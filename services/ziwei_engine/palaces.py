"""
services/ziwei_engine/palaces.py — 十二宫定位（命宫/身宫/宫名）

核心算法（来源：《紫微斗数全书》起命宫法）：
  命宫地支 = (2 + lunar_month - 1 - hour_branch) mod 12
           = (寅 + 月数-1 - 时支) mod 12
  身宫地支 = (2 + lunar_month - 1 + hour_branch) mod 12

命宫天干（五虎遁年+数宫步数）：
  从月干开始，步数 = (命宫支 - 寅支) mod 12
  命宫天干 = (月干 + 步数) mod 10

五行局（命宫干支纳音→局数）：
  公式：jiazi_idx = (6*stem - 5*branch) mod 60
        nayin_idx = jiazi_idx // 2
        五行局 = NAYIN_TO_JU[NAYIN_30[nayin_idx]]

宫名分配（命宫为1宫，顺时针逆地支方向依次排列）：
  palace_name[i] = PALACE_NAMES[(i - 命宫支 + 12) % 12]
"""
from __future__ import annotations

from dataclasses import dataclass
from .tables import (
    STEMS, BRANCHES, PALACE_NAMES,
    NAYIN_30, NAYIN_TO_JU, WUHU_M1_STEM,
)
from .lunar import LunarInfo


@dataclass
class PalaceLayout:
    """十二宫布局"""
    life_branch_idx: int    # 命宫地支索引
    body_branch_idx: int    # 身宫地支索引
    life_stem_idx: int      # 命宫天干索引
    life_ganzhi: str        # 命宫干支 如"丁未"
    body_ganzhi: str        # 身宫干支
    wuxing_ju: int          # 五行局数 2/3/4/5/6
    wuxing_ju_name: str     # "水二局" / "木三局" 等
    # 12宫索引 → 宫名 : branch_idx → palace_name
    branch_to_palace: dict[int, str]
    # 宫名 → branch_idx
    palace_to_branch: dict[str, int]


_JU_NAMES: dict[int, str] = {
    2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局",
}


def calc_palaces(info: LunarInfo) -> PalaceLayout:
    """根据农历信息计算十二宫布局"""
    m  = info.calc_lunar_month   # 闰月按下一月（如闰五月=6），确保命宫计算正确
    hb = info.hour_branch_idx    # 子=0…亥=11 (寅=2)

    # ── 命宫地支 ──
    life_b = (2 + m - 1 - hb) % 12    # 寅(2) + 月数-1 - 时支

    # ── 身宫地支 ──
    body_b = (2 + m - 1 + hb) % 12

    # ── 命宫天干（五虎遁：寅干起+步数）──
    # 步数 = 从寅(2) 顺数到命宫地支（寅宫天干 = WUHU_M1_STEM[年干]）
    steps = (life_b - 2) % 12
    life_stem_idx = (WUHU_M1_STEM[info.year_stem_idx] + steps) % 10

    # ── 五行局 ──
    # jiazi_60_index = (6*stem - 5*branch) mod 60
    jiazi_idx = (6 * life_stem_idx - 5 * life_b) % 60
    nayin_idx = jiazi_idx // 2
    nayin_element = NAYIN_30[nayin_idx]
    ju = NAYIN_TO_JU[nayin_element]

    life_gz = STEMS[life_stem_idx] + BRANCHES[life_b]
    body_stem_steps = (body_b - 2) % 12
    body_stem_idx = (WUHU_M1_STEM[info.year_stem_idx] + body_stem_steps) % 10
    body_gz = STEMS[body_stem_idx] + BRANCHES[body_b]

    # ── 宫名分配 ──
    # 命宫所在支=life_b，为PALACE_NAMES[0]="命宫"
    # 宫名顺序：从命宫支开始，沿地支逆序（减少方向）排列
    # 即：life_b=命宫, (life_b-1)%12=兄弟宫, (life_b-2)%12=夫妻宫, ...
    branch_to_palace: dict[int, str] = {}
    palace_to_branch: dict[str, int] = {}
    for i, name in enumerate(PALACE_NAMES):
        b = (life_b - i) % 12
        branch_to_palace[b] = name
        palace_to_branch[name] = b

    return PalaceLayout(
        life_branch_idx  = life_b,
        body_branch_idx  = body_b,
        life_stem_idx    = life_stem_idx,
        life_ganzhi      = life_gz,
        body_ganzhi      = body_gz,
        wuxing_ju        = ju,
        wuxing_ju_name   = _JU_NAMES[ju],
        branch_to_palace = branch_to_palace,
        palace_to_branch = palace_to_branch,
    )
