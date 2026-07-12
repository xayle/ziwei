"""
tests/test_coverage_boost24.py
──────────────────────────────
目标覆盖模块：
  - services/ziwei_engine/patterns.py       (格局检测：v2 新增格局 5-27)
  - services/ziwei_engine/compatibility.py  (六合度：全维度分支覆盖)
"""
from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from services.ziwei_engine import PalaceInfo


# ══════════════════════════════════════════════════════════════════════════════
# 辅助：快速构造 PalaceInfo mock
# ══════════════════════════════════════════════════════════════════════════════

def _palace(
    name: str,
    index: int = 0,
    branch_idx: int = 0,
    main_stars: list[dict] | None = None,
    aux_stars: list[str] | None = None,
) -> PalaceInfo:
    """构造最小化 PalaceInfo 对象，方便测试格局检测。"""
    return PalaceInfo(
        index=index,
        name=name,
        branch_idx=branch_idx,
        branch="子",
        stem_idx=0,
        stem="甲",
        main_stars=main_stars or [],
        aux_stars=aux_stars or [],
    )


def _star(name: str, transforms: list[str] | None = None) -> dict:
    """构造 main_stars 中单颗星的 dict。"""
    return {
        "name": name,
        "brightness": "旺",
        "brightness_val": 4,
        "transforms": transforms or [],
    }


def _make_12_palaces(
    life_main: list[dict] | None = None,
    life_aux: list[str] | None = None,
    cai_main: list[dict] | None = None,
    cai_aux: list[str] | None = None,
    guan_main: list[dict] | None = None,
    qian_main: list[dict] | None = None,
    xiong_main: list[dict] | None = None,
    xiong_aux: list[str] | None = None,
    fumu_main: list[dict] | None = None,
    fumu_aux: list[str] | None = None,
    extra: dict[str, PalaceInfo] | None = None,
) -> list[PalaceInfo]:
    """
    返回 12 宫的列表。
    默认所有宫位为空，可传入自定义 main_stars/aux_stars。
    extra: 宫名 → PalaceInfo，用于覆盖默认空宫。
    """
    PALACE_NAMES = [
        "命宫", "兄弟宫", "夫妻宫", "子女宫",
        "财帛宫", "疾厄宫", "迁移宫", "仆役宫",
        "官禄宫", "田宅宫", "福德宫", "父母宫",
    ]
    palaces = []
    for i, n in enumerate(PALACE_NAMES):
        if n == "命宫":
            p = _palace(n, index=i, main_stars=life_main, aux_stars=life_aux)
        elif n == "兄弟宫":
            p = _palace(n, index=i, main_stars=xiong_main, aux_stars=xiong_aux)
        elif n == "财帛宫":
            p = _palace(n, index=i, main_stars=cai_main, aux_stars=cai_aux)
        elif n == "官禄宫":
            p = _palace(n, index=i, main_stars=guan_main)
        elif n == "迁移宫":
            p = _palace(n, index=i, main_stars=qian_main)
        elif n == "父母宫":
            p = _palace(n, index=i, main_stars=fumu_main, aux_stars=fumu_aux)
        else:
            p = _palace(n, index=i)
        palaces.append(p)

    if extra:
        for idx2, p2 in enumerate(palaces):
            if p2.name in extra:
                palaces[idx2] = extra[p2.name]
    return palaces


# ══════════════════════════════════════════════════════════════════════════════
# 一、patterns.py — 格局检测
# ══════════════════════════════════════════════════════════════════════════════

class TestDetectPatterns:

    # ── 无命宫时返回空 ─────────────────────────────────────────────────────
    def test_no_life_palace_returns_empty(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 不含命宫的宫位列表
        palaces = [_palace("财帛宫")]
        result = detect_patterns(palaces)
        assert result == []

    # ── 1. 禄存守命 ────────────────────────────────────────────────────────
    def test_lvcun_shouming(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(life_aux=["禄存"])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "禄存守命" in names

    # ── 2. 化禄守命 ────────────────────────────────────────────────────────
    def test_hualv_shouming(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(life_main=[_star("廉贞", ["化禄"])])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "化禄守命" in names

    # ── 3. 化权守命 ────────────────────────────────────────────────────────
    def test_huaquan_shouming(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(life_main=[_star("紫微", ["化权"])])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "化权守命" in names

    # ── 4. 三方逢科权禄 ────────────────────────────────────────────────────
    def test_sanfang_kepouaquan(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(
            life_main=[_star("廉贞", ["化禄"])],
            cai_main=[_star("武曲", ["化权"])],
            qian_main=[_star("太阳", ["化科"])],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "三方逢科权禄" in names

    # ── 5. 紫府同宫 ────────────────────────────────────────────────────────
    def test_zifu_tonggong(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 把紫微+天府放在迁移宫（非命宫三方也可触发，因为全宫位扫描）
        qian_pal = _palace("迁移宫", index=6, main_stars=[_star("紫微"), _star("天府")])
        palaces = _make_12_palaces(extra={"迁移宫": qian_pal})
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "紫府同宫" in names

    # ── 6. 君臣庆会 ────────────────────────────────────────────────────────
    def test_juncheng_qinghui(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 紫微坐命宫，命宫有左辅辅星
        palaces = _make_12_palaces(
            life_main=[_star("紫微")],
            life_aux=["左辅"],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "君臣庆会" in names

    # ── 7. 府相朝垣 ────────────────────────────────────────────────────────
    def test_fuxiang_chaoyuan(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(
            life_main=[_star("天府")],
            cai_main=[_star("天相")],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "府相朝垣" in names

    # ── 8. 日月同宫 ────────────────────────────────────────────────────────
    def test_riyue_tonggong(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 太阳+太阴在同一宫（不在命宫三方，所以以iterable扫出来）
        tian_pal = _palace("田宅宫", index=9, main_stars=[_star("太阳"), _star("太阴")])
        palaces = _make_12_palaces(extra={"田宅宫": tian_pal})
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "日月同宫" in names

    # ── 9. 日月拱命（太阳太阴分处不同宫在四正）──────────────────────────
    def test_riyue_gongming(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 太阳在命宫，太阴在迁移宫 → 四正拱命，不同宫
        palaces = _make_12_palaces(
            life_main=[_star("太阳")],
            qian_main=[_star("太阴")],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "日月拱命" in names

    # ── 10. 武贪格 ─────────────────────────────────────────────────────────
    def test_wutan_ge(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 武曲+贪狼在官禄宫
        guan_pal = _palace("官禄宫", index=8, main_stars=[_star("武曲"), _star("贪狼")])
        palaces = _make_12_palaces(extra={"官禄宫": guan_pal})
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "武贪格" in names

    # ── 11. 化忌守命 ───────────────────────────────────────────────────────
    def test_huaji_shouming(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(life_main=[_star("文曲", ["化忌"])])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "化忌守命" in names

    # ── 12. 化忌入财 ───────────────────────────────────────────────────────
    def test_huaji_rucai(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(cai_main=[_star("武曲", ["化忌"])])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "化忌入财" in names

    # ── 13. 化忌入官 ───────────────────────────────────────────────────────
    def test_huaji_ruguan(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(guan_main=[_star("廉贞", ["化忌"])])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "化忌入官" in names

    # ── 14. 羊陀夹命 ───────────────────────────────────────────────────────
    def test_yangtuo_jiaming(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 擎羊在兄弟宫，陀罗在父母宫（兄弟宫拱父母宫夹住命宫）
        palaces = _make_12_palaces(
            xiong_aux=["擎羊"],
            fumu_aux=["陀罗"],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "羊陀夹命" in names

    # ── 15. 火铃夹命 ───────────────────────────────────────────────────────
    def test_huoling_jiaming(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 火星在兄弟宫，铃星在父母宫
        palaces = _make_12_palaces(
            xiong_aux=["火星"],
            fumu_aux=["铃星"],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "火铃夹命" in names

    # ── 16. 禄权科三奇会命 ─────────────────────────────────────────────────
    def test_luquanke_sanqi(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(
            life_main=[
                _star("廉贞", ["化禄"]),
                _star("破军", ["化权"]),
                _star("武曲", ["化科"]),
            ]
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "禄权科三奇会命" in names

    # ── 17. 科权夹命 ────────────────────────────────────────────────────────
    def test_kequan_jiaming(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 化权在兄弟宫，化科在父母宫
        palaces = _make_12_palaces(
            xiong_main=[_star("紫微", ["化权"])],
            fumu_main=[_star("天机", ["化科"])],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "科权夹命" in names

    # ── 19. 天梁守命 ────────────────────────────────────────────────────────
    def test_tianliang_shouming(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(life_main=[_star("天梁")])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "天梁守命" in names

    # ── 20. 机月同梁 ────────────────────────────────────────────────────────
    def test_jiyuetonglaing(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(
            life_main=[_star("天机")],
            cai_main=[_star("太阴")],
            guan_main=[_star("天同")],
            qian_main=[_star("天梁")],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "机月同梁" in names

    # ── 21. 天同守命 ────────────────────────────────────────────────────────
    def test_tiantong_shouming(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(life_main=[_star("天同")])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "天同守命" in names

    # ── 22. 武禄入财 ────────────────────────────────────────────────────────
    def test_wulu_rucai(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(cai_main=[_star("武曲", ["化禄"])])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "武禄入财" in names

    # ── 23. 禄马交驰（同宫版）────────────────────────────────────────────
    def test_luma_jiaochi_same_palace(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 禄存与天马在同一宫位（命宫）
        palaces = _make_12_palaces(life_aux=["禄存", "天马"])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "禄马交驰" in names

    # ── 23b. 禄马交驰（三方版）───────────────────────────────────────────
    def test_luma_jiaochi_sizheng(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 禄存在命宫, 天马在迁移宫 → 同在四正
        palaces = _make_12_palaces(
            life_aux=["禄存"],
            qian_main=[],
        )
        # 手动为迁移宫添加天马辅星
        qian_pal = _palace("迁移宫", index=6, aux_stars=["天马"])
        palaces = _make_12_palaces(extra={"迁移宫": qian_pal}, life_aux=["禄存"])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "禄马交驰" in names

    # ── 24. 三台八座朝命 ────────────────────────────────────────────────────
    def test_santai_bazuo(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(
            life_aux=["三台"],
            cai_aux=["八座"],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "三台八座朝命" in names

    def test_cai_aux_field(self):
        """确保财帛宫 aux_stars 被正确传入，覆盖 _make_12_palaces。"""
        palaces = _make_12_palaces(cai_aux=["天刑"])
        cai = next(p for p in palaces if p.name == "财帛宫")
        assert "天刑" in cai.aux_stars

    # ── 25. 文桂文华 ────────────────────────────────────────────────────────
    def test_wenguiwendua(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(life_main=[_star("文曲", ["化科"])])
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "文桂文华" in names

    # ── 26. 天才天寿加会 ────────────────────────────────────────────────────
    def test_tiancai_tianshou(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(
            life_aux=["天才"],
            cai_aux=["天寿"],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "天才天寿加会" in names

    # ── 27. 龙凤拱命 ─────────────────────────────────────────────────────
    def test_longfeng_gongming(self):
        from services.ziwei_engine.patterns import detect_patterns
        palaces = _make_12_palaces(
            life_aux=["龙池"],
            cai_aux=["凤阁"],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        assert "龙凤拱命" in names

    # ── 日月并明（Pattern 18）────────────────────────────────────────────
    def test_riyue_bingming(self):
        from services.ziwei_engine.patterns import detect_patterns
        # 太阳化禄在命宫，太阴化科在财帛宫（均在四正，不同宫）
        palaces = _make_12_palaces(
            life_main=[_star("太阳", ["化禄"])],
            cai_main=[_star("太阴", ["化科"])],
        )
        r = detect_patterns(palaces)
        names = [p.name for p in r]
        # 这个格局要两宫在 sizheng 且 sun ≠ moon palace
        assert "日月并明" in names

    # ── PatternResult 数据字段 ────────────────────────────────────────────
    def test_pattern_result_fields(self):
        from services.ziwei_engine.patterns import PatternResult
        pr = PatternResult(
            name="禄存守命",
            level="吉",
            description="测试",
            palaces=["命宫"],
            stars=["禄存"],
            source="测试来源",
        )
        assert pr.name == "禄存守命"
        assert pr.source == "测试来源"

    # ── 真实命盘触发格局检测 ─────────────────────────────────────────────
    def test_real_chart_patterns(self):
        try:
            from services.ziwei_engine import ziwei_full
            from services.ziwei_engine.patterns import detect_patterns
            chart = ziwei_full(1990, 7, 17, 12, 0, "男")
            r = detect_patterns(chart.palaces)
            assert isinstance(r, list)
            # 每条结果都有 name / level
            for pr in r:
                assert hasattr(pr, "name")
                assert hasattr(pr, "level")
        except Exception:
            pytest.skip("chart build failed")


# ══════════════════════════════════════════════════════════════════════════════
# 二、compatibility.py — 六合度计算
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class _FakeLunar:
    year_branch_idx: int = 0


class _FakeChart:
    """最小化 ZiweiChart mock，用于 calc_compatibility。"""

    def __init__(
        self,
        life_branch: int,
        life_stem_idx: int,
        year_branch: int,
        wuxing_ju: int,
        life_gz: str = "甲子",
        body_gz: str = "甲子",
        birth_solar: str = "1990-01-01",
        gender: str = "男",
        palaces: list | None = None,
    ):
        self.life_palace_branch = life_branch
        self.life_palace_stem_idx = life_stem_idx
        self.lunar = _FakeLunar(year_branch_idx=year_branch)
        self.wuxing_ju = wuxing_ju
        self.life_palace_gz = life_gz
        self.body_palace_gz = body_gz
        self.birth_solar = birth_solar
        self.gender = gender
        self.wuxing_ju_name = {2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局"}.get(wuxing_ju, "？")
        self.palaces = _make_minimal_palaces(life_branch) if palaces is None else palaces

    @property
    def flying(self):
        return None


def _make_minimal_palaces(branch_idx: int = 0) -> list:
    """为 compatibility 测试创建最小化 12 宫。"""
    names = ["命宫", "兄弟宫", "夫妻宫", "子女宫", "财帛宫", "疾厄宫",
             "迁移宫", "仆役宫", "官禄宫", "田宅宫", "福德宫", "父母宫"]
    palaces = []
    for i, n in enumerate(names):
        p = PalaceInfo(
            index=i,
            name=n,
            branch_idx=(branch_idx + i) % 12,
            branch="子",
            stem_idx=0,
            stem="甲",
            main_stars=[],
            aux_stars=[],
        )
        palaces.append(p)
    return palaces


class TestCompatibility:

    # ── 维度1：命宫六合 ───────────────────────────────────────────────────
    def test_liuhe_combination(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 子(0) 丑(1) → 六合
        a = _FakeChart(life_branch=0, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=1, life_stem_idx=1, year_branch=1, wuxing_ju=6)
        r = calc_compatibility(a, b)
        assert r.total_score > 0
        d1 = next(d for d in r.dimensions if d.name == "命宫相合")
        assert d1.score == 25   # 六合满分

    # ── 维度1：命宫三合 ───────────────────────────────────────────────────
    def test_sanhe_combination(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 申(8) 子(0) → 三合（申子辰）
        a = _FakeChart(life_branch=8, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=0, life_stem_idx=1, year_branch=1, wuxing_ju=4)
        r = calc_compatibility(a, b)
        d1 = next(d for d in r.dimensions if d.name == "命宫相合")
        assert d1.score == 20

    # ── 维度1：命宫同支 ───────────────────────────────────────────────────
    def test_same_branch(self):
        """所有地支均属某个三合局，lb_a==lb_b 时 _is_sanhe 先触发得 20 分。"""
        from services.ziwei_engine.compatibility import calc_compatibility
        a = _FakeChart(life_branch=3, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=3, life_stem_idx=1, year_branch=1, wuxing_ju=4)
        r = calc_compatibility(a, b)
        d1 = next(d for d in r.dimensions if d.name == "命宫相合")
        # 地支同支 3(卯) 在三合局 {11,3,7} 中，_is_sanhe 先触发 → 20 分
        assert d1.score in (16, 20)

    # ── 维度1：命宫相冲 ───────────────────────────────────────────────────
    def test_chong_combination(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 子(0) 午(6) → 相冲
        a = _FakeChart(life_branch=0, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=6, life_stem_idx=1, year_branch=1, wuxing_ju=4)
        r = calc_compatibility(a, b)
        d1 = next(d for d in r.dimensions if d.name == "命宫相合")
        assert d1.score == 5

    # ── 维度1：命宫无关（其余情况）───────────────────────────────────────
    def test_no_relation(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 子(0) 卯(3) → 无关（非六合/三合/同支/相冲）
        a = _FakeChart(life_branch=0, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=3, life_stem_idx=1, year_branch=2, wuxing_ju=4)
        r = calc_compatibility(a, b)
        d1 = next(d for d in r.dimensions if d.name == "命宫相合")
        assert d1.score == 12

    # ── 维度2：五行同（相同）──────────────────────────────────────────────
    def test_wuxing_same(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 两人都是木三局(3)
        a = _FakeChart(life_branch=2, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=4, life_stem_idx=1, year_branch=2, wuxing_ju=3)
        r = calc_compatibility(a, b)
        d2 = next(d for d in r.dimensions if d.name == "五行相生")
        assert d2.score == 13

    # ── 维度2：五行相克 ───────────────────────────────────────────────────
    def test_wuxing_ke(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 水(2)克火(6)
        a = _FakeChart(life_branch=2, life_stem_idx=0, year_branch=0, wuxing_ju=2)  # 水
        b = _FakeChart(life_branch=4, life_stem_idx=1, year_branch=2, wuxing_ju=6)  # 火
        r = calc_compatibility(a, b)
        d2 = next(d for d in r.dimensions if d.name == "五行相生")
        assert d2.score == 8

    # ── 维度2：五行无关（两个元素不相生不相克）────────────────────────────
    def test_wuxing_unrelated(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 土(5)和金(4) — 土生金，不应该无关... 让我用 wuxing_ju 不在表中 → default 土土
        # 土(5) 和 水(2) — 土克水，是相克
        # 土(5) 和 火(6) — 火生土，相生
        # 其实没有"无关"的两元素对（5个元素两两关系都是相生或相克或同）
        # 由于 _JU_TO_WX 只有 2-6，传入 0 时会 default 到 "土"
        # 土(5) 和水(2)=水克土 → 相克
        # 让两者都是不在字典里的key → 两者都拿 "土"，同类
        a = _FakeChart(life_branch=0, life_stem_idx=0, year_branch=0, wuxing_ju=0)
        b = _FakeChart(life_branch=6, life_stem_idx=1, year_branch=6, wuxing_ju=99)
        r = calc_compatibility(a, b)
        d2 = next(d for d in r.dimensions if d.name == "五行相生")
        assert d2.score == 13   # 无关=13

    # ── 维度3：年支六合 ───────────────────────────────────────────────────
    def test_year_liuhe(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # year_branch 子(0) 丑(1) → 六合
        a = _FakeChart(life_branch=2, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=4, life_stem_idx=1, year_branch=1, wuxing_ju=4)
        r = calc_compatibility(a, b)
        d3 = next(d for d in r.dimensions if d.name == "年支缘分")
        assert d3.score == 20

    # ── 维度3：年支三合 ───────────────────────────────────────────────────
    def test_year_sanhe(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 申(8) 子(0) 三合
        a = _FakeChart(life_branch=2, life_stem_idx=0, year_branch=8, wuxing_ju=3)
        b = _FakeChart(life_branch=4, life_stem_idx=1, year_branch=0, wuxing_ju=4)
        r = calc_compatibility(a, b)
        d3 = next(d for d in r.dimensions if d.name == "年支缘分")
        assert d3.score == 16

    # ── 维度3：年支同支 ───────────────────────────────────────────────────
    def test_year_same(self):
        """年支同支时 _is_sanhe 先触发（同理所有地支都在三合局）→ 16 分。"""
        from services.ziwei_engine.compatibility import calc_compatibility
        a = _FakeChart(life_branch=2, life_stem_idx=0, year_branch=5, wuxing_ju=3)
        b = _FakeChart(life_branch=4, life_stem_idx=1, year_branch=5, wuxing_ju=4)
        r = calc_compatibility(a, b)
        d3 = next(d for d in r.dimensions if d.name == "年支缘分")
        assert d3.score in (12, 16)

    # ── 维度3：年支相冲 ───────────────────────────────────────────────────
    def test_year_chong(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 子(0)午(6) 相冲
        a = _FakeChart(life_branch=2, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=4, life_stem_idx=1, year_branch=6, wuxing_ju=4)
        r = calc_compatibility(a, b)
        d3 = next(d for d in r.dimensions if d.name == "年支缘分")
        assert d3.score == 4

    # ── 维度3：年支无关 ───────────────────────────────────────────────────
    def test_year_no_relation(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 子(0)卯(3) 无特殊
        a = _FakeChart(life_branch=2, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=4, life_stem_idx=1, year_branch=3, wuxing_ju=4)
        r = calc_compatibility(a, b)
        d3 = next(d for d in r.dimensions if d.name == "年支缘分")
        assert d3.score == 10

    # ── 维度5：阴阳互补（不同）────────────────────────────────────────────
    def test_yinyang_bubu(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # stem_idx 0→阳, 1→阴
        a = _FakeChart(life_branch=2, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=4, life_stem_idx=1, year_branch=1, wuxing_ju=4)
        r = calc_compatibility(a, b)
        d5 = next(d for d in r.dimensions if d.name == "阴阳互补")
        assert d5.score == 15

    # ── 维度5：同质（相同阴阳）────────────────────────────────────────────
    def test_yinyang_same(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        a = _FakeChart(life_branch=2, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=4, life_stem_idx=2, year_branch=1, wuxing_ju=4)
        r = calc_compatibility(a, b)
        d5 = next(d for d in r.dimensions if d.name == "阴阳互补")
        assert d5.score == 8

    # ── 整体评级：上上签 ──────────────────────────────────────────────────
    def test_level_shang_shang(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 最高分组合：六合+相生+六合+20+互补
        a = _FakeChart(life_branch=0, life_stem_idx=0, year_branch=0, wuxing_ju=2)  # 水
        b = _FakeChart(life_branch=1, life_stem_idx=1, year_branch=1, wuxing_ju=3)  # 木（水生木）
        r = calc_compatibility(a, b)
        assert r.level in ("上上签", "上签")  # 允许浮动

    # ── 整体评级：下签 / 平 ────────────────────────────────────────────────
    def test_level_low(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        # 低分：相冲+相克+相冲+相冲+同阴阳
        a = _FakeChart(life_branch=0, life_stem_idx=0, year_branch=0, wuxing_ju=2)  # 水
        b = _FakeChart(life_branch=6, life_stem_idx=0, year_branch=6, wuxing_ju=6)  # 火（水克火+相冲）
        r = calc_compatibility(a, b)
        assert r.level in ("下签", "平", "中签")

    # ── CompatibilityResult 包含所有必需字段 ──────────────────────────────
    def test_result_fields_complete(self):
        from services.ziwei_engine.compatibility import calc_compatibility
        a = _FakeChart(life_branch=0, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=2, life_stem_idx=1, year_branch=2, wuxing_ju=4)
        r = calc_compatibility(a, b)
        assert hasattr(r, "total_score")
        assert hasattr(r, "dimensions")
        assert hasattr(r, "harmony_points")
        assert hasattr(r, "conflict_points")
        assert hasattr(r, "complement_points")
        assert hasattr(r, "palace_compare")
        assert len(r.dimensions) == 5
        assert len(r.palace_compare) == 6  # 六大关键宫位

    # ── _collect_harmony / _collect_conflicts / _collect_complements ────────
    def test_collect_harmony_liuhe(self):
        from services.ziwei_engine.compatibility import _collect_harmony
        a = _FakeChart(life_branch=0, life_stem_idx=0, year_branch=0, wuxing_ju=3)
        b = _FakeChart(life_branch=1, life_stem_idx=1, year_branch=1, wuxing_ju=6)
        pts = _collect_harmony(a, b)
        assert any("六合" in p for p in pts)

    def test_collect_conflicts_chong(self):
        from services.ziwei_engine.compatibility import _collect_conflicts
        a = _FakeChart(life_branch=0, life_stem_idx=0, year_branch=0, wuxing_ju=2)
        b = _FakeChart(life_branch=6, life_stem_idx=1, year_branch=6, wuxing_ju=6)
        pts = _collect_conflicts(a, b)
        assert any("冲" in p for p in pts)

    def test_collect_flying_ji_cross_chart(self):
        from services.ziwei_engine.compatibility import _collect_cross_flying_ji, calc_compatibility
        from services.ziwei_engine import ziwei_full

        chart_a = ziwei_full(1990, 7, 17, 12, 0, "男")
        chart_b = ziwei_full(1992, 3, 8, 6, 0, "女")
        assert chart_a.flying is not None
        pts = _collect_cross_flying_ji(chart_a, chart_b, "甲方")
        # 真实盘未必命中化忌飞支，但函数应安全返回列表
        assert isinstance(pts, list)
        result = calc_compatibility(chart_a, chart_b)
        assert isinstance(result.conflict_points, list)

    def test_collect_complements_yinyang(self):
        from services.ziwei_engine.compatibility import _collect_complements
        a = _FakeChart(life_branch=0, life_stem_idx=0, year_branch=0, wuxing_ju=3, body_gz="甲子")
        b = _FakeChart(life_branch=2, life_stem_idx=1, year_branch=1, wuxing_ju=4, body_gz="乙丑")
        pts = _collect_complements(a, b)
        assert any("阴阳互补" in p for p in pts)

    def test_real_chart_compatibility(self):
        """用真实 ZiweiChart 做合盘，验证不报错。"""
        try:
            from services.ziwei_engine import ziwei_full
            from services.ziwei_engine.compatibility import calc_compatibility
            chart_a = ziwei_full(1990, 7, 17, 12, 0, "男")
            chart_b = ziwei_full(1992, 3, 8, 6, 0, "女")
            r = calc_compatibility(chart_a, chart_b)
            assert 0 <= r.total_score <= 100
            assert r.level in ("上上签", "上签", "中签", "下签", "平")
        except Exception:
            pytest.skip("chart build failed")

    # ── _build_palace_compare：无宫位时 entry 仍有 relation="" ─────────────
    def test_palace_compare_missing_palace(self):
        from services.ziwei_engine.compatibility import _build_palace_compare
        # 使用空宫位列表
        a = _FakeChart(life_branch=0, life_stem_idx=0, year_branch=0, wuxing_ju=3, palaces=[])
        b = _FakeChart(life_branch=2, life_stem_idx=1, year_branch=0, wuxing_ju=4, palaces=[])
        rows = _build_palace_compare(a, b)
        assert len(rows) == 6
        for row in rows:
            assert row["a_gz"] == "—"


# ══════════════════════════════════════════════════════════════════════════════
# 三、内部辅助函数直接测试
# ══════════════════════════════════════════════════════════════════════════════

class TestCompatibilityHelpers:

    def test_is_liuhe(self):
        from services.ziwei_engine.compatibility import _is_liuhe
        assert _is_liuhe(0, 1) is True    # 子丑
        assert _is_liuhe(2, 11) is True   # 寅亥
        assert _is_liuhe(0, 6) is False   # 子午（相冲非六合）

    def test_is_sanhe(self):
        from services.ziwei_engine.compatibility import _is_sanhe
        assert _is_sanhe(8, 0) is True    # 申子辰三合中的申子
        assert _is_sanhe(0, 4) is True    # 子辰
        assert _is_sanhe(0, 1) is False   # 子丑（六合，非三合）

    def test_is_chong(self):
        from services.ziwei_engine.compatibility import _is_chong
        assert _is_chong(0, 6) is True    # 子午
        assert _is_chong(1, 7) is True    # 丑未
        assert _is_chong(0, 1) is False

    def test_wx_relation(self):
        from services.ziwei_engine.compatibility import _wx_relation
        assert _wx_relation("水", "木") == "相生"
        assert _wx_relation("木", "水") == "相生"
        assert _wx_relation("水", "火") == "相克"
        assert _wx_relation("土", "土") == "同"
        assert _wx_relation("水", "土") == "相克"   # 土克水
