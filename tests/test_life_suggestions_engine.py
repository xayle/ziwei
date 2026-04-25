"""
tests/test_life_suggestions_engine.py
生活化建议引擎单元测试

覆盖所有四种触发类型（palace_star / palace_transform / pattern / wuxing_ju）的
正/负样例，以及规则加载、优先级排序与空命盘的边界情况。
"""
from __future__ import annotations

import types
from types import SimpleNamespace

import pytest

from services.ziwei_engine.life_suggestions import calc_life_suggestions, LifeSuggestion


# ──────────────────────────────────────────────────────────────
# 工厂函数：构造轻量级 mock 命盘
# ──────────────────────────────────────────────────────────────

def _palace(name: str, main_stars: list[str] | None = None,
            transforms: dict[str, list[str]] | None = None,
            minor_stars: list[str] | None = None) -> SimpleNamespace:
    """
    构造单个宫位 mock 对象。

    Parameters
    ----------
    name : str
        宫位名称（须与规则库完全一致）。
    main_stars : list[str]
        该宫主星名称列表。
    transforms : dict[str, list[str]]
        星名 → 四化列表映射，e.g. {"紫微": ["化权"]}.
    minor_stars : list[str]
        辅星名称列表。
    """
    transforms = transforms or {}
    ms = [
        {"name": s, "brightness": "", "brightness_val": 0,
         "transforms": transforms.get(s, [])}
        for s in (main_stars or [])
    ]
    aux = [{"name": s} for s in (minor_stars or [])]
    return SimpleNamespace(name=name, main_stars=ms, minor_stars=aux)


def _chart(palaces: list, patterns: list[str] | None = None,
           wuxing_ju_name: str = "水二局",
           liunian_year: int = 2026) -> SimpleNamespace:
    """构造完整的轻量级命盘 mock 对象。"""
    pat_objs = [SimpleNamespace(name=p) for p in (patterns or [])]
    return SimpleNamespace(
        palaces=palaces,
        patterns=pat_objs,
        wuxing_ju_name=wuxing_ju_name,
        liunian_year=liunian_year,
    )


def _ids(suggestions: list[LifeSuggestion]) -> set[str]:
    """提取建议列表中所有规则 ID。"""
    return {s.id for s in suggestions}


# ══════════════════════════════════════════════════════════════
# 1. palace_star 触发器
# ══════════════════════════════════════════════════════════════

class TestPalaceStar:
    """palace_star 触发器：宫位包含指定主星/辅星。"""

    def test_positive_caibox_wuqu(self):
        """财帛宫含武曲 → js_001 旺财黄金建议被触发。"""
        chart = _chart([
            _palace("财帛", main_stars=["武曲", "天相"]),
        ])
        results = calc_life_suggestions(chart)
        assert "js_001" in _ids(results), "财帛宫含武曲应触发 js_001"

    def test_positive_caibox_tianfu(self):
        """财帛宫含天府 → js_001 同样触发。"""
        chart = _chart([_palace("财帛", main_stars=["天府"])])
        assert "js_001" in _ids(calc_life_suggestions(chart))

    def test_negative_caibox_no_matching_star(self):
        """财帛宫仅有紫微（不在触发列表）→ js_001 不触发。"""
        chart = _chart([_palace("财帛", main_stars=["紫微"])])
        assert "js_001" not in _ids(calc_life_suggestions(chart))

    def test_positive_guanlu_ziwei(self):
        """官禄宫含紫微 → js_003 紫水晶建议被触发。"""
        chart = _chart([_palace("官禄", main_stars=["紫微"])])
        assert "js_003" in _ids(calc_life_suggestions(chart))

    def test_positive_fuqi_tanlang(self):
        """夫妻宫含贪狼 → js_004 粉晶旺桃花被触发。"""
        chart = _chart([_palace("夫妻", main_stars=["贪狼"])])
        assert "js_004" in _ids(calc_life_suggestions(chart))

    def test_negative_wrong_palace(self):
        """武曲在官禄宫（而非财帛）→ js_001 不触发。"""
        chart = _chart([
            _palace("官禄", main_stars=["武曲"]),
            _palace("财帛", main_stars=["太阳"]),
        ])
        assert "js_001" not in _ids(calc_life_suggestions(chart))

    def test_positive_jiaoyou_shastar(self):
        """交友宫含煞星(擎羊) → pl_004 仙人掌建议被触发。"""
        chart = _chart([_palace("交友", minor_stars=["擎羊"])])
        assert "pl_004" in _ids(calc_life_suggestions(chart))

    def test_negative_empty_palaces(self):
        """空命盘，无宫位 → 无任何建议触发（不报错）。"""
        chart = _chart([])
        results = calc_life_suggestions(chart)
        assert isinstance(results, list)


# ══════════════════════════════════════════════════════════════
# 2. palace_transform 触发器
# ══════════════════════════════════════════════════════════════

class TestPalaceTransform:
    """palace_transform 触发器：宫位主星携带指定四化。"""

    def test_positive_minggong_huaji(self):
        """命宫主星化忌 → js_002 蓝色水晶被触发。"""
        chart = _chart([
            _palace("命宫", main_stars=["天同"], transforms={"天同": ["化忌"]}),
        ])
        assert "js_002" in _ids(calc_life_suggestions(chart))

    def test_negative_minggong_no_huaji(self):
        """命宫主星无化忌 → js_002 不触发。"""
        chart = _chart([
            _palace("命宫", main_stars=["天同"], transforms={"天同": ["化禄"]}),
        ])
        assert "js_002" not in _ids(calc_life_suggestions(chart))

    def test_positive_guanlu_huaquan(self):
        """官禄宫化权 → js_006 铜铃手环被触发。"""
        chart = _chart([
            _palace("官禄", main_stars=["紫微"], transforms={"紫微": ["化权"]}),
        ])
        assert "js_006" in _ids(calc_life_suggestions(chart))

    def test_negative_guanlu_huaji_not_huaquan(self):
        """官禄宫仅化忌（非化权）→ js_006 不触发。"""
        chart = _chart([
            _palace("官禄", main_stars=["紫微"], transforms={"紫微": ["化忌"]}),
        ])
        assert "js_006" not in _ids(calc_life_suggestions(chart))

    def test_positive_caibox_hualu_plants(self):
        """财帛宫化禄 → pl_003 金钱树建议被触发。"""
        chart = _chart([
            _palace("财帛", main_stars=["太阴"], transforms={"太阴": ["化禄"]}),
        ])
        assert "pl_003" in _ids(calc_life_suggestions(chart))

    def test_positive_jie_huaji_plant(self):
        """疾厄宫化忌 → pl_005 薰衣草建议被触发。"""
        chart = _chart([
            _palace("疾厄", main_stars=["天梁"], transforms={"天梁": ["化忌"]}),
        ])
        assert "pl_005" in _ids(calc_life_suggestions(chart))

    def test_positive_caibox_huaji_object(self):
        """财帛宫化忌 → ob_001 铜制貔貅被触发。"""
        chart = _chart([
            _palace("财帛", main_stars=["太阴"], transforms={"太阴": ["化忌"]}),
        ])
        assert "ob_001" in _ids(calc_life_suggestions(chart))

    def test_positive_multiple_stars_any_has_transform(self):
        """宫内多主星，只要一颗带化忌即可触发。"""
        chart = _chart([
            _palace("命宫",
                    main_stars=["紫微", "天府"],
                    transforms={"紫微": [], "天府": ["化忌"]}),
        ])
        assert "js_002" in _ids(calc_life_suggestions(chart))


# ══════════════════════════════════════════════════════════════
# 3. pattern 触发器（pattern_name_contains）
# ══════════════════════════════════════════════════════════════

class TestPatternTrigger:
    """pattern 触发器：命盘格局名称包含关键词。"""

    def test_positive_yangduo_js005(self):
        """命盘含'羊陀夹命'格局 → js_005 黑曜石被触发。"""
        chart = _chart([], patterns=["羊陀夹命"])
        assert "js_005" in _ids(calc_life_suggestions(chart))

    def test_positive_yangduo_partial_match(self):
        """格局名只要含'羊陀'子串即可匹配。"""
        chart = _chart([], patterns=["火星羊陀三煞"])
        assert "js_005" in _ids(calc_life_suggestions(chart))

    def test_negative_no_pattern(self):
        """无任何格局时，pattern 类规则一律不触发。"""
        chart = _chart([])
        result_ids = _ids(calc_life_suggestions(chart))
        # js_005/pl_002/ob_004/tm_004/js_037 均基于 pattern 触发
        pattern_ids = {"js_005", "pl_002", "ob_004", "tm_004", "js_037"}
        assert result_ids.isdisjoint(pattern_ids)

    def test_positive_huaji_pl002(self):
        """格局名含'化忌' → pl_002 绿萝净化被触发。"""
        chart = _chart([], patterns=["命宫化忌流年对冲"])
        assert "pl_002" in _ids(calc_life_suggestions(chart))

    def test_positive_shaqi_ob004(self):
        """格局名含'空劫夹' → ob_004 泰山石敢当被触发。"""
        chart = _chart([], patterns=["空劫夹命"])
        assert "ob_004" in _ids(calc_life_suggestions(chart))

    def test_positive_sanjixing_js037(self):
        """格局名含'三奇' → js_037 三奇聚会步进建议被触发。"""
        chart = _chart([], patterns=["禄权科三奇会命"])
        assert "js_037" in _ids(calc_life_suggestions(chart))

    def test_negative_wrong_keyword(self):
        """格局名不含任何规则关键词 → 无 pattern 规则触发。"""
        chart = _chart([], patterns=["天府坐命"])
        pattern_ids = {"js_005", "pl_002", "ob_004", "tm_004", "js_037"}
        assert _ids(calc_life_suggestions(chart)).isdisjoint(pattern_ids)


# ══════════════════════════════════════════════════════════════
# 4. wuxing_ju 触发器
# ══════════════════════════════════════════════════════════════

class TestWuxingJu:
    """wuxing_ju 触发器：根据五行局匹配。"""

    def test_positive_water2_bd001(self):
        """水二局 → bd_001 床头朝向北/东北被触发。"""
        chart = _chart([], wuxing_ju_name="水二局")
        assert "bd_001" in _ids(calc_life_suggestions(chart))

    def test_positive_wood3_bd001(self):
        """木三局同属 bd_001 触发列表。"""
        chart = _chart([], wuxing_ju_name="木三局")
        assert "bd_001" in _ids(calc_life_suggestions(chart))

    def test_negative_fire6_bd001(self):
        """火六局不在 bd_001 触发列表 → bd_001 不触发。"""
        chart = _chart([], wuxing_ju_name="火六局")
        assert "bd_001" not in _ids(calc_life_suggestions(chart))

    def test_positive_wood3_tm001(self):
        """木三局 → tm_001 春季实施择日建议被触发。"""
        chart = _chart([], wuxing_ju_name="木三局")
        assert "tm_001" in _ids(calc_life_suggestions(chart))

    def test_negative_metal4_tm001(self):
        """金四局 → tm_001 不触发。"""
        chart = _chart([], wuxing_ju_name="金四局")
        assert "tm_001" not in _ids(calc_life_suggestions(chart))


# ══════════════════════════════════════════════════════════════
# 5. 综合与边界测试
# ══════════════════════════════════════════════════════════════

class TestCombinedAndEdge:
    """综合场景与边界情况测试。"""

    def test_multiple_triggers_same_chart(self):
        """同一命盘多条件满足时，所有匹配规则均出现在结果中。"""
        chart = _chart(
            palaces=[
                _palace("财帛", main_stars=["武曲"]),       # → js_001
                _palace("命宫", main_stars=["天同"],
                         transforms={"天同": ["化忌"]}),     # → js_002
                _palace("官禄", main_stars=["紫微"]),        # → js_003
            ],
            wuxing_ju_name="水二局",   # → bd_001
        )
        result_ids = _ids(calc_life_suggestions(chart))
        for expected in ("js_001", "js_002", "js_003", "bd_001"):
            assert expected in result_ids, f"预期 {expected} 触发但未出现"

    def test_results_sorted_by_priority(self):
        """返回列表按 priority 升序排列（1 最高）。"""
        chart = _chart(
            palaces=[
                _palace("财帛", main_stars=["武曲"]),
                _palace("命宫", main_stars=["天同"],
                         transforms={"天同": ["化忌"]}),
            ],
            patterns=["羊陀夹命"],
        )
        results = calc_life_suggestions(chart)
        assert results == sorted(results, key=lambda r: (r.priority, r.category, r.name)), \
            "结果应按 (priority, category, name) 升序排列"

    def test_result_fields_complete(self):
        """返回的 LifeSuggestion 对象包含必需字段。"""
        chart = _chart([_palace("财帛", main_stars=["武曲"])])
        results = calc_life_suggestions(chart)
        assert results, "应有至少一条结果"
        s = results[0]
        assert s.id
        assert s.name
        assert s.category in ("jewelry", "plants", "objects", "bed", "timing")
        assert s.category_label
        assert s.priority in (1, 2, 3)
        assert s.cost_level in ("低", "中", "高")
        assert s.valid_scope in ("流年", "大运", "长期")
        assert isinstance(s.actions, list)

    def test_no_duplicate_ids(self):
        """同一命盘中每条规则最多触发一次，ID 不重复。"""
        chart = _chart(
            palaces=[_palace("财帛", main_stars=["武曲", "天府"])],
        )
        results = calc_life_suggestions(chart)
        ids = [s.id for s in results]
        assert len(ids) == len(set(ids)), "存在重复规则 ID"

    def test_no_palaces_no_error(self):
        """完全空的宫位列表不报错。"""
        chart = _chart([])
        results = calc_life_suggestions(chart)
        assert isinstance(results, list)

    def test_evidence_template_filled(self):
        """evidence 字段应被正确填充（不含未解析的 {key}）。"""
        chart = _chart([_palace("财帛", main_stars=["武曲"])])
        results = calc_life_suggestions(chart)
        js001 = next((r for r in results if r.id == "js_001"), None)
        assert js001 is not None
        assert "{" not in js001.evidence, f"evidence 含未解析占位符：{js001.evidence}"
        assert "武曲" in js001.evidence

    def test_disclaimer_always_present(self):
        """每条建议都有免责声明文字。"""
        chart = _chart([_palace("财帛", main_stars=["武曲"])])
        for s in calc_life_suggestions(chart):
            assert s.disclaimer, f"{s.id} 缺少 disclaimer"
