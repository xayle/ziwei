"""
tests/test_ziwei_api.py — 紫微斗数 HTTP API 集成测试

覆盖：
  - POST /api/v1/ziwei/full  正常/异常/边界
  - GET  /api/v1/ziwei/demo  演示盘
  - GET  /api/v1/cities      城市列表
  - GET  /api/v1/glossary    词汇表
  - liunian_year 默认值时区验证（Asia/Shanghai）
  - template_version 三档模板切换（simple/standard/pro）
"""
import datetime
import os
import pytest
from zoneinfo import ZoneInfo

from app.schemas.ziwei import ZiweiRequest

# 使用 conftest 中的 client fixture（已含 DB 依赖注入覆盖，但 ziwei 端点不使用 DB）
# GOLDEN = 黄金测试案例 2002-03-13 14:55 女
GOLDEN = dict(year=2002, month=3, day=13, hour=14, minute=55, gender="女")

# ── 模块级 AUTH_BYPASS patch（禁用速率限制，防止跨文件/类 429）─────────────────
@pytest.fixture(scope="module", autouse=True)
def _disable_rate_limit():
    """将 AUTH_BYPASS=true 植入环境，使 _rate_limit_key 每次返回唯一 UUID。"""
    _prev = os.environ.get("AUTH_BYPASS")
    os.environ["AUTH_BYPASS"] = "true"
    yield
    if _prev is None:
        os.environ.pop("AUTH_BYPASS", None)
    else:
        os.environ["AUTH_BYPASS"] = _prev


# ─────────────────────────────────────────────────────────────
# POST /api/v1/ziwei/full
# ─────────────────────────────────────────────────────────────
class TestZiweiFullEndpoint:

    def test_golden_case_200(self, client):
        """黄金测试案例返回 200，关键字段值正确。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        data = r.json()
        assert data["wuxing_ju_name"] == "水二局"
        assert data["life_palace_gz"] == "丁未"
        assert len(data["palaces"]) == 12

    def test_default_youbi_month_trust_advisory(self, client):
        """R038: default month youbi → advisory trust + explicit missing_fields."""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        data = r.json()
        assert data.get("trust_level") == "advisory"
        assert "youbi_month_vs_iztro_hour" in (data.get("missing_fields") or [])
        assert any("右弼" in w for w in (data.get("engine_warnings") or []))

    def test_youbi_hour_request_accepted(self, client):
        """R044: API accepts youbi_method=hour."""
        r = client.post("/api/v1/ziwei/full", json={**GOLDEN, "youbi_method": "hour"})
        assert r.status_code == 200
        assert "youbi_month_vs_iztro_hour" not in (r.json().get("missing_fields") or [])

    def test_palace_analysis_trimmed_to_80(self, client):
        """R045: standard /full trims long palace narrative fields."""
        r = client.post("/api/v1/ziwei/full", json={**GOLDEN, "template_version": "standard"})
        assert r.status_code == 200
        for palace in r.json()["palaces"]:
            for field in ("analysis", "conclusion", "explanation", "suggestion", "tooltip"):
                text = palace.get(field) or ""
                assert len(text) <= 81, f"{palace['name']}.{field} too long: {len(text)}"

    def test_illegal_feb31_422(self, client):
        """2月31日应被 field_validator 拒绝，返回 422。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "month": 2, "day": 31})
        assert r.status_code == 422
        detail = r.json()["detail"]
        # Pydantic 错误信息应包含日期相关提示
        assert any("日期" in str(d) or "day" in str(d).lower() for d in detail)

    def test_illegal_apr31_422(self, client):
        """4月31日不存在，应返回 422。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "month": 4, "day": 31})
        assert r.status_code == 422

    def test_illegal_jun31_422(self, client):
        """6月31日不存在，应返回 422。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "month": 6, "day": 31})
        assert r.status_code == 422

    def test_valid_leap_feb29_200(self, client):
        """2004年（闰年）2月29日应通过验证。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "year": 2004, "month": 2, "day": 29})
        assert r.status_code == 200

    def test_invalid_leap_feb29_non_leap_422(self, client):
        """2003年（非闰年）2月29日应返回 422。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "year": 2003, "month": 2, "day": 29})
        assert r.status_code == 422

    def test_invalid_gender_422(self, client):
        """gender 非['男','女'] 应返回 422。"""
        for bad in ("male", "female", "M", "F", "1", ""):
            r = client.post("/api/v1/ziwei/full",
                            json={**GOLDEN, "gender": bad})
            assert r.status_code == 422, \
                f"gender={bad!r} 应被拒绝，实得 {r.status_code}"

    def test_missing_required_fields_422(self, client):
        """缺少必填字段应返回 422。"""
        r = client.post("/api/v1/ziwei/full", json={"year": 2002})
        assert r.status_code == 422

    def test_year_below_min_422(self, client):
        """年份低于 1900 应返回 422。"""
        r = client.post("/api/v1/ziwei/full", json={**GOLDEN, "year": 1800})
        assert r.status_code == 422

    def test_year_above_max_422(self, client):
        """年份高于 2100 应返回 422。"""
        r = client.post("/api/v1/ziwei/full", json={**GOLDEN, "year": 2200})
        assert r.status_code == 422

    def test_with_longitude_true_solar_time(self, client):
        """传入经度时 true_solar_time 应非空，且为 HH:MM 格式。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "longitude": 116.4})
        assert r.status_code == 200
        tst = r.json()["true_solar_time"]
        assert tst not in ("", None), "传入经度后 true_solar_time 不应为空"
        assert ":" in tst, f"true_solar_time 格式应为 HH:MM，实得 {tst!r}"

    def test_without_longitude_empty_true_solar(self, client):
        """不传经度时 true_solar_time 应为空字符串。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        assert r.json()["true_solar_time"] == ""

    def test_custom_liunian_year(self, client):
        """传入 liunian_year=2030 时，liunian.year 应为 2030。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "liunian_year": 2030})
        assert r.status_code == 200
        assert r.json()["liunian"]["year"] == 2030

    def test_forecast_structure(self, client):
        """forecast 字段应有完整结构。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        fc = r.json().get("forecast")
        assert fc is not None, "forecast 不应为 None"
        assert fc["year"] > 2000
        assert 1 <= fc["yearly"]["score"] <= 100
        assert len(fc["monthly"]) == 12

    def test_forecast_current_month_optional_in_json(self, client):
        """current_month 字段在 JSON 中必须存在（值可为 null 或 dict）。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        fc = r.json().get("forecast")
        assert fc is not None
        assert "current_month" in fc   # 字段存在，值可为 null

    def test_forecast_tier_layer_and_evidence_chain(self, client):
        """BE-P1-03：forecast 含 tier/layer；响应含 evidence_chain。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        data = r.json()
        fc = data.get("forecast")
        assert fc is not None
        assert fc.get("layer") == "heuristic"
        yearly = fc["yearly"]
        assert yearly.get("tier") in ("favorable", "neutral", "caution")
        assert yearly.get("layer") == "heuristic"
        for mo in fc.get("monthly") or []:
            assert mo.get("tier") in ("favorable", "neutral", "caution")
        chain = data.get("evidence_chain") or []
        assert len(chain) >= 3
        assert any(item.get("source") == "life_palace" for item in chain)

    def test_all_12_palaces_present(self, client):
        """应有恰好 12 个宫位。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        palaces = r.json()["palaces"]
        assert len(palaces) == 12
        names = {p["name"] for p in palaces}
        expected = {"命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
                    "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"}
        assert names == expected, f"宫位名不匹配: 缺少 {expected-names}"
        empty = [p for p in palaces if p.get("is_empty_palace")]
        assert empty, "应至少存在一个空宫用于借星结构测试"
        assert empty[0]["borrowed_main_stars"], "空宫应带 borrowed_main_stars"
        assert empty[0]["borrowed_from_palace"], "空宫应标注 borrowed_from_palace"

    def test_flying_chart_present(self, client):
        """飞星盘应包含 12 个宫位。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        fly = r.json().get("flying")
        assert fly is not None
        assert len(fly["palaces"]) == 12

    def test_dayun_present(self, client):
        """大运列表不应为空。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        dayun = r.json()["dayun"]
        assert len(dayun["items"]) > 0


# ─────────────────────────────────────────────────────────────
# GET /api/v1/ziwei/demo
# ─────────────────────────────────────────────────────────────
class TestZiweiDemoEndpoint:

    def test_demo_200_golden_fields(self, client):
        r = client.get("/api/v1/ziwei/demo")
        assert r.status_code == 200
        data = r.json()
        assert data["wuxing_ju_name"] == "水二局"
        assert data["life_palace_gz"] == "丁未"
        assert data["gender"] == "女"

    def test_demo_has_forecast(self, client):
        r = client.get("/api/v1/ziwei/demo")
        assert r.status_code == 200
        assert r.json().get("forecast") is not None

    def test_demo_has_liuyue(self, client):
        r = client.get("/api/v1/ziwei/demo")
        assert r.status_code == 200
        assert len(r.json().get("liuyue", [])) == 12
        summary = r.json().get("ziwei_structural_summary", {})
        assert summary.get("source") == "routers.ziwei.build_response"
        assert summary.get("chart_relation_summary", {}).get("source") == "routers.ziwei.build_response"


# ─────────────────────────────────────────────────────────────
# 辅助接口
# ─────────────────────────────────────────────────────────────
class TestAuxEndpoints:

    def test_cities_200(self, client):
        r = client.get("/api/v1/cities")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 10

    def test_cities_have_required_fields(self, client):
        r = client.get("/api/v1/cities")
        assert r.status_code == 200
        for city in r.json():
            assert "name" in city
            assert "lng" in city
            assert "lat" in city

    def test_beijing_in_cities(self, client):
        r = client.get("/api/v1/cities")
        assert r.status_code == 200
        names = [c["name"] for c in r.json()]
        assert "北京" in names

    def test_cities_lng_range(self, client):
        """中国境内经度范围 [73, 136]。"""
        r = client.get("/api/v1/cities")
        assert r.status_code == 200
        for city in r.json():
            lng = city["lng"]
            assert 73.0 <= lng <= 136.0, \
                f"{city['name']} 经度 {lng} 超出中国境内范围"

    def test_glossary_200(self, client):
        r = client.get("/api/v1/glossary")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_glossary_items_have_term(self, client):
        r = client.get("/api/v1/glossary")
        assert r.status_code == 200
        for item in r.json()[:5]:   # 只检查前5条
            assert "term" in item, f"词汇表条目缺少 term 字段: {item}"


# ─────────────────────────────────────────────────────────────
# liunian_year 时区测试
# ─────────────────────────────────────────────────────────────
class TestLiunianTimezone:
    """
    Fix ②验证：liunian_year 默认值应使用 Asia/Shanghai 时区。
    不传 liunian_year 时，API 返回 liunian.year 应等于上海当年年份。
    """

    def test_default_liunian_uses_shanghai_year(self, client):
        expected = datetime.datetime.now(ZoneInfo("Asia/Shanghai")).year
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        actual = r.json()["liunian"]["year"]
        assert actual == expected, \
            f"liunian.year 应为上海当年 {expected}，实得 {actual}"

    def test_explicit_liunian_overrides_default(self, client):
        """显式传 liunian_year 不应使用服务器时区默认值。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "liunian_year": 2035})
        assert r.status_code == 200
        assert r.json()["liunian"]["year"] == 2035


# ─────────────────────────────────────────────────────────────
# POST /api/v1/ziwei/compatibility
# ─────────────────────────────────────────────────────────────

GOLDEN_B = dict(year=1998, month=7, day=15, hour=9, minute=0, gender="男")

class TestCompatibilityEndpoint:

    def test_basic_200(self, client):
        """合盘接口返回 200，关键字段存在。"""
        r = client.post("/api/v1/ziwei/compatibility",
                        json={"person_a": GOLDEN, "person_b": GOLDEN_B})
        assert r.status_code == 200
        data = r.json()
        assert "total_score" in data
        assert "max_score" in data
        assert "level" in data
        assert "dimensions" in data
        assert len(data["dimensions"]) == 5

    def test_score_range(self, client):
        """总分在 [0, max_score] 之内。"""
        r = client.post("/api/v1/ziwei/compatibility",
                        json={"person_a": GOLDEN, "person_b": GOLDEN_B})
        data = r.json()
        assert 0 <= data["total_score"] <= data["max_score"]

    def test_harmony_conflict_complement_fields(self, client):
        """新增字段 harmony_points / conflict_points / complement_points 为列表。"""
        r = client.post("/api/v1/ziwei/compatibility",
                        json={"person_a": GOLDEN, "person_b": GOLDEN_B})
        data = r.json()
        assert isinstance(data.get("harmony_points", []), list)
        assert isinstance(data.get("conflict_points", []), list)
        assert isinstance(data.get("complement_points", []), list)

    def test_palace_compare_field(self, client):
        """palace_compare 字段为列表，每项包含双方干支和星曜。"""
        r = client.post("/api/v1/ziwei/compatibility",
                        json={"person_a": GOLDEN, "person_b": GOLDEN_B})
        data = r.json()
        pc = data.get("palace_compare", [])
        assert isinstance(pc, list)
        assert len(pc) == 6   # 六大宫位
        row = pc[0]
        assert "palace" in row
        assert "a_gz" in row and "b_gz" in row
        assert "a_stars" in row and "b_stars" in row
        assert "relation" in row

    def test_dimension_scores_in_range(self, client):
        """每个维度分值不超过 max_score，且非负。"""
        r = client.post("/api/v1/ziwei/compatibility",
                        json={"person_a": GOLDEN, "person_b": GOLDEN_B})
        for dim in r.json()["dimensions"]:
            assert 0 <= dim["score"] <= dim["max_score"]

    def test_level_is_valid_string(self, client):
        """level 字段为有效评级字符串。"""
        r = client.post("/api/v1/ziwei/compatibility",
                        json={"person_a": GOLDEN, "person_b": GOLDEN_B})
        valid = {"上上签", "上签", "中签", "下签", "平"}
        assert r.json()["level"] in valid

    def test_same_person_sanity(self, client):
        """同一人合盘应得高分（命宫/年支必然同支，加分多）。"""
        r = client.post("/api/v1/ziwei/compatibility",
                        json={"person_a": GOLDEN, "person_b": GOLDEN})
        assert r.status_code == 200
        data = r.json()
        assert data["total_score"] >= 40   # 同支 + 同五行仍得分

    def test_invalid_gender_422(self, client):
        """非法 gender 字段应返回 422。"""
        bad = {**GOLDEN, "gender": "unknown"}
        r = client.post("/api/v1/ziwei/compatibility",
                        json={"person_a": bad, "person_b": GOLDEN_B})
        assert r.status_code == 422

    def test_person_info_fields(self, client):
        """person_a_info / person_b_info 包含 birth_solar / life_gz / wuxing_ju。"""
        r = client.post("/api/v1/ziwei/compatibility",
                        json={"person_a": GOLDEN, "person_b": GOLDEN_B})
        data = r.json()
        for key in ("person_a_info", "person_b_info"):
            info = data[key]
            assert "birth_solar" in info
            assert "life_gz" in info
            assert "wuxing_ju" in info


# ─────────────────────────────────────────────────────────────
# 新增字段：governance + patterns + remedies + life_suggestions
# ─────────────────────────────────────────────────────────────

class TestNewResponseFields:
    """验证 ZiweiResponse 新增字段的结构与类型。"""

    def test_governance_fields_present(self, client):
        """algorithm_version 和 template_version 字段应存在于响应中。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        data = r.json()
        assert "algorithm_version" in data
        assert "template_version" in data
        assert data["algorithm_version"] == "2.1.0"
        assert data["template_version"] == "standard"

    def test_engine_version_present(self, client):
        """engine_version 字段应存在且格式正确。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        data = r.json()
        assert "engine_version" in data
        assert "." in data["engine_version"]  # 格式如 "2.1.0"

    def test_patterns_is_list(self, client):
        """patterns 字段应为列表。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        patterns = r.json()["patterns"]
        assert isinstance(patterns, list)

    def test_patterns_item_structure(self, client):
        """patterns 列表中每项格局含必需字段。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        data = r.json()
        for pt in data["patterns"]:
            assert "name" in pt
            assert "level" in pt
            assert "description" in pt
            assert isinstance(pt.get("palaces", []), list)
            assert isinstance(pt.get("stars", []), list)

    def test_remedies_is_list(self, client):
        """remedies 字段应为列表。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert isinstance(r.json()["remedies"], list)

    def test_remedies_item_structure(self, client):
        """若 remedies 非空，每项应含必需字段。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        for rem in r.json()["remedies"]:
            assert "id" in rem
            assert "name" in rem
            assert "priority" in rem
            assert "cost_level" in rem
            assert "valid_scope" in rem
            assert isinstance(rem.get("actions", []), list)
            assert isinstance(rem.get("evidence", ""), str)
            assert isinstance(rem.get("disclaimer", ""), str)

    def test_life_suggestions_is_list(self, client):
        """life_suggestions 字段应为列表。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert isinstance(r.json()["life_suggestions"], list)

    def test_life_suggestions_item_structure(self, client):
        """若 life_suggestions 非空，每项应含必需字段。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        for s in r.json()["life_suggestions"]:
            assert "id" in s
            assert "category" in s
            assert "category_label" in s
            assert "name" in s
            assert "priority" in s
            assert "cost_level" in s
            assert "valid_scope" in s
            assert isinstance(s.get("actions", []), list)

    def test_demo_has_governance_fields(self, client):
        """演示盘也应包含治理字段。"""
        r = client.get("/api/v1/ziwei/demo")
        assert r.status_code == 200
        data = r.json()
        assert data.get("algorithm_version") == "2.1.0"
        assert data.get("template_version") == "standard"

    def test_demo_has_patterns_list(self, client):
        """演示盘 patterns 字段应为列表。"""
        r = client.get("/api/v1/ziwei/demo")
        assert r.status_code == 200
        assert isinstance(r.json().get("patterns", None), list)

    def test_demo_has_remedies_list(self, client):
        """演示盘 remedies 字段应为列表。"""
        r = client.get("/api/v1/ziwei/demo")
        assert isinstance(r.json().get("remedies", None), list)

    def test_demo_has_life_suggestions_list(self, client):
        """演示盘 life_suggestions 字段应为列表。"""
        r = client.get("/api/v1/ziwei/demo")
        assert isinstance(r.json().get("life_suggestions", None), list)


# ─────────────────────────────────────────────────────────────
# 报告模板切换：simple / standard / pro
# ─────────────────────────────────────────────────────────────

class TestTemplateVersion:
    """验证三档模板切换的字段取舍行为。"""

    def test_standard_template_is_default(self, client):
        """不传 template_version 时默认返回 standard。"""
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        assert r.json()["template_version"] == "standard"

    def test_standard_has_forecast(self, client):
        """standard 模板应包含 forecast。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "standard"})
        assert r.status_code == 200
        assert r.json()["forecast"] is not None

    def test_standard_has_flying(self, client):
        """standard 模板应包含 flying 飞星盘。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "standard"})
        data = r.json()
        assert data["flying"] is not None

    def test_standard_has_life_suggestions(self, client):
        """standard 模板应包含 life_suggestions 列表（非空或非 None）。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "standard"})
        assert isinstance(r.json()["life_suggestions"], list)

    # ── simple 模板 ──────────────────────────────────────────

    def test_simple_template_returns_200(self, client):
        """simple 模板请求应返回 200。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "simple"})
        assert r.status_code == 200
        assert r.json()["template_version"] == "simple"

    def test_simple_no_forecast(self, client):
        """simple 模板不应包含 forecast（应为 null）。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "simple"})
        assert r.json()["forecast"] is None

    def test_simple_no_flying(self, client):
        """simple 模板不应包含 flying（应为 null）。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "simple"})
        assert r.json()["flying"] is None

    def test_simple_empty_liuyue(self, client):
        """simple 模板流月列表应为空。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "simple"})
        assert r.json()["liuyue"] == []

    def test_simple_empty_analysis(self, client):
        """simple 模板 analysis 字典应为空。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "simple"})
        assert r.json()["analysis"] == {}

    def test_simple_empty_remedies(self, client):
        """simple 模板 remedies 应为空列表。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "simple"})
        assert r.json()["remedies"] == []

    def test_simple_empty_life_suggestions(self, client):
        """simple 模板 life_suggestions 应为空列表。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "simple"})
        assert r.json()["life_suggestions"] == []

    def test_simple_still_has_palaces(self, client):
        """simple 模板仍应包含 12 宫位数据。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "simple"})
        assert len(r.json()["palaces"]) == 12

    def test_simple_still_has_patterns(self, client):
        """simple 模板仍应包含 patterns 格局检测结果。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "simple"})
        assert isinstance(r.json()["patterns"], list)

    def test_simple_has_summary(self, client):
        """simple 模板仍应包含摘要文字。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "simple"})
        assert isinstance(r.json()["summary"], str)

    # ── pro 模板 ─────────────────────────────────────────────

    def test_pro_template_returns_200(self, client):
        """pro 模板请求应返回 200。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "pro"})
        assert r.status_code == 200
        assert r.json()["template_version"] == "pro"

    def test_pro_has_forecast(self, client):
        """pro 模板应包含完整 forecast。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "pro"})
        assert r.json()["forecast"] is not None

    def test_pro_has_life_suggestions(self, client):
        """pro 模板应包含 life_suggestions 列表。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "pro"})
        assert isinstance(r.json()["life_suggestions"], list)

    def test_invalid_template_rejected(self, client):
        """无效 template_version 应返回 422。"""
        r = client.post("/api/v1/ziwei/full",
                        json={**GOLDEN, "template_version": "invalid_tpl"})
        assert r.status_code == 422


class TestZiweiExtendedParams:
    """ZiweiRequest 扩展参数 wenchang_method / flow_* 等。"""

    def test_liunian_sihua_default_year_stem(self):
        req = ZiweiRequest(year=2002, month=3, day=13, hour=14, gender="女")
        assert req.liunian_sihua_method == "year_stem"

    def test_flow_params_accepted(self, client):
        payload = {
            **GOLDEN,
            "flow_liuyue_month": 3,
            "flow_lunar_day": 15,
            "flow_hour_branch": 6,
        }
        r = client.post("/api/v1/ziwei/full", json=payload)
        assert r.status_code == 200
        liuri = r.json().get("liuri_liushi")
        assert liuri is not None

    def test_wenchang_method_legacy_accepted(self, client):
        r = client.post(
            "/api/v1/ziwei/full",
            json={**GOLDEN, "wenchang_method": "year_branch", "youbi_method": "hour"},
        )
        assert r.status_code == 200

    def test_flow_lunar_day_without_month_rejected(self, client):
        r = client.post(
            "/api/v1/ziwei/full",
            json={**GOLDEN, "flow_lunar_day": 10},
        )
        assert r.status_code == 422

    def test_invalid_wenchang_method_rejected(self, client):
        r = client.post(
            "/api/v1/ziwei/full",
            json={**GOLDEN, "wenchang_method": "invalid"},
        )
        assert r.status_code == 422

    def test_flying_accepts_method_params(self, client):
        r = client.post(
            "/api/v1/ziwei/flying",
            json={**GOLDEN, "liunian_sihua_method": "life_palace_stem", "wenchang_method": "year_branch"},
        )
        assert r.status_code == 200
        assert "palaces" in r.json()
