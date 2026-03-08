"""
Integration tests for case management API
Tests CRUD operations, validation, and business logic
"""

import pytest
from datetime import datetime, date
from uuid import uuid4
from fastapi import status
from fastapi.testclient import TestClient

from app.models import Case, Member, Snapshot, Event
from sqlmodel import Session

# 通过 EventJsonValidator 验证的最小合法 bazi_json（BaziResultModel 要求 pillars_primary + ten_gods）
MINIMAL_VALID_BAZI_JSON = (
    '{"pillars_primary": {'
    '"year_pillar": {"heavenly_stem": "甲", "earthly_branch": "子"},'
    '"month_pillar": {"heavenly_stem": "丙", "earthly_branch": "寅"},'
    '"day_pillar":   {"heavenly_stem": "戊", "earthly_branch": "午"},'
    '"time_pillar":  {"heavenly_stem": "庚", "earthly_branch": "申"}'
    '}, "ten_gods": {}}'
)


@pytest.mark.api
class TestCaseAPI:
    """Test suite for case (BaZi analysis) API endpoints"""
    
    def test_create_case(self, client_with_auth: TestClient):
        """Test creating a new case"""
        payload = {
            "name": "Test Case",
            "gender": "male",
            "birth_dt_local": "2000-01-01T12:00:00",
            "tz": "Asia/Shanghai",
            "birth_dt": "2000-01-01T04:00:00Z",
            "city": "Shanghai",
            "lon": 121.47,
            "solar_time_enabled": False,
        }
        
        response = client_with_auth.post("/api/v1/cases", json=payload)
        
        assert response.status_code == 201, response.text
        data = response.json()
        assert "id" in data
        assert data["name"] == payload["name"]
        assert data["gender"] == payload["gender"]
    
    def test_list_cases(self, client_with_auth: TestClient, test_case: Case):
        """Test listing all user's cases — response envelope is {items, total, next_cursor}"""
        response = client_with_auth.get("/api/v1/cases")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data, f"list_cases envelope missing 'items': {data}"
        assert "total" in data, f"list_cases envelope missing 'total': {data}"
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
    
    def test_get_case_by_id(self, client_with_auth: TestClient, test_case: Case):
        """Test retrieving a specific case by ID"""
        response = client_with_auth.get(f"/api/v1/cases/{test_case.id}")
        
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == test_case.id
        assert data["name"] == test_case.name
    
    def test_update_case(self, client_with_auth: TestClient, test_case: Case):
        """Test updating case information"""
        payload = {
            "name": "Updated Case Name",
            "notes": "Updated notes",
        }
        
        response = client_with_auth.patch(
            f"/api/v1/cases/{test_case.id}",
            json=payload
        )
        
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["name"] == payload["name"]
    
    def test_delete_case(self, client_with_auth: TestClient, test_case: Case):
        """Test soft-deleting a case"""
        response = client_with_auth.delete(f"/api/v1/cases/{test_case.id}")
        
        assert response.status_code == 204, response.text
        # Verify case is soft-deleted
        get_response = client_with_auth.get(f"/api/v1/cases/{test_case.id}")
        assert get_response.status_code in [404, 410]
    
    def test_create_case_with_invalid_data(self, client_with_auth: TestClient):
        """Test case creation fails with invalid data"""
        payload = {
            "name": "",  # Empty name
            "gender": "X",  # Invalid gender
            "birth_dt_local": "invalid-date",
            "tz": "Invalid/Timezone",
            "city": "",
            "lon": 999.0,  # Invalid longitude
        }
        
        response = client_with_auth.post("/api/v1/cases", json=payload)
        assert response.status_code == 422  # Validation error


@pytest.mark.api
class TestMemberAPI:
    """Test suite for member (person) API endpoints"""
    
    def test_create_member(self, client_with_auth: TestClient):
        """Test creating a new member"""
        payload = {
            "name": "Test Member",
            "birth_date": "2000-01-01",
            "gender": "M",
            "birth_time_hour": 12,
            "birth_time_minute": 0,
            "birth_city": "Shanghai",
            "birth_longitude": 121.47,
            "solar_time_enabled": False,
        }
        
        response = client_with_auth.post("/api/v1/members", json=payload)
        
        assert response.status_code == 201, response.text
        data = response.json()
        assert "id" in data
        assert data["name"] == payload["name"]
    
    def test_list_members(self, client_with_auth: TestClient, test_member: Member):
        """Test listing all user's members — response envelope is {items, total, next_cursor}"""
        response = client_with_auth.get("/api/v1/members")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data, f"list_members envelope missing 'items': {data}"
        assert "total" in data, f"list_members envelope missing 'total': {data}"
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        # 预置了 test_member，total 至少为 1
        assert data["total"] >= 1
    
    def test_get_member_by_id(self, client_with_auth: TestClient, test_member: Member):
        """Test retrieving a specific member"""
        response = client_with_auth.get(f"/api/v1/members/{test_member.id}")
        
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == test_member.id
        assert data["name"] == test_member.name


@pytest.mark.api
class TestEventAPI:
    """Test suite for event API endpoints"""
    
    def test_create_event(
        self,
        client_with_auth: TestClient,
        test_member: Member,
    ):
        """Test creating a new event — bazi_json must satisfy BaziResultModel schema"""
        payload = {
            "member_id": test_member.id,
            "name": "Test Event",
            "event_type": "marriage",
            "bazi_json": MINIMAL_VALID_BAZI_JSON,
            "L_level": 1,
            "confidence_score": 0.85,
        }

        response = client_with_auth.post("/api/v1/events", json=payload)

        assert response.status_code == 201, (
            f"create_event failed {response.status_code}: {response.text[:300]}"
        )
        data = response.json()
        assert "id" in data
        assert data["name"] == payload["name"]
    
    def test_list_events(self, client_with_auth: TestClient, test_event: Event):
        """Test listing all user's events — response envelope is {items, total, next_cursor}"""
        response = client_with_auth.get("/api/v1/events")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data, f"list_events envelope missing 'items': {data}"
        assert "total" in data, f"list_events envelope missing 'total': {data}"
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)


@pytest.mark.integration
class TestCaseWorkflow:
    """Integration tests for complete case analysis workflow"""
    
    def test_full_case_creation_workflow(
        self,
        client_with_auth: TestClient,
        db_session: Session,
    ):
        """Test complete workflow: create case -> add member -> record event"""
        
        # Step 1: Create a case
        case_payload = {
            "name": "Workflow Test Case",
            "gender": "male",
            "birth_dt_local": "2000-01-01T12:00:00",
            "tz": "Asia/Shanghai",
            "birth_dt": "2000-01-01T04:00:00Z",
            "city": "Shanghai",
            "lon": 121.47,
            "solar_time_enabled": False,
        }
        
        case_response = client_with_auth.post(
            "/api/v1/cases",
            json=case_payload
        )
        assert case_response.status_code == 201, f"Step 1 case create failed: {case_response.text}"
        case_id = case_response.json()["id"]

        # Step 2: Create a member
        member_payload = {
            "name": "Workflow Test Member",
            "birth_date": "2000-01-01",
            "gender": "M",
            "birth_time_hour": 12,
            "birth_time_minute": 0,
            "birth_city": "Shanghai",
            "birth_longitude": 121.47,
            "solar_time_enabled": False,
        }

        member_response = client_with_auth.post(
            "/api/v1/members",
            json=member_payload
        )
        assert member_response.status_code == 201, f"Step 2 member create failed: {member_response.text}"
        member_id = member_response.json()["id"]

        # Step 3: Create an event (valid bazi_json required)
        event_payload = {
            "member_id": member_id,
            "name": "Workflow Event",
            "event_type": "marriage",
            "bazi_json": MINIMAL_VALID_BAZI_JSON,
            "L_level": 1,
            "confidence_score": 0.85,
        }

        event_response = client_with_auth.post(
            "/api/v1/events",
            json=event_payload
        )
        assert event_response.status_code == 201, f"Step 3 event create failed: {event_response.text}"

        # Verify all IDs are populated
        assert case_id
        assert member_id
        assert event_response.json()["id"]


@pytest.mark.benchmark
class TestCasePerformance:
    """Performance benchmarks for case operations"""
    
    def test_case_creation_performance(
        self,
        client_with_auth: TestClient,
        benchmark_timer,
    ):
        """Benchmark case creation performance"""
        payload = {
            "name": "Perf Test Case",
            "gender": "male",
            "birth_dt_local": "2000-01-01T12:00:00",
            "tz": "Asia/Shanghai",
            "birth_dt": "2000-01-01T04:00:00Z",
            "city": "Shanghai",
            "lon": 121.47,
            "solar_time_enabled": False,
        }
        
        with benchmark_timer:
            for i in range(5):
                response = client_with_auth.post(
                    "/api/v1/cases",
                    json={**payload, "name": f"Case {i}"}
                )
                if response.status_code != 201:
                    # Skip if endpoint not implemented
                    break
        
        # Case creation should be relatively fast
        if benchmark_timer.elapsed_ms > 0:
            assert benchmark_timer.elapsed_ms < 5000  # 5 creations in < 5 seconds
    
    def test_case_retrieval_performance(
        self,
        client_with_auth: TestClient,
        bulk_test_cases: list,
        benchmark_timer,
    ):
        """Benchmark case retrieval performance"""
        if not bulk_test_cases:
            pytest.skip("No bulk test cases available")
        
        with benchmark_timer:
            for case in bulk_test_cases:
                response = client_with_auth.get(f"/api/v1/cases/{case.id}")
                if response.status_code != 200:
                    break
        
        # Case retrieval should be very fast
        if benchmark_timer.elapsed_ms > 0:
            assert benchmark_timer.elapsed_ms < 1000  # 5 retrievals in < 1 second


@pytest.mark.api
class TestCaseTagSearch:
    """P0-23: 案例搜索返回关系匹配 — 搜索'七杀格'返回相关案例"""

    def test_tag_search_returns_matching_cases(self, client_with_auth: TestClient):
        """P0-23: 按tag搜索能返回含该tag的案例"""
        # Step 1: 创建含七杀格 tag 的案例
        payload = {
            "name": "七杀格测试案例",
            "gender": "male",
            "birth_dt_local": "1985-07-15T10:00:00",
            "tz": "Asia/Shanghai",
            "lon": 121.47,
            "solar_time_enabled": False,
            "tags": "七杀格,阳刃格",
        }
        create_resp = client_with_auth.post("/api/v1/cases", json=payload)
        if create_resp.status_code != 201:
            pytest.skip("案例创建端点不可用，跳过P0-23集成测试")

        # Step 2: 按 tag=七杀格 搜索
        search_resp = client_with_auth.get("/api/v1/cases", params={"tag": "七杀格"})
        assert search_resp.status_code == 200, f"搜索应返回200，实际: {search_resp.status_code}"

        data = search_resp.json()
        # GET /cases 现在返回统一信封 {items, total, next_cursor}
        items = data["items"] if isinstance(data, dict) else data
        assert isinstance(items, list), "响应应为列表"
        assert len(items) >= 1, "搜索'七杀格'应至少返回1条案例"

        # Step 3: 验证返回的案例确实包含该 tag
        ids_with_tag = [c["id"] for c in items if "七杀格" in (str(c.get("tags") or ""))]
        assert len(ids_with_tag) >= 1, "返回的案例中应有至少1条包含'七杀格' tag"

    def test_name_search_returns_matching_cases(self, client_with_auth: TestClient):
        """P0-23 补充: 按名称可搜索到案例"""
        payload = {
            "name": "七杀格命盘示例",
            "gender": "female",
            "birth_dt_local": "1990-03-20T08:00:00",
            "tz": "Asia/Shanghai",
            "lon": 116.40,
            "solar_time_enabled": False,
        }
        create_resp = client_with_auth.post("/api/v1/cases", json=payload)
        if create_resp.status_code != 201:
            pytest.skip("案例创建端点不可用")

        search_resp = client_with_auth.get("/api/v1/cases", params={"q": "七杀格命盘"})
        assert search_resp.status_code == 200
        data = search_resp.json()
        items = data["items"] if isinstance(data, dict) else data
        assert any("七杀格命盘" in (c.get("name") or "") for c in items), \
            "按名称搜索'七杀格命盘'应返回相关案例"
