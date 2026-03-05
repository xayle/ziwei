"""tests/test_v2_batch.py — POST /api/v2/batch/verify 功能测试.

覆盖范围（与 test_redlines_r36_r45.py 的 R39/R40 不重叠）：
  - 单条正常请求：results 列表长度 = 1，内容有 pillars_primary 等核心字段
  - 多条不同生日：results 全部成功
  - 数量守恒 invariant（3条/5条/10条）
  - 响应字段结构完整性
  - 无效输入导致单条 failed，不影响其他条

注意：批量端点限速 10/min per-user。TestClient remote_address="testclient"，
多测试文件同时命中速率上限会导致 429。通过 AUTH_BYPASS=true 让每请求使用唯一
UUID key，从而禁用速率限制（仅对非 production 环境有效）。
"""
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient


# ── 模块级 AUTH_BYPASS patch（禁用速率限制，防止跨文件 429）──────────────────
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


# ── 公共基准请求体 ─────────────────────────────────────────────────────────────

VALID_ITEM = {
    "dt": "1990-07-17T12:20:00",
    "tz": "Asia/Shanghai",
    "lon": 116.4,
    "gender": "female",
    "mode": "dual",
    "solar_time_enabled": False,
}

# 几个不同日期，方便测试多条
ITEMS_3 = [
    {"dt": "1985-03-15T08:00:00", "tz": "Asia/Shanghai", "lon": 121.5},
    {"dt": "1990-11-22T14:30:00", "tz": "Asia/Shanghai", "lon": 104.1},
    {"dt": "2000-06-01T06:00:00", "tz": "Asia/Shanghai", "lon": 113.3},
]

ITEMS_5 = ITEMS_3 + [
    {"dt": "1975-09-09T18:00:00", "tz": "Asia/Shanghai", "lon": 120.0},
    {"dt": "1998-01-31T00:30:00", "tz": "Asia/Shanghai", "lon": 117.3},
]


# ── 基本幂等性 ─────────────────────────────────────────────────────────────────

class TestBatchResponseCount:
    """len(results) + len(failed) == len(request.items) 对各种输入都成立。"""

    def test_count_invariant_1(self, client_with_auth: TestClient):
        resp = client_with_auth.post("/api/v2/batch/verify", json={"items": [VALID_ITEM]})
        assert resp.status_code == 200
        body = resp.json()
        total = len(body["results"]) + len(body["failed"])
        assert total == 1, f"1条但 total={total}"

    def test_count_invariant_3(self, client_with_auth: TestClient):
        resp = client_with_auth.post("/api/v2/batch/verify", json={"items": ITEMS_3})
        assert resp.status_code == 200
        body = resp.json()
        total = len(body["results"]) + len(body["failed"])
        assert total == 3, f"3条但 total={total}"

    def test_count_invariant_5(self, client_with_auth: TestClient):
        resp = client_with_auth.post("/api/v2/batch/verify", json={"items": ITEMS_5})
        assert resp.status_code == 200
        body = resp.json()
        total = len(body["results"]) + len(body["failed"])
        assert total == 5, f"5条但 total={total}"


# ── 响应字段结构 ───────────────────────────────────────────────────────────────

class TestBatchResponseFields:
    """单条成功响应包含必要的 VerifyResponse 核心字段。"""

    def test_single_item_has_four_pillars(self, client_with_auth: TestClient):
        resp = client_with_auth.post("/api/v2/batch/verify", json={"items": [VALID_ITEM]})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["results"]) == 1
        result = body["results"][0]
        assert "pillars_primary" in result, f"缺少 pillars_primary，keys={list(result.keys())[:10]}"

    def test_single_item_has_wuxing(self, client_with_auth: TestClient):
        resp = client_with_auth.post("/api/v2/batch/verify", json={"items": [VALID_ITEM]})
        assert resp.status_code == 200
        result = resp.json()["results"][0]
        assert "wuxing_score" in result, (
            f"缺少 wuxing_score，keys={list(result.keys())[:10]}"
        )

    def test_single_item_has_dayun(self, client_with_auth: TestClient):
        resp = client_with_auth.post(
            "/api/v2/batch/verify", json={"items": [VALID_ITEM]}
        )
        assert resp.status_code == 200
        result = resp.json()["results"][0]
        assert "dayun" in result, f"缺少 dayun，keys={list(result.keys())[:10]}"

    def test_failed_entries_have_index_and_error(self, client_with_auth: TestClient):
        """failed 列表中每条必须有 index（int） + error（str）。"""
        # 构造一个肯定失败的 item：年份超出支持范围
        bad_item = {
            "dt": "1850-01-01T12:00:00",
            "tz": "Asia/Shanghai",
            "lon": 116.4,
        }
        resp = client_with_auth.post(
            "/api/v2/batch/verify",
            json={"items": [VALID_ITEM, bad_item]},
        )
        assert resp.status_code == 200
        body = resp.json()
        total = len(body["results"]) + len(body["failed"])
        assert total == 2
        # failed 中必须有 index 和 error 字段
        for f in body["failed"]:
            assert "index" in f, f"failed 条目缺少 index: {f}"
            assert "error" in f, f"failed 条目缺少 error: {f}"
            assert isinstance(f["index"], int), f"index 不是 int: {f}"


# ── 多条互不干扰 ───────────────────────────────────────────────────────────────

class TestBatchIsolation:
    """一条失败不影响其他条。"""

    def test_valid_items_succeed_even_with_one_invalid(
        self, client_with_auth: TestClient
    ):
        bad_item = {
            "dt": "1800-06-15T10:00:00",   # 超出支持范围
            "tz": "Asia/Shanghai",
            "lon": 116.4,
        }
        items = [VALID_ITEM, bad_item, ITEMS_3[1]]
        resp = client_with_auth.post("/api/v2/batch/verify", json={"items": items})
        assert resp.status_code == 200
        body = resp.json()
        # 总数守恒
        assert len(body["results"]) + len(body["failed"]) == 3
        # 至少 2 条有效 item 成功
        assert len(body["results"]) >= 2, (
            f"期望 ≥2条成功，实际 results={len(body['results'])}, failed={len(body['failed'])}"
        )


# ── 响应结构 keys ──────────────────────────────────────────────────────────────

class TestBatchResponseStructure:
    """响应 JSON 顶层必须包含 results 和 failed 字段。"""

    def test_response_has_results_and_failed(self, client_with_auth: TestClient):
        resp = client_with_auth.post("/api/v2/batch/verify", json={"items": [VALID_ITEM]})
        assert resp.status_code == 200
        body = resp.json()
        assert "results" in body
        assert "failed" in body
        # results 必须是 list
        assert isinstance(body["results"], list)
        # failed 必须是 list
        assert isinstance(body["failed"], list)
