"""
tests/test_name_engine.py — 姓名学引擎 + API 端点测试
"""
from __future__ import annotations

import os
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def _disable_rate_limit_name():
    prev = os.environ.get("AUTH_BYPASS")
    os.environ["AUTH_BYPASS"] = "true"
    yield
    if prev is None:
        os.environ.pop("AUTH_BYPASS", None)
    else:
        os.environ["AUTH_BYPASS"] = prev


# ─────────────────────────────────────────────────────────────────────────────
# 1. get_stroke_count
# ─────────────────────────────────────────────────────────────────────────────

class TestGetStrokeCount:

    def test_common_chars(self):
        from services.name_engine.engine import get_stroke_count
        assert get_stroke_count("李") == 7
        assert get_stroke_count("王") == 4
        assert get_stroke_count("一") == 1

    def test_fallback_unicode_range(self):
        """CJK 范围内的未收录字应返回 >= 1"""
        from services.name_engine.engine import get_stroke_count
        # 随便选一个不大可能在数据库里的字
        result = get_stroke_count("龥")  # U+9FA5，末尾CJK
        assert result >= 1

    def test_non_cjk_returns_one(self):
        """非 CJK 字符返回 1"""
        from services.name_engine.engine import get_stroke_count
        assert get_stroke_count("A") == 1

    def test_all_returns_positive(self):
        from services.name_engine.engine import get_stroke_count
        for ch in "张伟芳明国志华建":
            assert get_stroke_count(ch) >= 1, f"'{ch}' should have >= 1 stroke"


# ─────────────────────────────────────────────────────────────────────────────
# 2. calc_five_grids
# ─────────────────────────────────────────────────────────────────────────────

class TestCalcFiveGrids:

    def test_single_surname_single_name(self):
        """李明：天格=李+1=8，人格=李+明=7+8=15，地格=明+1=9，外格=8+9-15=2，总格=7+8=15"""
        from services.name_engine.engine import calc_five_grids
        t, r, d, w, z = calc_five_grids("李", "明")
        assert t == 8   # 7+1
        assert r == 15  # 7+8
        assert d == 9   # 8+1
        assert w == 2   # 8+9-15
        assert z == 15  # 7+8

    def test_single_surname_double_name(self):
        """王小明：天格=王+1=5，人格=王+小=4+3=7，地格=小+明=3+8=11，外格=5+11-7=9，总格=4+3+8=15"""
        from services.name_engine.engine import calc_five_grids
        t, r, d, w, z = calc_five_grids("王", "小明")
        assert t == 5    # 4+1
        assert r == 7    # 4+3
        assert d == 11   # 3+8
        assert w == 9    # 5+11-7
        assert z == 15   # 4+3+8

    def test_double_surname(self):
        """复姓欧阳：天格 = 欧笔画+阳笔画（不+1），与单姓规则不同"""
        from services.name_engine.engine import calc_five_grids, get_stroke_count
        t, r, d, w, z = calc_five_grids("欧阳", "明")
        ou = get_stroke_count("欧")
        yang = get_stroke_count("阳")
        ming = get_stroke_count("明")
        # 复姓天格 = 所有姓字笔画之和
        assert t == ou + yang
        # 人格 = 姓末字笔画 + 名首字笔画
        assert r == yang + ming

    def test_none_given_name(self):
        """空名字：地格=1，外格=天格+1-人格"""
        from services.name_engine.engine import calc_five_grids
        t, r, d, w, z = calc_five_grids("李", "")
        assert d == 1

    def test_outer_ge_min_one(self):
        """外格最小为1"""
        from services.name_engine.engine import calc_five_grids
        # 设计极端组合：单姓1画，单名1画 → 天=2,人=2,地=2,外=max(1,2+2-2)=2
        # 用"一"(1画)姓+"一"(1画)名
        t, r, d, w, z = calc_five_grids("一", "一")
        assert w >= 1

    def test_zonge_equals_sum_of_strokes(self):
        from services.name_engine.engine import calc_five_grids, get_stroke_count
        t, r, d, w, z = calc_five_grids("张", "伟")
        assert z == get_stroke_count("张") + get_stroke_count("伟")


# ─────────────────────────────────────────────────────────────────────────────
# 3. analyze_name
# ─────────────────────────────────────────────────────────────────────────────

class TestAnalyzeName:

    def test_basic(self):
        from services.name_engine.engine import analyze_name
        result = analyze_name("李", "明")
        assert result.surname == "李"
        assert result.given_name == "明"
        assert result.tianke.number == 8
        assert result.renke.number == 15
        assert result.dike.number == 9
        assert result.waike.number == 2
        assert result.zonge.number == 15

    def test_grid_fields(self):
        from services.name_engine.engine import analyze_name
        result = analyze_name("王", "小明")
        for grid in (result.tianke, result.renke, result.dike, result.waike, result.zonge):
            assert grid.number > 0
            assert grid.element in ("木", "火", "土", "金", "水")
            assert grid.lucky
            assert 1 <= grid.score <= 10
            assert grid.desc

    def test_sancai_pattern(self):
        from services.name_engine.engine import analyze_name
        result = analyze_name("李", "明")
        assert len(result.sancai.pattern) == 3  # e.g. "金土金"
        assert result.sancai.lucky
        assert 1 <= result.sancai.score <= 10

    def test_overall_score_range(self):
        from services.name_engine.engine import analyze_name
        result = analyze_name("李", "明")
        assert 0 <= result.overall_score <= 100

    def test_summary_non_empty(self):
        from services.name_engine.engine import analyze_name
        result = analyze_name("张", "伟")
        assert result.summary

    def test_empty_surname_raises(self):
        from services.name_engine.engine import analyze_name
        with pytest.raises(ValueError, match="surname"):
            analyze_name("", "明")

    def test_double_surname(self):
        from services.name_engine.engine import analyze_name
        result = analyze_name("欧阳", "明")
        assert result.tianke.number > 0

    def test_single_char_name(self):
        from services.name_engine.engine import analyze_name
        result = analyze_name("王", "芳")
        assert result is not None

    def test_three_char_name(self):
        from services.name_engine.engine import analyze_name
        result = analyze_name("诸葛", "孔明")
        assert result.zonge.number > 0

    def test_consistency_multiple_calls(self):
        """同参数多次调用结果应一致。"""
        from services.name_engine.engine import analyze_name
        r1 = analyze_name("李", "明")
        r2 = analyze_name("李", "明")
        assert r1.overall_score == r2.overall_score
        assert r1.sancai.pattern == r2.sancai.pattern


# ─────────────────────────────────────────────────────────────────────────────
# 4. API 端点 POST /api/v1/name/analyze
# ─────────────────────────────────────────────────────────────────────────────

class TestNameAnalyzeEndpoint:

    def test_basic_request(self, client):
        r = client.post("/api/v1/name/analyze", json={
            "surname": "李",
            "given_name": "明",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["surname"] == "李"
        assert data["given_name"] == "明"

    def test_response_schema(self, client):
        r = client.post("/api/v1/name/analyze", json={
            "surname": "王",
            "given_name": "小明",
        })
        assert r.status_code == 200
        data = r.json()
        for grid_key in ("tianke", "renke", "dike", "waike", "zonge"):
            assert grid_key in data
            grid = data[grid_key]
            assert "number" in grid
            assert "element" in grid
            assert "lucky" in grid
            assert "score" in grid
            assert "desc" in grid
        assert "sancai" in data
        assert "pattern" in data["sancai"]
        assert "overall_score" in data
        assert "summary" in data

    def test_double_surname(self, client):
        r = client.post("/api/v1/name/analyze", json={
            "surname": "欧阳",
            "given_name": "明",
        })
        assert r.status_code == 200

    def test_missing_given_name(self, client):
        r = client.post("/api/v1/name/analyze", json={
            "surname": "李",
        })
        # given_name 有默认值，不应报错
        assert r.status_code in (200, 422)

    def test_empty_surname_422(self, client):
        r = client.post("/api/v1/name/analyze", json={
            "surname": "",
            "given_name": "明",
        })
        assert r.status_code == 422

    def test_too_long_surname_422(self, client):
        r = client.post("/api/v1/name/analyze", json={
            "surname": "李王张赵",  # 超过3个字
            "given_name": "明",
        })
        assert r.status_code == 422

    def test_overall_score_in_range(self, client):
        r = client.post("/api/v1/name/analyze", json={
            "surname": "张",
            "given_name": "伟",
        })
        assert r.status_code == 200
        data = r.json()
        assert 0 <= data["overall_score"] <= 100

    def test_sancai_pattern_three_elements(self, client):
        r = client.post("/api/v1/name/analyze", json={
            "surname": "刘",
            "given_name": "国志",
        })
        assert r.status_code == 200
        pattern = r.json()["sancai"]["pattern"]
        assert len(pattern) == 3
        for ch in pattern:
            assert ch in "木火土金水"

    def test_multiple_names(self, client):
        """测试多个常见姓名，确保无意外崩溃。"""
        names = [
            ("张", "伟"), ("王", "芳"), ("李", "强"), ("赵", "敏"),
            ("陈", "华"), ("刘", "建国"), ("杨", "志远"), ("黄", "小红"),
        ]
        for surname, given_name in names:
            r = client.post("/api/v1/name/analyze", json={
                "surname": surname,
                "given_name": given_name,
            })
            assert r.status_code == 200, f"Failed for {surname}{given_name}"


# ─────────────────────────────────────────────────────────────────────────────
# 5. suggest_names 引擎函数
# ─────────────────────────────────────────────────────────────────────────────

class TestSuggestNames:

    def test_basic_2char(self):
        """2字名建议，返回 list 且每条字段合法。"""
        from services.name_engine.engine import suggest_names
        suggestions, total = suggest_names("张", name_length=2, top_n=5, min_score=60)
        assert isinstance(suggestions, list)
        assert total > 0
        for s in suggestions:
            assert len(s.given_name) == 2
            assert 0 <= s.overall_score <= 100
            assert s.overall_score >= 60
            assert 1 <= s.renke_score <= 10
            assert 1 <= s.sancai_score <= 10
            assert len(s.sancai_pattern) == 3
            assert len(s.element_composition) == 2
            for ele in s.element_composition:
                assert ele in ("木", "火", "土", "金", "水", "?")

    def test_basic_1char(self):
        """1字名建议。"""
        from services.name_engine.engine import suggest_names
        suggestions, total = suggest_names("李", name_length=1, top_n=5, min_score=50)
        assert isinstance(suggestions, list)
        for s in suggestions:
            assert len(s.given_name) == 1
            assert len(s.element_composition) == 1

    def test_preferred_elements_filter(self):
        """指定水+木五行时，建议字的五行应包含水或木。"""
        from services.name_engine.engine import suggest_names
        suggestions, _ = suggest_names(
            "王", name_length=2, preferred_elements=["水", "木"], top_n=10, min_score=50
        )
        assert len(suggestions) > 0
        for s in suggestions:
            # 至少有一个字属于水或木
            assert any(e in ("水", "木") for e in s.element_composition), (
                f"'{s.given_name}' elements {s.element_composition} has no 水/木"
            )

    def test_sorted_by_score(self):
        """建议应按 overall_score 降序排列。"""
        from services.name_engine.engine import suggest_names
        suggestions, _ = suggest_names("李", name_length=2, top_n=10, min_score=0)
        scores = [s.overall_score for s in suggestions]
        assert scores == sorted(scores, reverse=True)

    def test_top_n_respected(self):
        """返回数量不超过 top_n。"""
        from services.name_engine.engine import suggest_names
        suggestions, _ = suggest_names("张", name_length=2, top_n=3, min_score=0)
        assert len(suggestions) <= 3

    def test_min_score_filter(self):
        """所有返回结果的 overall_score 均 >= min_score。"""
        from services.name_engine.engine import suggest_names
        suggestions, _ = suggest_names("陈", name_length=2, top_n=20, min_score=70)
        for s in suggestions:
            assert s.overall_score >= 70

    def test_invalid_name_length_raises(self):
        from services.name_engine.engine import suggest_names
        with pytest.raises(ValueError, match="name_length"):
            suggest_names("李", name_length=3)

    def test_empty_surname_raises(self):
        from services.name_engine.engine import suggest_names
        with pytest.raises(ValueError, match="surname"):
            suggest_names("", name_length=1)

    def test_summary_non_empty(self):
        from services.name_engine.engine import suggest_names
        suggestions, _ = suggest_names("王", name_length=2, top_n=3, min_score=0)
        for s in suggestions:
            assert s.summary


# ─────────────────────────────────────────────────────────────────────────────
# 6. API 端点 POST /api/v1/name/suggest
# ─────────────────────────────────────────────────────────────────────────────

class TestNameSuggestEndpoint:

    def test_basic_request(self, client):
        r = client.post("/api/v1/name/suggest", json={
            "surname": "张",
            "name_length": 2,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["surname"] == "张"
        assert data["name_length"] == 2
        assert "suggestions" in data
        assert "total_candidates_evaluated" in data
        assert data["total_candidates_evaluated"] > 0

    def test_preferred_elements(self, client):
        r = client.post("/api/v1/name/suggest", json={
            "surname": "李",
            "name_length": 2,
            "preferred_elements": ["水", "木"],
            "top_n": 5,
            "min_score": 50,
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data["suggestions"]) <= 5
        for item in data["suggestions"]:
            assert any(e in ("水", "木") for e in item["element_composition"])

    def test_response_schema(self, client):
        r = client.post("/api/v1/name/suggest", json={
            "surname": "王",
            "name_length": 2,
            "top_n": 3,
        })
        assert r.status_code == 200
        data = r.json()
        for item in data["suggestions"]:
            assert "given_name" in item
            assert "overall_score" in item
            assert "renke_score" in item
            assert "sancai_score" in item
            assert "sancai_pattern" in item
            assert "element_composition" in item
            assert "summary" in item
            assert 0 <= item["overall_score"] <= 100

    def test_1char_name(self, client):
        r = client.post("/api/v1/name/suggest", json={
            "surname": "刘",
            "name_length": 1,
            "top_n": 5,
        })
        assert r.status_code == 200
        for item in r.json()["suggestions"]:
            assert len(item["given_name"]) == 1
            assert len(item["element_composition"]) == 1

    def test_invalid_element_422(self, client):
        r = client.post("/api/v1/name/suggest", json={
            "surname": "张",
            "preferred_elements": ["风"],
        })
        assert r.status_code == 422

    def test_invalid_name_length_422(self, client):
        r = client.post("/api/v1/name/suggest", json={
            "surname": "张",
            "name_length": 3,
        })
        assert r.status_code == 422

    def test_empty_surname_422(self, client):
        r = client.post("/api/v1/name/suggest", json={
            "surname": "",
            "name_length": 2,
        })
        assert r.status_code == 422

    def test_scores_sorted_desc(self, client):
        r = client.post("/api/v1/name/suggest", json={
            "surname": "陈",
            "name_length": 2,
            "top_n": 10,
            "min_score": 0,
        })
        assert r.status_code == 200
        scores = [item["overall_score"] for item in r.json()["suggestions"]]
        assert scores == sorted(scores, reverse=True)

    def test_algorithm_version_present(self, client):
        r = client.post("/api/v1/name/suggest", json={"surname": "张"})
        assert r.status_code == 200
        assert r.json()["algorithm_version"] == "1.0.0"
