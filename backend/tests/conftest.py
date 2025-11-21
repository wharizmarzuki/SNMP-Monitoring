"""
Pytest configuration and fixtures for SNMP Monitoring System

Test Types:
- API Integration Tests: Test endpoints through HTTP (most tests)
- Auth Tests: Test authentication flow (minimal scope)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core import models
from app.core.security import get_current_user, get_password_hash
from main import app

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"


# =============================================================================
# Safety Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """
    CRITICAL: Clear dependency overrides after each test to prevent leakage.

    Without this, failed tests can leave overrides active, causing:
    - False positives in subsequent tests
    - Hard-to-debug test interactions
    - Flaky test behavior

    This fixture runs automatically for ALL tests.
    """
    yield
    app.dependency_overrides.clear()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh test database for each test.

    Uses in-memory SQLite for speed. Database is destroyed after test.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# =============================================================================
# API Client Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def client(test_db):
    """
    API test client with authentication BYPASSED.

    Use for: Business logic tests (thresholds, queries, data validation)
    Don't use for: Authentication/authorization tests

    Auth is mocked to return admin user automatically.
    """
    from app.core.cache import cache

    def mock_current_user():
        return {"username": "testuser", "admin": True}

    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_current_user] = mock_current_user

    # Clear cache before each test to prevent cross-test contamination
    cache.clear_all()

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Safety: Clear even if test fails
        app.dependency_overrides.clear()
        test_db.rollback()
        cache.clear_all()  # Clear cache after test too


@pytest.fixture(scope="function")
def client_no_auth(test_db):
    """
    API test client with REAL authentication (no bypass).

    Use for: Authentication and authorization tests
    Don't use for: Business logic tests (use `client` instead)

    Requires valid JWT token in Authorization header.
    """
    app.dependency_overrides[get_db] = lambda: test_db
    # NO auth override - real auth required

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        test_db.rollback()


# =============================================================================
# Auth Fixtures
# =============================================================================

@pytest.fixture
def test_user(test_db):
    """
    Create a test user with known credentials.

    Credentials:
        username: testuser
        password: testpass (plain text - will be hashed)
        email: test@example.com
        admin: True
    """
    user = models.User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass"),
        is_active=True,
        is_admin=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client_no_auth, test_user):
    """
    Returns authorization headers with valid JWT token.

    Use this instead of manually logging in for each test.

    Example:
        def test_protected_endpoint(self, client_no_auth, auth_headers):
            response = client_no_auth.get("/device/", headers=auth_headers)
            assert response.status_code == 200
    """
    response = client_no_auth.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200, "Login failed in auth_headers fixture"

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Data Fixtures
# =============================================================================

@pytest.fixture
def sample_device(test_db):
    """Create a sample device for testing"""
    device = models.Device(
        ip_address="192.168.1.100",
        hostname="test-device",
        vendor="Cisco",
        mac_address="00:11:22:33:44:55",
        is_reachable=True,
        cpu_threshold=80.0,
        memory_threshold=85.0,
        failure_threshold=3,
        cpu_alert_state="clear",
        memory_alert_state="clear",
        reachability_alert_state="clear"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    return device


@pytest.fixture
def sample_devices(test_db):
    """Create multiple sample devices for testing"""
    devices = [
        models.Device(
            ip_address=f"192.168.1.{i}",
            hostname=f"device-{i}",
            vendor="Cisco" if i % 2 == 0 else "Juniper",
            mac_address=f"00:11:22:33:44:{i:02x}",
            is_reachable=True if i % 3 != 0 else False,
            cpu_threshold=80.0,
            memory_threshold=85.0,
            failure_threshold=3,
            cpu_alert_state="clear",
            memory_alert_state="clear",
            reachability_alert_state="clear"
        )
        for i in range(1, 6)
    ]
    for device in devices:
        test_db.add(device)
    test_db.commit()
    return devices


@pytest.fixture
def device_with_cpu_alert(test_db, sample_device):
    """Create a device with CPU alert in triggered state"""
    sample_device.cpu_alert_state = "triggered"
    test_db.commit()
    test_db.refresh(sample_device)
    return sample_device


@pytest.fixture
def device_with_memory_alert(test_db, sample_device):
    """Create a device with memory alert in triggered state"""
    sample_device.memory_alert_state = "triggered"
    test_db.commit()
    test_db.refresh(sample_device)
    return sample_device


@pytest.fixture
def device_with_reachability_alert(test_db, sample_device):
    """Create a device with reachability alert in triggered state"""
    sample_device.reachability_alert_state = "triggered"
    test_db.commit()
    test_db.refresh(sample_device)
    return sample_device


@pytest.fixture
def sample_recipient(test_db):
    """Create a sample alert recipient for testing"""
    recipient = models.AlertRecipient(email="test@example.com")
    test_db.add(recipient)
    test_db.commit()
    test_db.refresh(recipient)
    return recipient


@pytest.fixture
def sample_metric(test_db, sample_device):
    """Create a sample device metric for testing"""
    metric = models.DeviceMetric(
        device_id=sample_device.id,
        cpu_utilization=45.5,
        memory_utilization=62.3,
        uptime_seconds=86400
    )
    test_db.add(metric)
    test_db.commit()
    test_db.refresh(metric)
    return metric


@pytest.fixture
def sample_interface(test_db, sample_device):
    """Create a sample interface for testing"""
    interface = models.Interface(
        device_id=sample_device.id,
        if_index=1,
        if_name="GigabitEthernet0/0",
        packet_drop_threshold=0.1
    )
    test_db.add(interface)
    test_db.commit()
    test_db.refresh(interface)
    return interface


@pytest.fixture
def interface_with_status_alert(test_db, sample_interface):
    """Create an interface with status alert in triggered state"""
    sample_interface.oper_status_alert_state = "triggered"
    test_db.commit()
    test_db.refresh(sample_interface)
    return sample_interface
