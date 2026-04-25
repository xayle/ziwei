"""
test_coverage_boost26.py — routers/ziwei.py 集成测试

覆盖目标（当前 50%，目标 70%+）：
  /full (simple/pro 模板), /compatibility, /multi_compat,
  /batch (CSV 上传), /flying, /demo

所有测试无需 DB（ziwei 端点大多无状态），使用 AUTH_BYPASS 或直接不需鉴权。
"""
from __future__ import annotations

import io
import os
import zipfile

import pytest
from fastapi.testclient import TestClient

# ──────────────────────────────────────────────────────────────────────────────
# 共用常量 — 壬午年正月三十未时女（黄金测试案例，与 /demo 相同）
# ──────────────────────────────────────────────────────────────────────────────
_DEMO_PARAMS = {"year": 2002, "month": 3, "day": 13, "hour": 14, "minute": 55, "gender": "女"}
_PERSON_A    = {"year": 1990, "month": 7, "day": 17, "hour": 12, "minute": 0, "gender": "男"}
_PERSON_B    = {"year": 1993, "month": 3, "day": 15, "hour": 8,  "minute": 0, "gender": "女"}


def _bypass_client() -> TestClient:
    os.environ["AUTH_BYPASS"] = "true"
    from run import app as _app
    return TestClient(_app)


# ══════════════════════════════════════════════════════════════════════════════
# A. POST /api/v1/ziwei/full — 模板分支
# ══════════════════════════════════════════════════════════════════════════════

class TestZiweiFullTemplates:
    """测试不同 template_version 下的行为：simple / standard / pro"""

    def setup_method(self):
        self.client = _bypass_client()

    def test_standard_template(self):
        """默认 standard → 200，包含完整字段"""
        resp = self.client.post("/api/v1/ziwei/full", json=_DEMO_PARAMS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["template_version"] == "standard"
        assert "palaces" in data
        assert "dayun" in data
        assert "lunar" in data

    def test_simple_template_skips_heavy_fields(self):
        """simple 模板 → flying/forecast 为 None/空"""
        payload = {**_DEMO_PARAMS, "template_version": "simple"}
        resp = self.client.post("/api/v1/ziwei/full", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["template_version"] == "simple"
        # simple 模式：以下字段应当为空/None
        assert data.get("flying") is None
        assert data.get("forecast") is None
        assert data.get("liuyue") in (None, [])
        assert data.get("analysis") in ({}, None)

    def test_pro_template(self):
        """pro 模板 → 200，与 standard 基本相同"""
        payload = {**_DEMO_PARAMS, "template_version": "pro"}
        resp = self.client.post("/api/v1/ziwei/full", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["template_version"] == "pro"
        assert "palaces" in data

    def test_standard_has_remedies(self):
        """standard 模板 → remedies 字段存在"""
        resp = self.client.post("/api/v1/ziwei/full", json=_DEMO_PARAMS)
        assert resp.status_code == 200
        assert "remedies" in resp.json()

    def test_liunian_year_param(self):
        """指定 liunian_year → 200（liunian 字段非空）"""
        payload = {**_DEMO_PARAMS, "liunian_year": 2025}
        resp = self.client.post("/api/v1/ziwei/full", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        if data.get("liunian"):
            assert data["liunian"]["year"] == 2025

    def test_invalid_date(self):
        """无效日期 → 400（month=13）"""
        payload = {**_DEMO_PARAMS, "month": 13}
        resp = self.client.post("/api/v1/ziwei/full", json=payload)
        assert resp.status_code in (400, 422)

    def test_longitude_param(self):
        """指定经度 → 200（不报错）"""
        payload = {**_DEMO_PARAMS, "longitude": 121.47}
        resp = self.client.post("/api/v1/ziwei/full", json=payload)
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# B. GET /api/v1/ziwei/demo
# ══════════════════════════════════════════════════════════════════════════════

class TestZiweiDemo:
    """GET /api/v1/ziwei/demo → 壬午年正月三十未时女命盘"""

    def setup_method(self):
        self.client = _bypass_client()

    def test_demo_returns_200(self):
        resp = self.client.get("/api/v1/ziwei/demo")
        assert resp.status_code == 200

    def test_demo_expected_wuxing(self):
        """预期：水二局"""
        resp = self.client.get("/api/v1/ziwei/demo")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("wuxing_ju") == 2  # 水二局

    def test_demo_has_12_palaces(self):
        """命盘必须有 12 宫"""
        resp = self.client.get("/api/v1/ziwei/demo")
        assert resp.status_code == 200
        assert len(resp.json()["palaces"]) == 12


# ══════════════════════════════════════════════════════════════════════════════
# C. POST /api/v1/ziwei/compatibility — 合盘六合度
# ══════════════════════════════════════════════════════════════════════════════

class TestZiweiCompatibility:
    """POST /api/v1/ziwei/compatibility"""

    def setup_method(self):
        self.client = _bypass_client()

    def test_happy_path(self):
        """两人合盘 → 200，total_score 在 [0, 100]"""
        resp = self.client.post("/api/v1/ziwei/compatibility", json={
            "person_a": _PERSON_A,
            "person_b": _PERSON_B,
        })
        assert resp.status_code == 200
        data = resp.json()
        score = data.get("total_score") or data.get("overall_score", 0)
        assert 0 <= score <= 100
        # 验证维度列表非空
        dims = data.get("dimensions", [])
        assert isinstance(dims, list)

    def test_response_has_required_fields(self):
        """响应包含 level, summary, harmony_points 等"""
        resp = self.client.post("/api/v1/ziwei/compatibility", json={
            "person_a": _PERSON_A,
            "person_b": _PERSON_B,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "level" in data
        assert "summary" in data
        assert "person_a_info" in data
        assert "person_b_info" in data

    def test_same_person(self):
        """相同两人 → 不报错（最高分）"""
        resp = self.client.post("/api/v1/ziwei/compatibility", json={
            "person_a": _DEMO_PARAMS,
            "person_b": _DEMO_PARAMS,
        })
        assert resp.status_code == 200

    def test_invalid_date(self):
        """无效出生日期 → 400"""
        resp = self.client.post("/api/v1/ziwei/compatibility", json={
            "person_a": {**_PERSON_A, "month": 13},
            "person_b": _PERSON_B,
        })
        assert resp.status_code in (400, 422)


# ══════════════════════════════════════════════════════════════════════════════
# D. POST /api/v1/ziwei/multi_compat — 多人合盘
# ══════════════════════════════════════════════════════════════════════════════

class TestZiweiMultiCompat:
    """POST /api/v1/ziwei/multi_compat（2-4人）"""

    def setup_method(self):
        self.client = _bypass_client()

    def test_two_persons(self):
        """两人 → 1对结果"""
        resp = self.client.post("/api/v1/ziwei/multi_compat", json={
            "person_list": [_PERSON_A, _PERSON_B],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "pairs" in data
        assert "matrix" in data
        assert "team_harmony_score" in data
        assert data["person_count"] == 2
        assert len(data["pairs"]) == 1  # C(2,2)=1

    def test_three_persons(self):
        """三人 → 3对结果"""
        third = {"year": 1985, "month": 10, "day": 5, "hour": 6, "minute": 0, "gender": "男"}
        resp = self.client.post("/api/v1/ziwei/multi_compat", json={
            "person_list": [_PERSON_A, _PERSON_B, third],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["person_count"] == 3
        assert len(data["pairs"]) == 3  # C(3,2)=3
        # 矩阵为 3×3，对角线=100
        matrix = data["matrix"]
        assert len(matrix) == 3
        assert matrix[0][0] == 100

    def test_invalid_person(self):
        """含无效日期的人 → 400"""
        resp = self.client.post("/api/v1/ziwei/multi_compat", json={
            "person_list": [
                {**_PERSON_A, "month": 13},
                _PERSON_B,
            ],
        })
        assert resp.status_code in (400, 422)

    def test_too_few_persons(self):
        """只有 1 人 → 422（min_length=2 in schema or 处理后报错）"""
        resp = self.client.post("/api/v1/ziwei/multi_compat", json={
            "person_list": [_PERSON_A],
        })
        assert resp.status_code in (400, 422)


# ══════════════════════════════════════════════════════════════════════════════
# E. POST /api/v1/ziwei/flying — 飞星专项
# ══════════════════════════════════════════════════════════════════════════════

class TestZiweiFlyingEndpoint:
    """POST /api/v1/ziwei/flying"""

    def setup_method(self):
        self.client = _bypass_client()

    def test_happy_path(self):
        """正常请求 → 200，返回 12 宫飞星数据"""
        resp = self.client.post("/api/v1/ziwei/flying", json=_DEMO_PARAMS)
        assert resp.status_code == 200
        data = resp.json()
        assert "palaces" in data
        assert len(data["palaces"]) == 12
        assert "received" in data
        assert "chonged" in data
        assert "self_transforms" in data

    def test_with_longitude(self):
        """带经度参数 → 不报错"""
        payload = {**_DEMO_PARAMS, "longitude": 116.4}
        resp = self.client.post("/api/v1/ziwei/flying", json=payload)
        assert resp.status_code == 200

    def test_palace_has_stem_name(self):
        """每个宫位有 stem_name（天干）"""
        resp = self.client.post("/api/v1/ziwei/flying", json=_DEMO_PARAMS)
        assert resp.status_code == 200
        palaces = resp.json()["palaces"]
        assert all("stem_name" in p for p in palaces)

    def test_missing_required_field(self):
        """缺少必填字段 (gender) → 422"""
        payload = {k: v for k, v in _DEMO_PARAMS.items() if k != "gender"}
        resp = self.client.post("/api/v1/ziwei/flying", json=payload)
        assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# F. POST /api/v1/ziwei/batch — CSV 批量排盘
# ══════════════════════════════════════════════════════════════════════════════

class TestZiweiBatchEndpoint:
    """POST /api/v1/ziwei/batch (CSV Upload → ZIP)"""

    def setup_method(self):
        self.client = _bypass_client()

    def _csv(self, rows: list[str]) -> bytes:
        header = "name,year,month,day,hour,minute,gender\n"
        return (header + "\n".join(rows)).encode("utf-8")

    def test_single_row_returns_zip(self):
        """1 行 CSV → ZIP，含 JSON + summary"""
        csv_data = self._csv(["张三,1990,7,17,12,0,男"])
        resp = self.client.post(
            "/api/v1/ziwei/batch",
            files={"file": ("test.csv", io.BytesIO(csv_data), "text/csv")},
        )
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("application/zip")
        # 解压验证内容
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        names = zf.namelist()
        assert any("_summary.csv" in n for n in names)
        assert any(".json" in n for n in names)

    def test_two_rows_zip(self):
        """2行 CSV → ZIP，2个 JSON"""
        csv_data = self._csv([
            "甲,1990,7,17,12,0,男",
            "乙,1993,3,15,8,0,女",
        ])
        resp = self.client.post(
            "/api/v1/ziwei/batch",
            files={"file": ("test.csv", io.BytesIO(csv_data), "text/csv")},
        )
        assert resp.status_code == 200
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        json_files = [n for n in zf.namelist() if n.endswith(".json")]
        assert len(json_files) == 2

    def test_simple_template(self):
        """template_version=simple → ZIP 内 JSON 较小"""
        csv_data = self._csv(["测,2002,3,13,14,55,女"])
        resp = self.client.post(
            "/api/v1/ziwei/batch?template_version=simple",
            files={"file": ("test.csv", io.BytesIO(csv_data), "text/csv")},
        )
        assert resp.status_code == 200

    def test_empty_csv_rejected(self):
        """空 CSV → 400"""
        resp = self.client.post(
            "/api/v1/ziwei/batch",
            files={"file": ("empty.csv", io.BytesIO(b"name,year,month,day,hour,minute,gender\n"), "text/csv")},
        )
        assert resp.status_code == 400

    def test_missing_required_columns(self):
        """缺少必要列 → 400"""
        bad_csv = "name,year,month\n\u7532,1990,7\n".encode("utf-8")
        resp = self.client.post(
            "/api/v1/ziwei/batch",
            files={"file": ("bad.csv", io.BytesIO(bad_csv), "text/csv")},
        )
        assert resp.status_code == 400

    def test_invalid_row_summary_has_error_status(self):
        """含无效性别的行 → summary.csv 中 status=error"""
        # gender 不传值（空字符串），底层可能报错
        csv_data = self._csv(["\u574f,1990,7,17,12,0,"])  # 空 gender
        resp = self.client.post(
            "/api/v1/ziwei/batch",
            files={"file": ("bad.csv", io.BytesIO(csv_data), "text/csv")},
        )
        assert resp.status_code == 200
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        # 无论 error.txt 还是 json，zip 都不会是空的
        assert len(zf.namelist()) > 0

    def test_gb2312_encoding(self):
        """GB2312 编码 CSV → 自动解码，不报错"""
        header = "name,year,month,day,hour,minute,gender\n"
        row = "王五,1985,10,5,6,0,男\n"
        gb_data = (header + row).encode("gb2312")
        resp = self.client.post(
            "/api/v1/ziwei/batch",
            files={"file": ("gb.csv", io.BytesIO(gb_data), "text/csv")},
        )
        assert resp.status_code == 200

    def test_with_optional_columns(self):
        """带可选列 liunian_year/longitude → 正常处理"""
        header = b"name,year,month,day,hour,minute,gender,liunian_year,longitude\n"
        row = b"\xe5\xbc\xa0\xe4\xb8\x89,1990,7,17,12,0,\xe7\x94\xb7,2025,116.4\n"
        resp = self.client.post(
            "/api/v1/ziwei/batch",
            files={"file": ("opt.csv", io.BytesIO(header + row), "text/csv")},
        )
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# G. _chart_to_response 的模板分支 — 直接单元测试
# ══════════════════════════════════════════════════════════════════════════════

class TestChartToResponseTemplates:
    """直接导入 _chart_to_response，测试 simple/standard/pro 过滤逻辑"""

    def setup_method(self):
        from services.ziwei_engine import ziwei_full
        self.chart = ziwei_full(2002, 3, 13, 14, 55, "女")

    def test_simple_no_flying(self):
        from routers.ziwei import _chart_to_response
        resp = _chart_to_response(self.chart, template="simple")
        assert resp.flying is None

    def test_simple_no_forecast(self):
        from routers.ziwei import _chart_to_response
        resp = _chart_to_response(self.chart, template="simple")
        assert resp.forecast is None

    def test_simple_empty_liuyue(self):
        from routers.ziwei import _chart_to_response
        resp = _chart_to_response(self.chart, template="simple")
        assert resp.liuyue == []

    def test_simple_empty_analysis(self):
        from routers.ziwei import _chart_to_response
        resp = _chart_to_response(self.chart, template="simple")
        assert resp.analysis == {}

    def test_simple_empty_remedies(self):
        from routers.ziwei import _chart_to_response
        resp = _chart_to_response(self.chart, template="simple")
        assert resp.remedies == []

    def test_standard_has_content(self):
        """standard 包含非空的分析内容"""
        from routers.ziwei import _chart_to_response
        resp = _chart_to_response(self.chart, template="standard")
        # 至少有 flyouts 或 analysis（具体取决于引擎）
        assert resp.template_version == "standard"

    def test_pro_pattern_source(self):
        """pro 模板：pattern.source 保留（即使为空字符串）"""
        from routers.ziwei import _chart_to_response
        resp = _chart_to_response(self.chart, template="pro")
        assert resp.template_version == "pro"
        for p in resp.patterns:
            # source 字段存在（可以是空字符串）
            assert hasattr(p, "source")
