"""
services/ziwei_engine/patterns.py — 紫微斗数命盘格局检测

检测命盘中的吉格与凶局，包括：
  吉格：禄存守命、化禄/化权守命、三方逢科权禄、紫府同宫、
        君臣庆会、府相朝垣、日月同宫/拱命、武贪格
  凶局：化忌守命、化忌入财、羊陀夹命、火铃夹命

使用说明：
  from .patterns import detect_patterns, PatternResult
  patterns = detect_patterns(chart.palaces)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ──────────────────────────────────────────────────────────────
# 数据结构
# ──────────────────────────────────────────────────────────────


@dataclass
class PatternResult:
    """单个格局检测结果。"""

    name: str  # 格局名称，如"禄存守命"
    level: str  # "大吉" / "吉" / "凶" / "大凶"
    description: str  # 一到两句说明
    palaces: list[str] = field(default_factory=list)  # 涉及宫位名
    stars: list[str] = field(default_factory=list)  # 涉及星曜名
    source: str = ""  # 古典出处（专业版展示用）


# ──────────────────────────────────────────────────────────────
# 内部辅助函数
# ──────────────────────────────────────────────────────────────


def _main_star_names(p) -> set[str]:
    """返回宫位中所有主星名集合。"""
    return {s["name"] for s in p.main_stars}


def _stars_with_hua(p, hua: str) -> list[str]:
    """返回宫位中携带指定四化（如'化忌'）的主星名列表。"""
    return [s["name"] for s in p.main_stars if hua in s.get("transforms", [])]


def _hua_types_in_palace(p) -> set[str]:
    """返回宫位中存在的四化类型集合，如 {'化禄', '化权'}。"""
    result: set[str] = set()
    for s in p.main_stars:
        for t in s.get("transforms", []):
            if t.startswith("化"):
                result.add(t)
    return result


# ──────────────────────────────────────────────────────────────
# 主检测函数
# ──────────────────────────────────────────────────────────────


def detect_patterns(palaces: list) -> list[PatternResult]:
    """
    检测命盘格局（吉格与凶局）。

    参数
    ----
    palaces : list[PalaceInfo]
        来自 ZiweiChart.palaces 的宫位列表（12项）。

    返回
    ----
    list[PatternResult]
        检测到的格局列表。吉格在前，凶局在后。
        无格局时返回空列表。
    """
    results: list[PatternResult] = []

    # 建立宫位名 → PalaceInfo 的快速查找表
    p_by_name: dict[str, object] = {p.name: p for p in palaces}

    def get(name: str):
        return p_by_name.get(name)

    life = get("命宫")
    if not life:
        return results

    # 三方（命宫、财帛宫、官禄宫）
    SANFANG_NAMES = ["命宫", "财帛宫", "官禄宫"]
    # 四正（三方 + 迁移宫）
    SIZHENG_NAMES = ["命宫", "财帛宫", "官禄宫", "迁移宫"]
    sanfang = [p for n in SANFANG_NAMES if (p := get(n))]
    sizheng = [p for n in SIZHENG_NAMES if (p := get(n))]

    # 三方四正中所有主星集合
    sizheng_stars: set[str] = set()
    for p in sizheng:
        sizheng_stars.update(_main_star_names(p))

    # 三方四正中所有四化类型
    sizheng_hua: set[str] = set()
    for p in sizheng:
        sizheng_hua.update(_hua_types_in_palace(p))
    has_sizheng_ji = "化忌" in sizheng_hua  # 三方四正中有化忌

    # 三方（仅命/财/官）中所有主星
    sanfang_stars: set[str] = set()
    for p in sanfang:
        sanfang_stars.update(_main_star_names(p))

    # ════════════════════════════════════════════════
    # ── 吉格 ────────────────────────────────────────
    # ════════════════════════════════════════════════

    # 1. 禄存守命
    if "禄存" in life.aux_names:
        results.append(
            PatternResult(
                name="禄存守命",
                level="吉",
                description="禄存坐守命宫，财禄稳厚，一生衣食丰足，遇难化吉。",
                palaces=["命宫"],
                stars=["禄存"],
                source="《紫微斗数全书》",
            )
        )

    # 2. 化禄守命
    lu_stars = _stars_with_hua(life, "化禄")
    if lu_stars:
        results.append(
            PatternResult(
                name="化禄守命",
                level="吉",
                description=f"命宫逢化禄（{'/'.join(lu_stars)}），财源广进，诸事顺遂。",
                palaces=["命宫"],
                stars=lu_stars,
                source="《紫微斗数全书》",
            )
        )

    # 3. 化权守命
    quan_stars = _stars_with_hua(life, "化权")
    if quan_stars:
        results.append(
            PatternResult(
                name="化权守命",
                level="吉",
                description=f"命宫逢化权（{'/'.join(quan_stars)}），意志坚定，事业领导有方。",
                palaces=["命宫"],
                stars=quan_stars,
                source="《紫微斗数全书》",
            )
        )

    # 4. 三方逢科权禄（三化齐聚四正）
    if {"化禄", "化权", "化科"} <= sizheng_hua:
        involved = [p.name for p in sizheng if _hua_types_in_palace(p)]
        results.append(
            PatternResult(
                name="三方逢科权禄",
                level="大吉",
                description="命宫三方四正化禄、化权、化科三化齐聚，文武双全，功名富贵兼得。",
                palaces=involved,
                stars=[],
                source="《紫微斗数全书》",
            )
        )

    # 5. 紫府同宫
    for p in palaces:
        stars = _main_star_names(p)
        if "紫微" in stars and "天府" in stars:
            results.append(
                PatternResult(
                    name="紫府同宫",
                    level="大吉",
                    description=f"帝星紫微与天府同坐{p.name}，高贵多福，气度不凡，富贵双全。",
                    palaces=[p.name],
                    stars=["紫微", "天府"],
                    source="《紫微斗数全书》",
                )
            )
            break

    # 6. 君臣庆会：紫微与左辅/右弼同宫
    for p in palaces:
        stars = _main_star_names(p)
        aux = p.aux_names
        if "紫微" in stars and ("左辅" in aux or "右弼" in aux):
            helpers = [s for s in ["左辅", "右弼"] if s in aux]
            results.append(
                PatternResult(
                    name="君臣庆会",
                    level="大吉",
                    description=(f"紫微与{'/'.join(helpers)}同坐{p.name}，君臣得辅，领袖气质，贵人扶持。"),
                    palaces=[p.name],
                    stars=["紫微"] + helpers,
                    source="《紫微斗数全书》",
                )
            )
            break

    # 7. 府相朝垣：天府+天相均在三方（命/财/官）
    if "天府" in sanfang_stars and "天相" in sanfang_stars:
        pnames = [p.name for p in sanfang if "天府" in _main_star_names(p) or "天相" in _main_star_names(p)]
        results.append(
            PatternResult(
                name="府相朝垣",
                level="吉",
                description="天府、天相均在命宫三方，辅星拱照，事业基础稳固，贵人提携有力。",
                palaces=pnames,
                stars=["天府", "天相"],
                source="《紫微斗数全书》",
            )
        )

    # 8. 日月同宫
    for p in palaces:
        stars = _main_star_names(p)
        if "太阳" in stars and "太阴" in stars:
            results.append(
                PatternResult(
                    name="日月同宫",
                    level="吉",
                    description=f"太阳、太阴同坐{p.name}，日月交辉，性格温润，名望与人缘俱佳。",
                    palaces=[p.name],
                    stars=["太阳", "太阴"],
                    source="《紫微斗数全书》",
                )
            )
            break
    else:
        # 9. 日月拱命：太阳+太阴在三方四正（不同宫）
        if "太阳" in sizheng_stars and "太阴" in sizheng_stars:
            s_pals = [p.name for p in sizheng if "太阳" in _main_star_names(p)]
            m_pals = [p.name for p in sizheng if "太阴" in _main_star_names(p)]
            if set(s_pals) != set(m_pals):
                results.append(
                    PatternResult(
                        name="日月拱命",
                        level="吉",
                        description="太阳、太阴分处命宫三方四正，日月拱照，文明贵气，声名远播。",
                        palaces=list(dict.fromkeys(s_pals + m_pals)),
                        stars=["太阳", "太阴"],
                        source="《紫微斗数全书》",
                    )
                )

    # 10. 武贪格：武曲+贪狼同宫
    for p in palaces:
        stars = _main_star_names(p)
        if "武曲" in stars and "贪狼" in stars:
            results.append(
                PatternResult(
                    name="武贪格",
                    level="吉",
                    description=f"武曲贪狼同坐{p.name}，偏财武职皆有机缘，中年以后财运渐旺。",
                    palaces=[p.name],
                    stars=["武曲", "贪狼"],
                    source="《紫微斗数全书》",
                )
            )
            break

    # ════════════════════════════════════════════════
    # ── 凶局（高危预警）────────────────────────────
    # ════════════════════════════════════════════════

    # 11. 化忌守命
    ji_in_life = _stars_with_hua(life, "化忌")
    if ji_in_life:
        results.append(
            PatternResult(
                name="化忌守命",
                level="凶",
                description=(f"命宫坐化忌（{'/'.join(ji_in_life)}），宜防是非口舌与身心损耗，需以德化忌、韬光养晦。"),
                palaces=["命宫"],
                stars=ji_in_life,
                source="《紫微斗数全书》",
            )
        )

    # 12. 化忌入财帛
    cai = get("财帛宫")
    if cai:
        ji_in_cai = _stars_with_hua(cai, "化忌")
        if ji_in_cai:
            results.append(
                PatternResult(
                    name="化忌入财",
                    level="凶",
                    description=(f"财帛宫化忌（{'/'.join(ji_in_cai)}），财务需谨慎管理，防破财、借贷纠纷及意外损耗。"),
                    palaces=["财帛宫"],
                    stars=ji_in_cai,
                    source="《紫微斗数全书》",
                )
            )

    # 13. 化忌入官禄
    guan = get("官禄宫")
    if guan:
        ji_in_guan = _stars_with_hua(guan, "化忌")
        if ji_in_guan:
            results.append(
                PatternResult(
                    name="化忌入官",
                    level="凶",
                    description=(f"官禄宫化忌（{'/'.join(ji_in_guan)}），事业易逢阻碍或压力，宜低调稳健，防职场风波。"),
                    palaces=["官禄宫"],
                    stars=ji_in_guan,
                    source="《紫微斗数全书》",
                )
            )

    # 14. 羊陀夹命：擎羊+陀罗夹住命宫（分在两侧相邻宫）
    brother = get("兄弟宫")  # 命宫前一位（palace index 1）
    parent = get("父母宫")  # 命宫后一位（palace index 11）
    if brother and parent:
        adj_aux = brother.aux_names | parent.aux_names
        if "擎羊" in adj_aux and "陀罗" in adj_aux:
            results.append(
                PatternResult(
                    name="羊陀夹命",
                    level="大凶",
                    description="擎羊、陀罗夹住命宫，早年多磨折波折，宜坚韧处世，忌意气用事。",
                    palaces=["父母宫", "命宫", "兄弟宫"],
                    stars=["擎羊", "陀罗"],
                    source="《紫微斗数全书》",
                )
            )

    # 15. 火铃夹命：火星+铃星夹住命宫
    if brother and parent:
        adj_aux2 = brother.aux_names | parent.aux_names
        if "火星" in adj_aux2 and "铃星" in adj_aux2:
            results.append(
                PatternResult(
                    name="火铃夹命",
                    level="凶",
                    description="火星、铃星夹住命宫，性情急躁冲动，宜修身养性，慎防意外与刑事纠纷。",
                    palaces=["父母宫", "命宫", "兄弟宫"],
                    stars=["火星", "铃星"],
                    source="《紫微斗数全书》",
                )
            )

    # ════════════════════════════════════════════════
    # ── 吉格 v2（新增 16–27）───────────────────────
    # ════════════════════════════════════════════════

    # 16. 禄权科三奇会命：化禄、化权、化科同在命宫
    life_hua = _hua_types_in_palace(life)
    if {"化禄", "化权", "化科"} <= life_hua:
        lu_s = _stars_with_hua(life, "化禄")
        qu_s = _stars_with_hua(life, "化权")
        ke_s = _stars_with_hua(life, "化科")
        results.append(
            PatternResult(
                name="禄权科三奇会命",
                level="大吉",
                description="化禄、化权、化科三奇同聚命宫，功名利禄一身俱得，气运绝顶。",
                palaces=["命宫"],
                stars=lu_s + qu_s + ke_s,
                source="《紫微斗数全书》",
            )
        )

    # 17. 科权夹命：化科与化权分夹命宫两侧
    if brother and parent:
        adj_hua = set()
        for p in [brother, parent]:
            adj_hua.update(_hua_types_in_palace(p))
        if "化权" in adj_hua and "化科" in adj_hua:
            results.append(
                PatternResult(
                    name="科权夹命",
                    level="吉",
                    description="化权、化科夹护命宫，才华与魄力兼备，学术仕途双双顺遂。",
                    palaces=["父母宫", "命宫", "兄弟宫"],
                    stars=[],
                    source="《紫微斗数全书》",
                )
            )

    # 18. 日月并明：太阳或太阴化禄/化权在三方且均旺
    sun_p = next((p for p in sizheng if "太阳" in _main_star_names(p)), None)
    moon_p = next((p for p in sizheng if "太阴" in _main_star_names(p)), None)
    if sun_p and moon_p and sun_p is not moon_p:
        sun_hua = _hua_types_in_palace(sun_p)
        moon_hua = _hua_types_in_palace(moon_p)
        if ("化禄" in sun_hua or "化权" in sun_hua) and ("化禄" in moon_hua or "化科" in moon_hua):
            results.append(
                PatternResult(
                    name="日月并明",
                    level="大吉",
                    description="太阳化禄/化权、太阴化禄/化科同在三方，日月并明，声名显赫，贵气临门。",
                    palaces=[sun_p.name, moon_p.name],
                    stars=["太阳", "太阴"],
                    source="《紫微斗数全书》",
                )
            )

    # 19. 天梁守命（清白/清高格）
    liang_stars = _main_star_names(life)
    if "天梁" in liang_stars:
        results.append(
            PatternResult(
                name="天梁守命",
                level="吉",
                description="天梁坐命，清高自持，宜学术宗教法律，一生逢凶化吉，晚运转佳。",
                palaces=["命宫"],
                stars=["天梁"],
                source="《紫微斗数全书》",
            )
        )

    # 20. 机月同梁：天机、太阴、天同、天梁均在三方四正
    mjtl_req = {"天机", "太阴", "天同", "天梁"}
    if mjtl_req <= sizheng_stars:
        inv = [p.name for p in sizheng if _main_star_names(p) & mjtl_req]
        results.append(
            PatternResult(
                name="机月同梁",
                level="吉",
                description="天机、太阴、天同、天梁齐聚三方四正，适合公职幕僚，稳健安逸，中年享福。",
                palaces=inv,
                stars=list(mjtl_req),
                source="《全书》",
            )
        )

    # 21. 天同守命（桃花安命）
    if "天同" in liang_stars:
        results.append(
            PatternResult(
                name="天同守命",
                level="吉",
                description="天同坐命，心性温和，桃花旺盛，个性乐天，福泽绵延，颇得人缘。",
                palaces=["命宫"],
                stars=["天同"],
                source="《紫微斗数全书》",
            )
        )

    # 22. 武曲化禄守财（武禄入财）
    cai2 = get("财帛宫")
    if cai2:
        wu_lu = _stars_with_hua(cai2, "化禄")
        if wu_lu and "武曲" in wu_lu:
            results.append(
                PatternResult(
                    name="武禄入财",
                    level="大吉",
                    description="武曲化禄坐财帛宫，财运丰厚，经商理财得天独厚，正财偏财皆可得。",
                    palaces=["财帛宫"],
                    stars=["武曲"],
                    source="《紫微斗数全书》",
                )
            )

    # 23. 禄马交驰：禄存与天马在同宫或三方拱照
    def _has_aux(p, star: str) -> bool:
        return star in p.aux_names

    lu_palace = next((p for p in palaces if _has_aux(p, "禄存")), None)
    ma_palace = next((p for p in palaces if "天马" in p.aux_names), None)
    if lu_palace and ma_palace:
        if lu_palace is ma_palace:
            results.append(
                PatternResult(
                    name="禄马交驰",
                    level="大吉",
                    description="禄存与天马同宫，禄马交驰，奔波中得财，适合外贸、出国或跨区域发展。",
                    palaces=[lu_palace.name],
                    stars=["禄存", "天马"],
                    source="《紫微斗数全书》",
                )
            )
        elif lu_palace in sizheng and ma_palace in sizheng:
            results.append(
                PatternResult(
                    name="禄马交驰",
                    level="吉",
                    description="禄存与天马在三方四正相互拱照，禄马交驰，动中得财，四方奔走皆有收获。",
                    palaces=[lu_palace.name, ma_palace.name],
                    stars=["禄存", "天马"],
                    source="《紫微斗数全书》",
                )
            )

    # 24. 三台八座朝命：三台+八座在命宫三方
    _aux_in_sizheng: set[str] = set()
    for p in sizheng:
        _aux_in_sizheng.update(p.aux_names)
    if "三台" in _aux_in_sizheng and "八座" in _aux_in_sizheng:
        results.append(
            PatternResult(
                name="三台八座朝命",
                level="吉",
                description="三台、八座聚于命宫三方，权贵拱照，仕途有成，地位声望俱佳。",
                palaces=[p.name for p in sizheng if "三台" in p.aux_names or "八座" in p.aux_names],
                stars=["三台", "八座"],
                source="《紫微斗数全书》",
            )
        )

    # 25. 文桂文华（文曲/文昌化科在命宫三方）
    wenhua_stars: list[str] = []
    for p in sizheng:
        for s in p.main_stars:
            if s["name"] in ("文曲", "文昌") and "化科" in s.get("transforms", []):
                wenhua_stars.append(s["name"])
    if wenhua_stars:
        results.append(
            PatternResult(
                name="文桂文华",
                level="吉",
                description=f"{'、'.join(wenhua_stars)}化科在三方四正，文采风流，考试竞赛名列前茅，文艺才华出众。",
                palaces=[
                    p.name
                    for p in sizheng
                    if any(s["name"] in ("文曲", "文昌") and "化科" in s.get("transforms", []) for s in p.main_stars)
                ],
                stars=wenhua_stars,
                source="常见论法",
            )
        )

    # 26. 天才天寿加会（辅星天才+天寿在三方）
    if "天才" in _aux_in_sizheng and "天寿" in _aux_in_sizheng:
        results.append(
            PatternResult(
                name="天才天寿加会",
                level="吉",
                description="天才、天寿齐聚三方，聪明伶俐而且长寿有福，学术研究或技艺方面尤为突出。",
                palaces=[p.name for p in sizheng if "天才" in p.aux_names or "天寿" in p.aux_names],
                stars=["天才", "天寿"],
                source="常见论法",
            )
        )

    # 27. 龙凤拱命（凤阁+龙池在命宫三方）
    if "龙池" in _aux_in_sizheng and "凤阁" in _aux_in_sizheng:
        results.append(
            PatternResult(
                name="龙凤拱命",
                level="吉",
                description="龙池、凤阁拱照命宫，气质高雅，才艺双全，贵气玲珑，多得异性贵人缘。",
                palaces=[p.name for p in sizheng if "龙池" in p.aux_names or "凤阁" in p.aux_names],
                stars=["龙池", "凤阁"],
                source="常见论法",
            )
        )

    # ════════════════════════════════════════════════
    # ── 凶局 v2（新增 28–40）──────────────────────
    # ════════════════════════════════════════════════

    # 28. 化忌守迁移（漂泊格）
    qian = get("迁移宫")
    if qian:
        ji_in_qian = _stars_with_hua(qian, "化忌")
        if ji_in_qian:
            results.append(
                PatternResult(
                    name="化忌入迁移",
                    level="凶",
                    description=f"迁移宫化忌（{'/'.join(ji_in_qian)}），出行异乡多波折，宜在原籍稳定发展，防人在旅途横生变故。",
                    palaces=["迁移宫"],
                    stars=ji_in_qian,
                    source="《紫微斗数全书》",
                )
            )

    # 29. 空劫夹命：地空+地劫夹住命宫
    if brother and parent:
        adj_aux3 = brother.aux_names | parent.aux_names
        if "地空" in adj_aux3 and "地劫" in adj_aux3:
            results.append(
                PatternResult(
                    name="空劫夹命",
                    level="大凶",
                    description="地空、地劫夹住命宫，财运易被虚耗，宜防投机失利与无谓付出，需培养守成心态。",
                    palaces=["父母宫", "命宫", "兄弟宫"],
                    stars=["地空", "地劫"],
                    source="《紫微斗数全书》",
                )
            )

    # 30. 羊陀逢化忌（双重凶：羊陀夹 + 三方化忌）
    has_yang_tuo_jia = False
    if brother and parent:
        _adj4 = brother.aux_names | parent.aux_names
        has_yang_tuo_jia = "擎羊" in _adj4 and "陀罗" in _adj4
    if has_yang_tuo_jia and has_sizheng_ji:
        results.append(
            PatternResult(
                name="羊陀逢化忌",
                level="大凶",
                description="羊陀夹命兼三方逢化忌，双重煞气叠加，命途坎坷多磨，需诚心向善、广积功德化解。",
                palaces=["父母宫", "命宫", "兄弟宫"] + [p.name for p in sizheng if _stars_with_hua(p, "化忌")],
                stars=["擎羊", "陀罗"],
                source="《紫微斗数全书》",
            )
        )

    # 31. 廉贞化忌守命
    lian_ji = [s for s in _stars_with_hua(life, "化忌") if "廉贞" in s]
    if lian_ji:
        results.append(
            PatternResult(
                name="廉贞化忌守命",
                level="大凶",
                description="廉贞化忌坐命，官非刑讼之星化忌，宜慎防法律纠纷、意外血光，凡事低调守法。",
                palaces=["命宫"],
                stars=lian_ji,
                source="《紫微斗数全书》",
            )
        )

    # 32. 白虎守身（凶兆）
    body_palace_name = _find_body_palace(palaces)
    if body_palace_name:
        body_p = get(body_palace_name)
        if body_p and "白虎" in body_p.aux_names:
            results.append(
                PatternResult(
                    name="白虎守身",
                    level="凶",
                    description="白虎坐守身宫，主孝服、官司或意外伤损，宜定期健检，慎防血光与意外事故。",
                    palaces=[body_palace_name],
                    stars=["白虎"],
                    source="《紫微斗数全书》",
                )
            )

    # 33. 擎羊守官禄（事业阻碍）
    guan2 = get("官禄宫")
    if guan2 and "擎羊" in guan2.aux_names:
        results.append(
            PatternResult(
                name="擎羊守官禄",
                level="凶",
                description="擎羊坐官禄宫，事业易逢挫折、上司刁难或职场是非，宜从事技艺武职，以刚克刚。",
                palaces=["官禄宫"],
                stars=["擎羊"],
                source="常见论法",
            )
        )

    # 34. 铃昌陀武（铃星+文昌+陀罗+武曲齐聚）
    ilat_stars: set[str] = set()
    ilat_aux: set[str] = set()
    for p in palaces:
        ilat_stars.update(_main_star_names(p))
        ilat_aux.update(p.aux_names)
    if "铃星" in ilat_aux and "陀罗" in ilat_aux and "武曲" in ilat_stars:
        results.append(
            PatternResult(
                name="铃昌陀武",
                level="凶",
                description="铃星、陀罗、武曲在命盘中形成煞局，武曲之财受双煞侵扰，破财损耗难免，需严控风险投资。",
                palaces=[],
                stars=["铃星", "陀罗", "武曲"],
                source="《紫微斗数全书》",
            )
        )

    # 35. 马头带箭（命宫地支午+擎羊坐命）
    if life.branch == "午":
        life_aux_set = life.aux_names
        if "擎羊" in life_aux_set:
            results.append(
                PatternResult(
                    name="马头带箭",
                    level="大凶",
                    description="命宫午支逢擎羊，马头带箭，性急豪猛但冲动易惹祸，宜从武职或竞技，慎防刀伤意外。",
                    palaces=["命宫"],
                    stars=["擎羊"],
                    source="《紫微斗数全书》",
                )
            )

    # 36. 刑囚夹印（廉贞+天相在三方，三方逢大凶煞）
    if "廉贞" in sizheng_stars and "天相" in sizheng_stars:
        lian_ts_hua = set()
        for p in sizheng:
            if "廉贞" in _main_star_names(p) or "天相" in _main_star_names(p):
                lian_ts_hua.update(_hua_types_in_palace(p))
        if "化忌" in lian_ts_hua:
            inv2 = [p.name for p in sizheng if "廉贞" in _main_star_names(p) or "天相" in _main_star_names(p)]
            results.append(
                PatternResult(
                    name="刑囚夹印",
                    level="大凶",
                    description="廉贞、天相逢化忌在三方，刑囚夹印，主官非牢狱之灾，凡事宜守法循规，慎防诉讼。",
                    palaces=inv2,
                    stars=["廉贞", "天相"],
                    source="《紫微斗数全书》",
                )
            )

    # 37. 曲昌夹忌（文曲+文昌夹住化忌所在宫）
    for idx, p in enumerate(palaces):
        ji_s = _stars_with_hua(p, "化忌")
        if not ji_s:
            continue
        prev_p = palaces[(idx - 1) % 12]
        next_p = palaces[(idx + 1) % 12]
        prev_aux = prev_p.aux_names | _main_star_names(prev_p)
        next_aux = next_p.aux_names | _main_star_names(next_p)
        wen_stars = {"文曲", "文昌"}
        prev_wen = prev_aux & wen_stars
        next_wen = next_aux & wen_stars
        if prev_wen and next_wen and prev_wen != next_wen:
            results.append(
                PatternResult(
                    name="曲昌夹忌",
                    level="凶",
                    description=f"文曲、文昌夹住{p.name}化忌，才华反成羁绊，考试文书易出差错，宜细心为上。",
                    palaces=[prev_p.name, p.name, next_p.name],
                    stars=list(prev_wen | next_wen) + ji_s,
                    source="常见论法",
                )
            )
            break

    # 38. 生离死别（太阳化忌+太阴化忌齐在命宫三方）
    sun_ji = any(_stars_with_hua(p, "化忌") for p in sizheng if "太阳" in _main_star_names(p))
    moon_ji = any(_stars_with_hua(p, "化忌") for p in sizheng if "太阴" in _main_star_names(p))
    if sun_ji and moon_ji:
        results.append(
            PatternResult(
                name="生离死别",
                level="大凶",
                description="太阳、太阴均化忌在三方四正，日月皆暗，主感情破碎、亲人离散，宜宽心释怀广结善缘。",
                palaces=[p.name for p in sizheng if "太阳" in _main_star_names(p) or "太阴" in _main_star_names(p)],
                stars=["太阳", "太阴"],
                source="《紫微斗数全书》",
            )
        )

    # 39. 大限化忌冲本命宫（需大限信息，此处标记触发条件，实际由 analysis.py 深化）
    # 此格局在排盘时已由 analysis.py analysis_tags 标注"大限化忌"，此处跳过

    # 40. 三方无吉曜（三方四正无主吉星且有化忌）
    _GOOD_STARS = {
        "紫微",
        "天机",
        "太阳",
        "武曲",
        "天同",
        "廉贞",
        "天府",
        "太阴",
        "贪狼",
        "巨门",
        "天相",
        "天梁",
        "七杀",
        "破军",
    }
    sizheng_good = sizheng_stars & _GOOD_STARS
    if len(sizheng_good) <= 1 and has_sizheng_ji:
        results.append(
            PatternResult(
                name="三方无吉曜",
                level="大凶",
                description="命宫三方四正几乎无主吉星且有化忌，格局空旷孤贫，宜积德行善、广结善缘以扭转运势。",
                palaces=[p.name for p in sizheng],
                stars=[],
                source="常见论法",
            )
        )

    return results


# ──────────────────────────────────────────────────────────────
# 辅助：查找身宫所在宫位名
# ──────────────────────────────────────────────────────────────
def _find_body_palace(palaces: list) -> str | None:
    """返回身宫所在宫位名（若有标注 is_body_palace 属性）。"""
    for p in palaces:
        if getattr(p, "is_body_palace", False):
            return p.name
    return None
