"""
tests/test_remedies_engine.py
破局建议引擎单元测试

覆盖所有三种触发类型（palace_hua / pattern / pattern_and_liunian）的
正/负样例，以及规则加载、优先级排序与边界情况。
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from services.ziwei_engine.remedies import calc_remedies, RemedyResult


# ──────────────────────────────────────────────────────────────
# 工厂函数：构造轻量级 mock 命盘
# ──────────────────────────────────────────────────────────────

def _palace(name: str, stars: list[tuple[str, list[str]]] | None = None) -> SimpleNamespace:
    """
    构造宫位 mock 对象。

    Parameters
    ----------
    name : str
        宫位名称（须与 remedies_rules.json 完全一致，含"宫"字）。
    stars : list of (star_name, transforms)
        主星及其四化列表，例如 [("天同", ["化忌"])] 。
    """
    ms = [
        {"name": sn, "brightness": "", "brightness_val": 0, "transforms": tx}
        for sn, tx in (stars or [])
    ]
    return SimpleNamespace(name=name, main_stars=ms)


def _chart(palaces: list, patterns: list[str] | None = None,
           liunian_year: int = 2026) -> SimpleNamespace:
    """构造轻量级命盘 mock 对象。"""
    pat_objs = [SimpleNamespace(name=p) for p in (patterns or [])]
    dayun = SimpleNamespace(items=[])
    return SimpleNamespace(
        palaces=palaces,
        patterns=pat_objs,
        liunian_year=liunian_year,
        dayun=dayun,
    )


def _ids(remedies: list[RemedyResult]) -> set[str]:
    return {r.id for r in remedies}


# ══════════════════════════════════════════════════════════════
# 1. palace_hua 触发器
# ══════════════════════════════════════════════════════════════

class TestPalaceHua:
    """palace_hua 触发器：宫位主星携带指定四化。"""

    def test_positive_minggong_huaji(self):
        """命宫主星化忌 → remedy_001 修心积德被触发。"""
        chart = _chart([
            _palace("命宫", [("天同", ["化忌"])]),
        ])
        assert "remedy_001" in _ids(calc_remedies(chart))

    def test_negative_minggong_no_huaji(self):
        """命宫主星无化忌 → remedy_001 不触发。"""
        chart = _chart([
            _palace("命宫", [("天同", ["化禄"])]),
        ])
        assert "remedy_001" not in _ids(calc_remedies(chart))

    def test_positive_caibo_huaji(self):
        """财帛宫主星化忌 → remedy_002 理财防损被触发。"""
        chart = _chart([
            _palace("财帛宫", [("太阴", ["化忌"])]),
        ])
        assert "remedy_002" in _ids(calc_remedies(chart))

    def test_negative_caibo_no_huaji(self):
        """财帛宫主星仅化权 → remedy_002 不触发。"""
        chart = _chart([
            _palace("财帛宫", [("太阴", ["化权"])]),
        ])
        assert "remedy_002" not in _ids(calc_remedies(chart))

    def test_positive_guanlu_huaji(self):
        """官禄宫主星化忌 → remedy_003 职场韬光被触发。"""
        chart = _chart([
            _palace("官禄宫", [("紫微", ["化忌"])]),
        ])
        assert "remedy_003" in _ids(calc_remedies(chart))

    def test_positive_fuqi_huaji(self):
        """夫妻宫主星化忌 → remedy_005 感情维护被触发。"""
        chart = _chart([
            _palace("夫妻宫", [("天梁", ["化忌"])]),
        ])
        assert "remedy_005" in _ids(calc_remedies(chart))

    def test_positive_jie_huaji(self):
        """疾厄宫主星化忌 → remedy_006 健康防护被触发。"""
        chart = _chart([
            _palace("疾厄宫", [("廉贞", ["化忌"])]),
        ])
        assert "remedy_006" in _ids(calc_remedies(chart))

    def test_positive_multiple_stars_one_has_huaji(self):
        """宫内多主星，只有其中一颗化忌即可触发。"""
        chart = _chart([
            _palace("命宫", [("紫微", []), ("天府", ["化忌"])]),
        ])
        assert "remedy_001" in _ids(calc_remedies(chart))

    def test_negative_empty_palace(self):
        """宫位无主星时，palace_hua 规则不触发。"""
        chart = _chart([_palace("命宫")])
        assert "remedy_001" not in _ids(calc_remedies(chart))

    def test_negative_wrong_palace_name(self):
        """星曜化忌但宫位名称不匹配 → 不触发对应规则。"""
        # 命宫有化忌，但财帛宫规则 (remedy_002) 需要 "财帛宫" 化忌
        chart = _chart([
            _palace("命宫", [("太阴", ["化忌"])]),
        ])
        assert "remedy_002" not in _ids(calc_remedies(chart))

    def test_evidence_contains_star_name(self):
        """evidence 字段应包含触发该规则的星名。"""
        chart = _chart([
            _palace("命宫", [("天同", ["化忌"])]),
        ])
        results = calc_remedies(chart)
        r = next(x for x in results if x.id == "remedy_001")
        assert "天同" in r.evidence, f"evidence 应含主星名，实际为：{r.evidence!r}"


# ══════════════════════════════════════════════════════════════
# 2. pattern 触发器（精确匹配格局名）
# ══════════════════════════════════════════════════════════════

class TestPatternTrigger:
    """pattern 触发器：命盘格局名称与规则 pattern_name 精确匹配。"""

    def test_positive_yangtuo_jiaming(self):
        """命盘含'羊陀夹命'格局 → remedy_008 韧性处世被触发。"""
        chart = _chart([], patterns=["羊陀夹命"])
        assert "remedy_008" in _ids(calc_remedies(chart))

    def test_negative_yangtuo_partial(self):
        """格局名仅含子串但不完全匹配 → remedy_008 不触发（精确匹配）。"""
        chart = _chart([], patterns=["羊陀"])
        assert "remedy_008" not in _ids(calc_remedies(chart))

    def test_positive_huoling_jiaming(self):
        """命盘含'火铃夹命'→ remedy_009 修身控情被触发。"""
        chart = _chart([], patterns=["火铃夹命"])
        assert "remedy_009" in _ids(calc_remedies(chart))

    def test_positive_kongjie_jiaming(self):
        """命盘含'空劫夹命'→ remedy_010 防虚耗财被触发。"""
        chart = _chart([], patterns=["空劫夹命"])
        assert "remedy_010" in _ids(calc_remedies(chart))

    def test_positive_sanfang_wuji(self):
        """命盘含'三方无吉曜'→ remedy_012 补充贵人被触发。"""
        chart = _chart([], patterns=["三方无吉曜"])
        assert "remedy_012" in _ids(calc_remedies(chart))

    def test_negative_no_patterns(self):
        """无格局时所有 pattern 类规则不触发。"""
        chart = _chart([])
        pattern_rule_ids = {
            "remedy_008", "remedy_009", "remedy_010",
            "remedy_012", "remedy_013", "remedy_014",
        }
        assert _ids(calc_remedies(chart)).isdisjoint(pattern_rule_ids)

    def test_negative_wrong_pattern_name(self):
        """格局名与规则不匹配 → 对应规则不触发。"""
        chart = _chart([], patterns=["天府坐命"])
        assert "remedy_008" not in _ids(calc_remedies(chart))
        assert "remedy_009" not in _ids(calc_remedies(chart))

    def test_multiple_patterns_trigger_multiple_rules(self):
        """多个格局同时命中，多条 pattern 规则均触发。"""
        chart = _chart([], patterns=["羊陀夹命", "火铃夹命", "空劫夹命"])
        result_ids = _ids(calc_remedies(chart))
        for expected in ("remedy_008", "remedy_009", "remedy_010"):
            assert expected in result_ids


# ══════════════════════════════════════════════════════════════
# 3. pattern_and_liunian 触发器
# ══════════════════════════════════════════════════════════════

class TestPatternAndLiunian:
    """pattern_and_liunian 触发器：格局精确匹配 且 liunian_year 非零。"""

    def test_positive_with_liunian(self):
        """格局匹配且有流年 → remedy_011 流年叠加应对被触发。"""
        chart = _chart([], patterns=["化忌守命"], liunian_year=2026)
        assert "remedy_011" in _ids(calc_remedies(chart))

    def test_negative_no_liunian(self):
        """格局匹配但流年为 0 → remedy_011 不触发。"""
        chart = _chart([], patterns=["化忌守命"], liunian_year=0)
        assert "remedy_011" not in _ids(calc_remedies(chart))

    def test_negative_wrong_pattern(self):
        """有流年但格局名不匹配 → remedy_011 不触发。"""
        chart = _chart([], patterns=["羊陀夹命"], liunian_year=2026)
        assert "remedy_011" not in _ids(calc_remedies(chart))

    def test_liunian_year_appears_in_evidence(self):
        """evidence 中应包含流年年份信息。"""
        chart = _chart([], patterns=["化忌守命"], liunian_year=2026)
        results = calc_remedies(chart)
        r = next((x for x in results if x.id == "remedy_011"), None)
        assert r is not None
        assert "2026" in r.evidence, f"evidence 应含流年年份，实际：{r.evidence!r}"


# ══════════════════════════════════════════════════════════════
# 4. 综合与边界测试
# ══════════════════════════════════════════════════════════════

class TestCombinedAndEdge:
    """综合场景与边界情况测试。"""

    def test_multiple_palace_hua_triggers(self):
        """多个宫位同时化忌，各自规则均触发。"""
        chart = _chart([
            _palace("命宫",   [("天同",  ["化忌"])]),
            _palace("财帛宫", [("太阴",  ["化忌"])]),
            _palace("官禄宫", [("紫微",  ["化忌"])]),
        ])
        result_ids = _ids(calc_remedies(chart))
        for expected in ("remedy_001", "remedy_002", "remedy_003"):
            assert expected in result_ids

    def test_palace_and_pattern_combined(self):
        """palace_hua 与 pattern 同时触发。"""
        chart = _chart(
            palaces=[_palace("命宫", [("天同", ["化忌"])])],
            patterns=["羊陀夹命"],
        )
        result_ids = _ids(calc_remedies(chart))
        assert "remedy_001" in result_ids
        assert "remedy_008" in result_ids

    def test_sorted_by_priority(self):
        """结果按 priority 升序排列。"""
        chart = _chart(
            palaces=[_palace("命宫", [("天同", ["化忌"])])],
            patterns=["羊陀夹命", "空劫夹命"],
            liunian_year=2026,
        )
        results = calc_remedies(chart)
        assert results == sorted(results, key=lambda r: (r.priority, r.name))

    def test_result_fields_complete(self):
        """每条 RemedyResult 包含所有必需字段。"""
        chart = _chart([_palace("命宫", [("天同", ["化忌"])])])
        results = calc_remedies(chart)
        assert results, "应有至少一条结果"
        r = results[0]
        assert r.id
        assert r.name
        assert r.priority in (1, 2, 3)
        assert r.cost_level in ("低", "中", "高")
        assert r.valid_scope in ("流年", "大运", "长期")
        assert isinstance(r.actions, list)
        assert len(r.actions) > 0
        assert r.disclaimer

    def test_no_duplicate_ids(self):
        """同一命盘每条规则最多触发一次，ID 不重复。"""
        chart = _chart(
            palaces=[_palace("命宫", [("天同", ["化忌"])])],
            patterns=["羊陀夹命"],
        )
        ids = [r.id for r in calc_remedies(chart)]
        assert len(ids) == len(set(ids)), "存在重复规则 ID"

    def test_empty_chart_no_error(self):
        """完全空命盘不报错，返回空列表。"""
        chart = _chart([])
        results = calc_remedies(chart)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_no_huaji_star_but_has_other_transforms(self):
        """宫位主星仅化禄/化权/化科，无化忌 → palace_hua 规则均不触发。"""
        chart = _chart([
            _palace("命宫",   [("天同",  ["化禄"])]),
            _palace("财帛宫", [("太阴",  ["化权"])]),
            _palace("官禄宫", [("紫微",  ["化科"])]),
        ])
        palace_hua_ids = {
            "remedy_001", "remedy_002", "remedy_003",
            "remedy_004", "remedy_005", "remedy_006", "remedy_007",
        }
        assert _ids(calc_remedies(chart)).isdisjoint(palace_hua_ids)

    def test_actions_list_non_empty(self):
        """所有触发规则均有至少一条行动步骤。"""
        chart = _chart(
            palaces=[_palace("命宫", [("天同", ["化忌"])])],
            patterns=["羊陀夹命", "火铃夹命"],
            liunian_year=2026,
        )
        for r in calc_remedies(chart):
            assert r.actions, f"{r.id} 缺少 actions"
