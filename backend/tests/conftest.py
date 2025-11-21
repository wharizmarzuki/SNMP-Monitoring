"""
Pytest configuration and fixtures for SNMP Monitoring System tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core import models
from main import app

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal()

    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with test database dependency override"""
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

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
        if_descr="WAN Interface",
        if_type=6,
        if_mtu=1500,
        if_speed=1000000000,
        if_phys_address="00:11:22:33:44:66"
    )
    test_db.add(interface)
    test_db.commit()
    test_db.refresh(interface)
    return interface
