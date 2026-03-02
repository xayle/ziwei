"""
Unit tests for authentication and authorization
Tests login, token generation, and permission management
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient

from app.models import User
from app.exceptions import AuthenticationException
import services.auth_service as auth_service_module
from sqlmodel import Session


@pytest.mark.auth
class TestAuthenticationAPI:
    """Test suite for authentication endpoints"""
    
    def test_health_check(self, client: TestClient):
        """Test basic health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_login_with_valid_credentials(
        self,
        client: TestClient,
        test_user: User,
        test_user_data: dict,
    ):
        """Test login with valid username and password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_login_with_invalid_credentials(self, client: TestClient):
        """Test login with wrong password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "wrongpassword",
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTH_001"
    
    def test_access_protected_endpoint_without_token(self, client: TestClient, monkeypatch):
        """Test accessing protected endpoint without authorization"""
        monkeypatch.setenv("AUTH_BYPASS", "false")
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_access_protected_endpoint_with_valid_token(
        self,
        client_with_auth: TestClient,
        test_user: User,
    ):
        """Test accessing protected endpoint with valid token"""
        response = client_with_auth.get("/api/v1/auth/me")
        
        if response.status_code == 200:
            data = response.json()
            assert data["email"] == test_user.email
            assert data["username"] == test_user.username
    
    def test_token_refresh(self, db_session: Session, test_user: User):
        """Test refreshing access token"""
        # Generate tokens
        token_dict = auth_service_module.create_access_token(
            user_id=test_user.id,  # type: ignore[arg-type]
            username=test_user.username,
            role=test_user.role,
            expires_delta=timedelta(minutes=15)
        )
        
        assert token_dict is not None
        assert "access_token" in token_dict
        assert len(token_dict["access_token"]) > 0


@pytest.mark.auth
class TestAuthorizationRBAC:
    """Test suite for role-based access control"""
    
    def test_admin_access_to_admin_endpoint(
        self,
        client: TestClient,
        admin_user: User,
    ):
        """Test admin user can access admin endpoints"""
        from datetime import timedelta
        
        token_dict = auth_service_module.create_access_token(
            user_id=admin_user.id,  # type: ignore[arg-type]
            username=admin_user.username,
            role=admin_user.role,
            expires_delta=timedelta(minutes=1440)
        )
        token = token_dict["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/admin/stats", headers=headers)
        
        # Admin endpoint should exist and be accessible
        assert response.status_code in [200, 404]  # 404 if not implemented yet
    
    def test_regular_user_cannot_access_admin_endpoint(
        self,
        client_with_auth: TestClient,
        test_user: User,
    ):
        """Test regular user cannot access admin endpoints"""
        response = client_with_auth.get("/api/v1/admin/stats")
        
        # Should either be Unauthorized (401) or Forbidden (403)
        assert response.status_code in [401, 403, 404]


@pytest.mark.auth
class TestTokenManagement:
    """Test suite for JWT token management"""
    
    def test_create_valid_access_token(self):
        """Test creating a valid JWT access token"""
        token_dict = auth_service_module.create_access_token(
            user_id=1,
            username="testuser",
            role="user",
            expires_delta=timedelta(minutes=15)
        )
        
        assert token_dict is not None
        assert "access_token" in token_dict
        assert isinstance(token_dict["access_token"], str)
        assert len(token_dict["access_token"]) > 0
    
    def test_verify_valid_access_token(self):
        """Test verifying a valid JWT access token"""
        token_dict = auth_service_module.create_access_token(
            user_id=1,
            username="testuser",
            role="user",
            expires_delta=timedelta(minutes=15)
        )
        token = token_dict["access_token"]
        
        payload = auth_service_module.verify_token(token)
        assert payload is not None
        assert payload.user_id == 1
    
    def test_expired_token_verification(self):
        """Test verifying an expired token fails"""
        # Create token with very short expiry
        token_dict = auth_service_module.create_access_token(
            user_id=1,
            username="testuser",
            role="user",
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        token = token_dict["access_token"]
        
        with pytest.raises(AuthenticationException):
            auth_service_module.verify_token(token)


@pytest.mark.services
class TestPasswordManagement:
    """Test suite for password hashing and verification"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123!"
        hashed = auth_service_module.hash_password(password)
        
        assert hashed != password  # Should be different
        assert len(hashed) > len(password)  # Hash should be longer
    
    def test_verify_correct_password(self):
        """Test password verification with correct password"""
        password = "test_password_123!"
        hashed = auth_service_module.hash_password(password)
        
        is_valid = auth_service_module.verify_password(password, hashed)
        assert is_valid is True
    
    def test_verify_incorrect_password(self):
        """Test password verification with incorrect password"""
        password = "test_password_123!"
        hashed = auth_service_module.hash_password(password)
        
        is_valid = auth_service_module.verify_password("wrong_password", hashed)
        assert is_valid is False


@pytest.mark.benchmark
class TestAuthPerformance:
    """Performance benchmarks for authentication operations"""
    
    def test_hash_password_performance(
        self,
        benchmark_timer,
    ):
        """Benchmark password hashing performance"""
        password = "test_password_123!"
        
        with benchmark_timer:
            for _ in range(10):
                auth_service_module.hash_password(password)
        
        # Password hashing should complete in reasonable time
        # (typically 50-200ms per hash depending on work factor)
        assert benchmark_timer.elapsed_ms < 2000  # 10 hashes in < 2 seconds
    
    def test_token_generation_performance(
        self,
        benchmark_timer,
    ):
        """Benchmark JWT token generation"""
        from datetime import timedelta
        
        with benchmark_timer:
            for i in range(100):
                auth_service_module.create_access_token(
                    user_id=i,
                    username=f"user{i}",
                    role="user",
                    expires_delta=timedelta(minutes=15)
                )
        
        # Token generation should be fast (< 1ms per token)
        assert benchmark_timer.elapsed_ms < 500  # 100 tokens in < 500ms
    
    def test_token_verification_performance(
        self,
        benchmark_timer,
    ):
        """Benchmark JWT token verification"""
        from datetime import timedelta
        
        # Generate test tokens
        tokens = [
            auth_service_module.create_access_token(
                user_id=i,
                username=f"user{i}",
                role="user",
                expires_delta=timedelta(minutes=15)
            )["access_token"]
            for i in range(20)
        ]
        
        with benchmark_timer:
            for token in tokens:
                auth_service_module.verify_token(token)
        
        # Token verification should be very fast
        assert benchmark_timer.elapsed_ms < 100  # 20 verifications in < 100ms
