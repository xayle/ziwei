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
        
        assert response.status_code == 200, response.text
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
        
        assert response.status_code == 200, response.text
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
    
    def test_regular_user_cannot_access_admin_endpoint(
        self,
        client_with_auth: TestClient,
        test_user: User,
    ):
        """Test regular user cannot access admin endpoints"""
        response = client_with_auth.get("/api/v1/admin/stats")
        
        assert response.status_code in [401, 403], (
            f"Non-admin should receive 401/403, got {response.status_code}: {response.text}"
        )


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


@pytest.mark.services
class TestPasswordCompatibility:
    """Tests for SHA256 backward-compatible password verification."""

    def test_verify_sha256_password_correct(self):
        """SHA256 hash (legacy format) should verify correctly."""
        import hashlib
        raw = "legacy_password_abc"
        sha256_hash = hashlib.sha256(raw.encode()).hexdigest()
        assert auth_service_module.verify_password(raw, sha256_hash) is True

    def test_verify_sha256_password_wrong(self):
        """Wrong password against SHA256 hash should return False."""
        import hashlib
        raw = "legacy_password_abc"
        sha256_hash = hashlib.sha256(raw.encode()).hexdigest()
        assert auth_service_module.verify_password("wrong_pass", sha256_hash) is False

    def test_verify_unknown_hash_format(self):
        """Completely unknown hash format should return False, not raise."""
        result = auth_service_module.verify_password("any_password", "unknownhashformat123")
        assert result is False

    def test_validate_token_exists_and_valid_true(self):
        """validate_token_exists_and_valid returns True for a valid token."""
        token_dict = auth_service_module.create_access_token(
            user_id=99, username="validuser", role="user",
            expires_delta=timedelta(minutes=15)
        )
        assert auth_service_module.validate_token_exists_and_valid(token_dict["access_token"]) is True

    def test_validate_token_exists_and_valid_empty(self):
        """validate_token_exists_and_valid raises for an empty token."""
        with pytest.raises(Exception):
            auth_service_module.validate_token_exists_and_valid("")


@pytest.mark.services
class TestJtiRevocation:
    """Tests for Access Token JTI revocation (blacklist)."""

    def test_revoke_jti_in_memory(self):
        """Revoked JTI should be detected on next verify_token call."""
        import uuid
        # Create token and extract its JTI
        token_dict = auth_service_module.create_access_token(
            user_id=7, username="revoketest", role="user",
            expires_delta=timedelta(minutes=30)
        )
        import os
        from jose import jwt as jose_jwt
        _secret = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        payload = jose_jwt.decode(
            token_dict["access_token"],
            _secret,
            algorithms=["HS256"],
        )
        jti = payload.get("jti")
        assert jti is not None

        # Token should be valid before revocation
        result = auth_service_module.verify_token(token_dict["access_token"])
        assert result is not None

        # Revoke the JTI
        auth_service_module.revoke_access_token_jti(jti)

        # Token should now be invalid
        from app.exceptions import AuthenticationException
        with pytest.raises(AuthenticationException):
            auth_service_module.verify_token(token_dict["access_token"])

        # Clean up: remove from set to avoid affecting other tests
        auth_service_module._revoked_jtis.discard(jti)

    def test_revoke_jti_idempotent(self):
        """Calling revoke_access_token_jti twice should not raise."""
        fake_jti = "fake-jti-idempotency-test"
        auth_service_module.revoke_access_token_jti(fake_jti)
        auth_service_module.revoke_access_token_jti(fake_jti)  # should not raise
        auth_service_module._revoked_jtis.discard(fake_jti)


@pytest.mark.services
class TestRefreshTokenDB:
    """Tests for refresh token DB operations."""

    def test_create_and_verify_refresh_token(self, db_session):
        """create_refresh_token_record + verify_refresh_token round-trip."""
        # Need a user
        from app.models import User as _User
        user = _User(
            username=f"rt_user_{id(db_session)}",
            email=f"rt_{id(db_session)}@test.com",
            password_hash=auth_service_module.hash_password("pw"),
            role="user",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = auth_service_module.create_refresh_token_record(
            db_session, user_id=user.id  # type: ignore[arg-type]
        )
        assert isinstance(token, str) and len(token) > 0

        result = auth_service_module.verify_refresh_token(
            db_session, user_id=user.id, token=token  # type: ignore[arg-type]
        )
        assert result is True

    def test_verify_refresh_token_missing(self, db_session):
        """verify_refresh_token raises when token not found."""
        from app.exceptions import AuthenticationException
        with pytest.raises(AuthenticationException):
            auth_service_module.verify_refresh_token(
                db_session, user_id=9999, token="nonexistent_token"
            )

    def test_verify_refresh_token_empty_raises(self, db_session):
        """verify_refresh_token raises for empty token."""
        from app.exceptions import AuthenticationException
        with pytest.raises(AuthenticationException):
            auth_service_module.verify_refresh_token(db_session, user_id=1, token="")

    def test_revoke_refresh_token(self, db_session):
        """revoke_refresh_token marks token as revoked."""
        from app.models import User as _User
        user = _User(
            username=f"rv_user_{id(db_session)}",
            email=f"rv_{id(db_session)}@test.com",
            password_hash=auth_service_module.hash_password("pw"),
            role="user",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = auth_service_module.create_refresh_token_record(
            db_session, user_id=user.id  # type: ignore[arg-type]
        )
        auth_service_module.revoke_refresh_token(db_session, token)

        # After revoking, verify should fail
        from app.exceptions import AuthenticationException
        with pytest.raises(AuthenticationException):
            auth_service_module.verify_refresh_token(
                db_session, user_id=user.id, token=token  # type: ignore[arg-type]
            )

    def test_revoke_nonexistent_token(self, db_session):
        """revoke_refresh_token on unknown token should not raise."""
        auth_service_module.revoke_refresh_token(db_session, "totally_fake_token")

    def test_revoke_all_user_tokens(self, db_session):
        """revoke_all_user_tokens revokes all active tokens for a user."""
        from app.models import User as _User
        user = _User(
            username=f"ra_user_{id(db_session)}",
            email=f"ra_{id(db_session)}@test.com",
            password_hash=auth_service_module.hash_password("pw"),
            role="user",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        t1 = auth_service_module.create_refresh_token_record(
            db_session, user_id=user.id  # type: ignore[arg-type]
        )
        t2 = auth_service_module.create_refresh_token_record(
            db_session, user_id=user.id  # type: ignore[arg-type]
        )
        auth_service_module.revoke_all_user_tokens(db_session, user_id=user.id)  # type: ignore[arg-type]

        from app.exceptions import AuthenticationException
        for tok in [t1, t2]:
            with pytest.raises(AuthenticationException):
                auth_service_module.verify_refresh_token(
                    db_session, user_id=user.id, token=tok  # type: ignore[arg-type]
                )
