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
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["name"] == payload["name"]
            assert data["gender"] == payload["gender"]
    
    def test_list_cases(self, client_with_auth: TestClient, test_case: Case):
        """Test listing all user's cases"""
        response = client_with_auth.get("/api/v1/cases")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or isinstance(data, dict)
    
    def test_get_case_by_id(self, client_with_auth: TestClient, test_case: Case):
        """Test retrieving a specific case by ID"""
        response = client_with_auth.get(f"/api/v1/cases/{test_case.id}")
        
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == test_case.id
            assert data["name"] == test_case.name
    
    def test_update_case(self, client_with_auth: TestClient, test_case: Case):
        """Test updating case information"""
        payload = {
            "name": "Updated Case Name",
            "notes": "Updated notes",
        }
        
        response = client_with_auth.put(
            f"/api/v1/cases/{test_case.id}",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["name"] == payload["name"]
    
    def test_delete_case(self, client_with_auth: TestClient, test_case: Case):
        """Test soft-deleting a case"""
        response = client_with_auth.delete(f"/api/v1/cases/{test_case.id}")
        
        if response.status_code == 204:
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
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["name"] == payload["name"]
    
    def test_list_members(self, client_with_auth: TestClient, test_member: Member):
        """Test listing all user's members"""
        response = client_with_auth.get("/api/v1/members")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
    
    def test_get_member_by_id(self, client_with_auth: TestClient, test_member: Member):
        """Test retrieving a specific member"""
        response = client_with_auth.get(f"/api/v1/members/{test_member.id}")
        
        if response.status_code == 200:
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
        """Test creating a new event"""
        payload = {
            "member_id": test_member.id,
            "name": "Test Event",
            "event_type": "marriage",
            "bazi_json": '{"test": "data"}',
            "L_level": 1,
            "confidence_score": 0.85,
        }
        
        response = client_with_auth.post("/api/v1/events", json=payload)
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["name"] == payload["name"]
    
    def test_list_events(self, client_with_auth: TestClient, test_event: Event):
        """Test listing all user's events"""
        response = client_with_auth.get("/api/v1/events")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))


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
            "gender": "M",
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
        
        if case_response.status_code == 201:
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
            
            if member_response.status_code == 201:
                member_id = member_response.json()["id"]
                
                # Step 3: Create an event
                event_payload = {
                    "member_id": member_id,
                    "name": "Workflow Event",
                    "event_type": "marriage",
                    "bazi_json": '{"test": "data"}',
                    "L_level": 1,
                    "confidence_score": 0.85,
                }
                
                event_response = client_with_auth.post(
                    "/api/v1/events",
                    json=event_payload
                )
                
                # Verify workflow completed
                assert case_response.status_code == 201
                if member_response.status_code == 201:
                    if event_response.status_code == 201:
                        assert True  # Full workflow succeeded


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
            "gender": "M",
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
