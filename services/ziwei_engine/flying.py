"""
services/ziwei_engine/flying.py — 飞星紫微（陆斌兆体系）

飞星紫微斗数以"宫位飞化"为核心，
将本命盘的宫干四化飞入各宫（以宫干天干带出化禄/权/科/忌），
形成层叠的影响分析。

本模块：
  1. 计算12宫的宫干（每宫有固定天干，基于命宫天干排定）
  2. 对每个宫位，展开其飞化（禄权科忌落入哪个宫位）
  3. 提供"追星落宫"工具函数
"""
from __future__ import annotations

from dataclasses import dataclass, field
from .tables import STEMS, BRANCHES, PALACE_NAMES
from .transforms import SIHUA_TABLE


# ──────────────────────────────────────────────────────────────
# 五虎遁月：年干 → 正月天干索引（甲=0）
# 丁壬年: 正月=壬(8), 甲己年: 正月=丙(2), etc.
# 宫干从命宫天干顺推十二宫
# ──────────────────────────────────────────────────────────────
def _palace_stems(life_stem_idx: int) -> list[int]:
    """
    12宫的天干索引，从命宫天干顺数（每宫+1 mod 10）。
    索引顺序：命宫=0，兄弟=1，...，父母=11。
    """
    return [(life_stem_idx + i) % 10 for i in range(12)]


@dataclass
class PalaceFlyChart:
    """一个宫位的飞星分析。"""
    palace_idx: int         # 0-11（命宫=0）
    palace_name: str
    branch_idx: int         # 地支索引
    stem_idx: int           # 宫干天干索引
    stem_name: str          # 宫干天干名
    opposition_palace: str = ""  # 对冲宫位名（+6宫）
    # 本宫飞出的四化 → 落入哪个宫位（宫名）
    flying_out: dict[str, str] = field(default_factory=dict)
    # 自化：本宫宫干四化落回本宫的描述列表
    self_transforms: list[str] = field(default_factory=list)


@dataclass
class FlyingStarChart:
    palaces: list[PalaceFlyChart] = field(default_factory=list)
    # 接收到化禄/权/科/忌的宫位汇总
    received: dict[str, list[str]] = field(default_factory=dict)
    # {宫名: [来自x宫化xxx, ...]}
    # 对冲：某宫被飞化冲击的来源描述
    chonged: dict[str, list[str]] = field(default_factory=dict)
    # {宫名: ["来自x宫干y化z冲", ...]}
    # 全局自化列表
    self_transforms: list[str] = field(default_factory=list)


def calc_flying(
    life_palace_branch: int,
    life_stem_idx: int,
    star_branches: dict[str, int],   # {星名: branch_idx} 用于找星在哪个宫
) -> FlyingStarChart:
    """
    计算飞星盘。

    life_palace_branch : 命宫地支索引
    life_stem_idx      : 命宫天干索引
    star_branches      : 14主星 + 辅星的地支分布字典
    """
    # ── 建立"地支 → 宫位名"映射 ─────────────────────────────────
    # 12宫按逆序排列：命宫(life_b), 兄弟(life_b-1)%12, ...
    branch_to_palace_name: dict[int, str] = {}
    palace_order_branches: list[int] = []
    for i in range(12):
        b = (life_palace_branch - i) % 12
        branch_to_palace_name[b] = PALACE_NAMES[i]
        palace_order_branches.append(b)

    # 建立"宫位名 → 宫位索引(0-11)"反查（用于对冲定位）
    palace_name_to_idx: dict[str, int] = {name: idx for idx, name in enumerate(PALACE_NAMES)}

    # ── 建立"星名 → 宫位名"映射（用于飞化落宫定位）─────────────
    star_to_palace: dict[str, str] = {}
    for star, b in star_branches.items():
        pname = branch_to_palace_name.get(b, f"宫{b}")
        star_to_palace[star] = pname

    # ── 每宫干天干 ──────────────────────────────────────────────
    pal_stems = _palace_stems(life_stem_idx)  # 12个天干索引

    # ── 构建飞星宫位列表 ─────────────────────────────────────────
    palaces: list[PalaceFlyChart] = []
    received: dict[str, list[str]] = {name: [] for name in PALACE_NAMES}
    chonged: dict[str, list[str]] = {name: [] for name in PALACE_NAMES}
    all_self_transforms: list[str] = []

    for i, b in enumerate(palace_order_branches):
        stem_i = pal_stems[i]
        stem_name = STEMS[stem_i]
        sihua = SIHUA_TABLE.get(stem_name, {})
        this_palace_name = PALACE_NAMES[i]
        # 对冲宫位（相差6宫）
        opp_idx = (i + 6) % 12
        opp_palace_name = PALACE_NAMES[opp_idx]

        flying_out: dict[str, str] = {}
        pal_self_transforms: list[str] = []

        for hua_type, target_star in sihua.items():
            landing_palace = star_to_palace.get(target_star, "未知")
            flying_out[f"化{hua_type}"] = f"{target_star}({landing_palace})"

            # 记录到收到飞化的宫位
            if landing_palace in received:
                received[landing_palace].append(
                    f"{this_palace_name}宫干{stem_name}化{hua_type}"
                )

            # 对冲：飞化落宫的对面宫（+6）同时被冲
            if landing_palace in palace_name_to_idx:
                landing_idx = palace_name_to_idx[landing_palace]
                chong_palace_name = PALACE_NAMES[(landing_idx + 6) % 12]
                if chong_palace_name in chonged:
                    chonged[chong_palace_name].append(
                        f"{this_palace_name}宫干{stem_name}化{hua_type}冲"
                    )

            # 自化检测：飞化落回本宫
            if landing_palace == this_palace_name:
                desc = f"{this_palace_name}宫干{stem_name}化{hua_type}自化"
                pal_self_transforms.append(desc)
                all_self_transforms.append(desc)

        palaces.append(PalaceFlyChart(
            palace_idx=i,
            palace_name=this_palace_name,
            branch_idx=b,
            stem_idx=stem_i,
            stem_name=stem_name,
            opposition_palace=opp_palace_name,
            flying_out=flying_out,
            self_transforms=pal_self_transforms,
        ))

    return FlyingStarChart(
        palaces=palaces,
        received=received,
        chonged=chonged,
        self_transforms=all_self_transforms,
    )
