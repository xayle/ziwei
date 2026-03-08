"""
tests/test_quickstart.py — POST /api/v1/quickstart 功能测试

覆盖范围：
  - 正常流程：一步建档+计算，201 响应体包含 case 和 compute 两段
  - case.owner_id == 当前登录用户（所有权归属正确）
  - 无认证访问 → 401
  - 非法 IANA 时区 → 422
  - tags 传 List[str] 能被正常归一化
  - quickstart 建档后可通过 GET /api/v1/cases/{id} 正确取回
"""
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from app.models import User


# 禁用速率限制（防止多测试文件并发打 429）
@pytest.fixture(scope="module", autouse=True)
def _disable_rate_limit():
    _prev = os.environ.get("AUTH_BYPASS")
    os.environ["AUTH_BYPASS"] = "true"
    yield
    if _prev is None:
        os.environ.pop("AUTH_BYPASS", None)
    else:
        os.environ["AUTH_BYPASS"] = _prev


VALID_PAYLOAD = {
    "name": "Quickstart Test",
    "birth_dt_local": "2000-01-15T08:30:00",
    "tz": "Asia/Shanghai",
    "lon": 121.47,
    "gender": "male",
    "city": "Shanghai",
    "solar_time_enabled": False,
    "mode": "dual",
}


@pytest.mark.api
class TestQuickstartAPI:
    """POST /api/v1/quickstart 全功能测试"""

    def test_quickstart_success(self, client_with_auth: TestClient):
        """正常建档+计算返回 201，响应包含 case 和 compute 两段"""
        response = client_with_auth.post("/api/v1/quickstart", json=VALID_PAYLOAD)
        assert response.status_code == 201, response.text
        data = response.json()
        assert "case" in data, "响应应包含 case 字段"
        assert "compute" in data, "响应应包含 compute 字段"

    def test_quickstart_case_fields(self, client_with_auth: TestClient):
        """case 字段包含必须的 id / name / owner 归属字段"""
        response = client_with_auth.post("/api/v1/quickstart", json=VALID_PAYLOAD)
        assert response.status_code == 201, response.text
        case_data = response.json()["case"]
        assert "id" in case_data
        assert case_data["name"] == VALID_PAYLOAD["name"]
        assert case_data["gender"] == VALID_PAYLOAD["gender"]
        assert case_data["lon"] == VALID_PAYLOAD["lon"]

    def test_quickstart_compute_fields(self, client_with_auth: TestClient):
        """compute 字段包含 case_id / compute_batch_id / tasks / snapshots_created"""
        response = client_with_auth.post("/api/v1/quickstart", json=VALID_PAYLOAD)
        assert response.status_code == 201, response.text
        compute_data = response.json()["compute"]
        assert "case_id" in compute_data
        assert "compute_batch_id" in compute_data
        assert "tasks" in compute_data
        assert "snapshots_created" in compute_data

    def test_quickstart_compute_case_id_matches(self, client_with_auth: TestClient):
        """compute.case_id 必须与 case.id 一致"""
        response = client_with_auth.post("/api/v1/quickstart", json=VALID_PAYLOAD)
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["compute"]["case_id"] == body["case"]["id"]

    def test_quickstart_case_accessible_via_get(self, client_with_auth: TestClient):
        """quickstart 创建的案例可通过 GET /api/v1/cases/{id} 正确取回"""
        response = client_with_auth.post("/api/v1/quickstart", json=VALID_PAYLOAD)
        assert response.status_code == 201, response.text
        case_id = response.json()["case"]["id"]

        get_resp = client_with_auth.get(f"/api/v1/cases/{case_id}")
        assert get_resp.status_code == 200, get_resp.text
        assert get_resp.json()["id"] == case_id

    def test_quickstart_owner_matches_current_user(
        self, client_with_auth: TestClient, test_user: User
    ):
        """quickstart 所创建的案例应出现在当前用户的案例列表中（owner_id 归属正确）"""
        response = client_with_auth.post("/api/v1/quickstart", json=VALID_PAYLOAD)
        assert response.status_code == 201, response.text
        case_id = response.json()["case"]["id"]

        list_resp = client_with_auth.get("/api/v1/cases")
        assert list_resp.status_code == 200, list_resp.text
        items = list_resp.json().get("items", [])
        found_ids = [item["id"] for item in items]
        assert case_id in found_ids, "quickstart 创建的案例应在当前用户案例列表中"

    def test_quickstart_with_tags_list(self, client_with_auth: TestClient):
        """tags 传 List[str] 应被接受并归一化"""
        payload = {**VALID_PAYLOAD, "tags": ["八字", "测试", "2000"]}
        response = client_with_auth.post("/api/v1/quickstart", json=payload)
        assert response.status_code == 201, response.text
        case_data = response.json()["case"]
        assert case_data.get("tags") is not None

    def test_quickstart_with_tags_string(self, client_with_auth: TestClient):
        """tags 传逗号分隔字符串也应被接受"""
        payload = {**VALID_PAYLOAD, "tags": "八字,测试"}
        response = client_with_auth.post("/api/v1/quickstart", json=payload)
        assert response.status_code == 201, response.text

    def test_quickstart_without_auth_returns_401(self, client: TestClient):
        """未认证请求应返回 401（临时关闭 AUTH_BYPASS 以测试真实认证逻辑）"""
        import os as _os
        _prev = _os.environ.pop("AUTH_BYPASS", None)
        try:
            response = client.post("/api/v1/quickstart", json=VALID_PAYLOAD)
            assert response.status_code in (401, 403), response.text
        finally:
            if _prev is not None:
                _os.environ["AUTH_BYPASS"] = _prev

    def test_quickstart_invalid_timezone_returns_422(self, client_with_auth: TestClient):
        """非法 IANA 时区应返回 422"""
        payload = {**VALID_PAYLOAD, "tz": "NotA/ValidTimezone"}
        response = client_with_auth.post("/api/v1/quickstart", json=payload)
        # ZoneInfo 验证在路由内部触发（自定义异常），可能返回 422 或 400
        assert response.status_code in (400, 422), response.text

    def test_quickstart_missing_required_fields_returns_422(self, client_with_auth: TestClient):
        """缺少必填字段应返回 422"""
        incomplete = {"name": "test"}  # 缺少 birth_dt_local / tz / lon
        response = client_with_auth.post("/api/v1/quickstart", json=incomplete)
        assert response.status_code == 422, response.text

    def test_quickstart_invalid_lon_returns_422(self, client_with_auth: TestClient):
        """超出范围经度应返回 422"""
        payload = {**VALID_PAYLOAD, "lon": 999.0}
        response = client_with_auth.post("/api/v1/quickstart", json=payload)
        assert response.status_code == 422, response.text
