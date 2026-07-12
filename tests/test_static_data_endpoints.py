"""
tests/test_static_data_endpoints.py — §4.13 静态数据端点测试

覆盖:
  GET /api/v1/glossary  — ≥50条命理术语, R13/3.05
  GET /api/v1/cities    — 337 城（地级市全覆盖）, GAP-06
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def anon_client():
    """无需认证的测试客户端（static_data 端点不需要 auth）"""
    import os
    _prev = os.environ.get("AUTH_BYPASS")
    os.environ["AUTH_BYPASS"] = "true"
    try:
        from run import app
        yield TestClient(app)
    finally:
        if _prev is None:
            os.environ.pop("AUTH_BYPASS", None)
        else:
            os.environ["AUTH_BYPASS"] = _prev


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/glossary
# ─────────────────────────────────────────────────────────────────────────────

class TestGlossaryEndpoint:
    """§4.13 命理术语词汇表端点 (R13 / 3.05)"""

    def test_returns_200(self, anon_client: TestClient):
        resp = anon_client.get("/api/v1/glossary")
        assert resp.status_code == 200, resp.text

    def test_returns_list(self, anon_client: TestClient):
        data = anon_client.get("/api/v1/glossary").json()
        assert isinstance(data, list)

    def test_at_least_50_terms(self, anon_client: TestClient):
        """3.05 验收: TERM_GLOSSARY ≥ 50 条"""
        data = anon_client.get("/api/v1/glossary").json()
        assert len(data) >= 50, f"词汇表应 ≥50 条，实际 {len(data)}"

    def test_each_item_has_required_fields(self, anon_client: TestClient):
        """每条术语含 term / pinyin / definition / category"""
        data = anon_client.get("/api/v1/glossary").json()
        for item in data[:10]:  # 抽查前10条
            assert "term" in item and item["term"], f"缺少 term: {item}"
            assert "definition" in item and item["definition"], f"缺少 definition: {item}"
            assert "category" in item and item["category"], f"缺少 category: {item}"
            assert "pinyin" in item, f"缺少 pinyin: {item}"

    def test_valid_categories(self, anon_client: TestClient):
        """category 值只在允许范围内"""
        VALID = {"格局", "神煞", "五行", "十神", "大运", "紫微", "其他"}
        data = anon_client.get("/api/v1/glossary").json()
        for item in data:
            assert item["category"] in VALID, f"非法 category: {item['category']}"

    def test_category_filter(self, anon_client: TestClient):
        """?category=格局 只返回格局相关术语"""
        data = anon_client.get("/api/v1/glossary", params={"category": "格局"}).json()
        for item in data:
            assert item["category"] == "格局"

    def test_has_geju_terms(self, anon_client: TestClient):
        """词汇表应包含格局相关术语"""
        data = anon_client.get("/api/v1/glossary").json()
        terms = {item["term"] for item in data}
        geju_terms = {"七杀格", "正官格", "食神格", "正印格", "偏财格"}
        found = geju_terms & terms
        assert len(found) >= 1, f"应含格局术语，实际: {found}"


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/cities
# ─────────────────────────────────────────────────────────────────────────────

class TestCitiesEndpoint:
    """§4.13 城市经纬度端点 (GAP-06 / 红线34)"""

    def test_returns_200(self, anon_client: TestClient):
        resp = anon_client.get("/api/v1/cities")
        assert resp.status_code == 200, resp.text

    def test_exactly_36_cities(self, anon_client: TestClient):
        """红线34: 城市选择器 ≥ 300 城（含省会 + 地级市）"""
        data = anon_client.get("/api/v1/cities").json()
        assert len(data) >= 300, f"应 ≥300 城，实际 {len(data)}"

    def test_each_city_has_lng_lat(self, anon_client: TestClient):
        data = anon_client.get("/api/v1/cities").json()
        for city in data:
            assert "name" in city and city["name"]
            assert "lng" in city and 73 <= city["lng"] <= 136, f"经度超出范围: {city}"
            assert "lat" in city and 18 <= city["lat"] <= 54, f"纬度超出范围: {city}"

    def test_beijing_present(self, anon_client: TestClient):
        """北京必须在列表中"""
        data = anon_client.get("/api/v1/cities").json()
        names = {c["name"] for c in data}
        assert "北京" in names, "城市列表应包含北京"

    def test_valid_city_type(self, anon_client: TestClient):
        """city_type 值只在允许范围内"""
        VALID = {"直辖市", "省会", "计划单列市", "地级市"}
        data = anon_client.get("/api/v1/cities").json()
        for city in data:
            assert city.get("city_type") in VALID, f"非法 city_type: {city}"
