"""
Pytest Configuration and Global Fixtures
Supports: test database, app fixtures, auth fixtures, performance testing
"""

import os
import pytest
from datetime import datetime, timedelta, timezone
from typing import Generator, Dict, Any
from uuid import uuid4

# SQLAlchemy imports
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session

# SQLModel imports
from sqlmodel import SQLModel, Session as SQLModelSession

# FastAPI/Starlette imports
from fastapi.testclient import TestClient
from starlette.testclient import TestClient as StarletteTestClient

# App imports
from run import app
from app.config import settings
from app.models import (
    User, RefreshToken, Case, Snapshot, Member, Event,
    Scenario, Delegation, AuditLog
)
from db import get_session
import services.auth_service as auth_service_module


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Use SQLite in-memory database for tests (fast and clean)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine (session-scoped for efficiency)"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=pool.StaticPool,  # Required for in-memory SQLite
        echo=False,  # Set to True for SQL debugging
    )
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup (in-memory database auto-clears)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[SQLModelSession, None, None]:
    """Create a new database session for each test (function-scoped)"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    
    session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
        class_=SQLModelSession
    )()
    
    yield session
    
    # Rollback after test (ensures test isolation)
    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# APP AND CLIENT FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def app_with_test_db(db_session: SQLModelSession):
    """Override the get_session dependency to use test database"""
    def override_get_session():
        return db_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    yield app
    
    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app_with_test_db) -> TestClient:
    """Create a test client connected to test database"""
    return TestClient(app_with_test_db)


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_user_data() -> Dict[str, Any]:
    """Standard test user data"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "test_password_123!",
        "role": "user",
        "is_active": True,
        "is_admin": False,
    }


@pytest.fixture(scope="function")
def admin_user_data() -> Dict[str, Any]:
    """Admin user data for testing"""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin_password_123!",
        "role": "admin",
        "is_active": True,
        "is_admin": True,
    }


@pytest.fixture(scope="function")
def test_user(db_session: SQLModelSession, test_user_data: Dict[str, Any]) -> User:
    """Create a test user in the database"""
    # Hash password using auth_service module
    password_hash = auth_service_module.hash_password(test_user_data["password"])
    
    user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        password_hash=password_hash,
        role=test_user_data["role"],
        is_active=test_user_data["is_active"],
        is_admin=test_user_data["is_admin"],
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def admin_user(db_session: SQLModelSession, admin_user_data: Dict[str, Any]) -> User:
    """Create an admin test user"""
    password_hash = auth_service_module.hash_password(admin_user_data["password"])
    
    user = User(
        username=admin_user_data["username"],
        email=admin_user_data["email"],
        password_hash=password_hash,
        role=admin_user_data["role"],
        is_active=admin_user_data["is_active"],
        is_admin=admin_user_data["is_admin"],
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def access_token(test_user: User) -> str:
    """Generate a valid JWT access token for test user"""
    # Create access token (use a longer expiry for tests)
    expiry_minutes = 1440  # 24 hours for testing
    token_dict = auth_service_module.create_access_token(
        user_id=test_user.id,  # type: ignore[arg-type]
        username=test_user.username,
        role=test_user.role,
        expires_delta=timedelta(minutes=expiry_minutes)
    )
    
    return token_dict["access_token"]


@pytest.fixture(scope="function")
def refresh_token(db_session: SQLModelSession, test_user: User) -> str:
    """Create a valid refresh token in the database"""
    token = f"refresh_{uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    refresh_token_obj = RefreshToken(
        user_id=test_user.id,  # type: ignore[arg-type]
        token=token,
        expires_at=expires_at,
        is_revoked=False,
    )
    
    db_session.add(refresh_token_obj)
    db_session.commit()
    
    return token


@pytest.fixture(scope="function")
def auth_headers(access_token: str) -> Dict[str, str]:
    """Authorization headers with Bearer token"""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="function")
def client_with_auth(client: TestClient, auth_headers: Dict[str, str]) -> TestClient:
    """TestClient with pre-configured authentication headers"""
    client.headers.update(auth_headers)
    return client


# ============================================================================
# TEST CASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_case(db_session: SQLModelSession, test_user: User) -> Case:
    """Create a test case (BaZi analysis case)"""
    # Case data for 2026-02-27 12:00:00 in Shanghai
    case = Case(
        id=str(uuid4()),
        name="Test Case",
        gender="male",
        birth_dt_local="2000-01-01T12:00:00",
        tz="Asia/Shanghai",
        birth_dt="2000-01-01T04:00:00Z",  # UTC equivalent
        city="Shanghai",
        lon=121.47,
        solar_time_enabled=False,
        notes="Test case for unit testing",
        tags="test,unit",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    
    return case


@pytest.fixture(scope="function")
def test_member(db_session: SQLModelSession, test_user: User) -> Member:
    """Create a test member (person in BaZi analysis)"""
    from datetime import date
    
    member = Member(
        owner_id=test_user.id,  # type: ignore[arg-type]
        name="Test Member",
        birth_date=date(2000, 1, 1),
        gender="M",
        birth_time_hour=12,
        birth_time_minute=0,
        birth_city="Shanghai",
        birth_longitude=121.47,
        solar_time_enabled=False,
        notes="Test member",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    
    return member


@pytest.fixture(scope="function")
def test_event(db_session: SQLModelSession, test_user: User, test_member: Member) -> Event:
    """Create a test event"""
    event = Event(
        owner_id=test_user.id,  # type: ignore[arg-type]
        member_id=test_member.id,  # type: ignore[arg-type]
        name="Test Event",
        event_type="marriage",
        bazi_json='{"test": "data"}',
        pillars_primary="60甲子",
        L_level=1,
        confidence_score=0.85,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    
    return event


# ============================================================================
# SNAPSHOT AND SCENARIO FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_snapshot(db_session: SQLModelSession, test_case: Case) -> Snapshot:
    """Create a test snapshot"""
    snapshot = Snapshot(
        id=str(uuid4()),
        case_id=test_case.id,
        kind="full",
        compute_flags={"flag1": True},
        input_json={"test": "input"},
        output_json={"test": "output"},
        api_version="1.0.0",
        rule_version="1.0.0",
        created_at=datetime.now(timezone.utc),
    )
    
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)
    
    return snapshot


@pytest.fixture(scope="function")
def test_scenario(db_session: SQLModelSession, test_user: User, test_member: Member) -> Scenario:
    """Create a test scenario"""
    scenario = Scenario(
        owner_id=test_user.id,  # type: ignore[arg-type]
        base_member_id=test_member.id,  # type: ignore[arg-type]  # type: ignore[arg-type]
        name="Test Scenario",
        description="Test scenario description",
        scenario_type="comparison",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    db_session.add(scenario)
    db_session.commit()
    db_session.refresh(scenario)
    
    return scenario


@pytest.fixture(scope="function")
def test_delegation(db_session: SQLModelSession, test_user: User, admin_user: User) -> Delegation:
    """Create a test delegation"""
    delegation = Delegation(
        from_user_id=test_user.id,  # type: ignore[arg-type]  # type: ignore[arg-type]
        to_user_id=admin_user.id,  # type: ignore[arg-type]  # type: ignore[arg-type]
        permission_type="read",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    
    db_session.add(delegation)
    db_session.commit()
    db_session.refresh(delegation)
    
    return delegation


# ============================================================================
# PYTEST CONFIGURATION HOOKS
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before running any tests"""
    # Set test database URL as environment variable
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    
    # Disable logging during tests (optional)
    import logging
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.WARNING)
    
    yield
    
    # Cleanup after all tests
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "benchmark: marks tests as performance benchmarks"
    )


@pytest.fixture(scope="function", autouse=True)
def reset_request_state(client: TestClient):
    """Reset client state between tests"""
    # Clear any session state
    client.cookies.clear()
    yield
    client.cookies.clear()


# ============================================================================
# PERFORMANCE TESTING UTILITIES
# ============================================================================

@pytest.fixture(scope="function")
def benchmark_timer():
    """Simple benchmark timer for performance testing"""
    import time
    
    class BenchmarkTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def __enter__(self):
            self.start_time = time.perf_counter()
            return self
        
        def __exit__(self, *args):
            self.end_time = time.perf_counter()
        
        @property
        def elapsed_ms(self) -> float:
            """Return elapsed time in milliseconds"""
            if self.start_time is None or self.end_time is None:
                return 0.0
            return (self.end_time - self.start_time) * 1000
    
    return BenchmarkTimer()


# ============================================================================
# BATCH OPERATION FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def bulk_test_users(db_session: SQLModelSession) -> list[User]:
    """Create multiple test users for bulk operation testing"""
    users = []
    
    for i in range(10):
        user = User(
            username=f"bulkuser{i}",
            email=f"bulk{i}@example.com",
            password_hash=auth_service_module.hash_password(f"password{i}"),
            role="user",
            is_active=True,
            is_admin=False,
        )
        users.append(user)
    
    db_session.add_all(users)
    db_session.commit()
    
    # Refresh all to get IDs
    for user in users:
        db_session.refresh(user)
    
    return users


@pytest.fixture(scope="function")
def bulk_test_cases(db_session: SQLModelSession, bulk_test_users: list[User]) -> list[Case]:
    """Create multiple test cases for bulk operation testing"""
    cases = []
    
    for i, user in enumerate(bulk_test_users[:5]):  # Create 5 cases
        case = Case(
            id=f"case_{uuid4().hex[:8]}",
            name=f"Bulk Case {i}",
            gender="M" if i % 2 == 0 else "F",
            birth_dt_local=f"2000-01-{(i % 28) + 1:02d}T12:00:00",
            tz="Asia/Shanghai",
            birth_dt=f"2000-01-{(i % 28) + 1:02d}T04:00:00Z",
            city="Shanghai",
            lon=121.47,
            solar_time_enabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        cases.append(case)
    
    db_session.add_all(cases)
    db_session.commit()
    
    # Refresh all to ensure proper state
    for case in cases:
        db_session.refresh(case)
    
    return cases
