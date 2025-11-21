"""
Integration tests for device endpoints
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.device
class TestDeviceEndpoints:
    """Test device API endpoints"""

    def test_get_all_devices_empty(self, client):
        """Test getting all devices when database is empty"""
        response = client.get("/device/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_all_devices(self, client, sample_devices):
        """Test getting all devices"""
        response = client.get("/device/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5
        assert all("ip_address" in device for device in data)
        assert all("hostname" in device for device in data)

    def test_get_device_by_ip(self, client, sample_device):
        """Test getting a specific device by IP"""
        response = client.get(f"/device/{sample_device.ip_address}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["ip_address"] == sample_device.ip_address
        assert data["hostname"] == sample_device.hostname
        assert data["vendor"] == sample_device.vendor

    def test_get_device_not_found(self, client):
        """Test getting a non-existent device"""
        response = client.get("/device/192.168.99.99")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_device_thresholds(self, client, sample_device):
        """Test updating device thresholds in batch"""
        new_thresholds = {
            "cpu_threshold": 75.0,
            "memory_threshold": 90.0,
            "failure_threshold": 5
        }
        response = client.put(
            f"/device/{sample_device.ip_address}/thresholds",
            json=new_thresholds
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cpu_threshold"] == 75.0
        assert data["memory_threshold"] == 90.0
        assert data["failure_threshold"] == 5

    def test_update_device_thresholds_partial(self, client, sample_device):
        """Test updating only some thresholds"""
        response = client.put(
            f"/device/{sample_device.ip_address}/thresholds",
            json={"cpu_threshold": 70.0}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cpu_threshold"] == 70.0
        # Other thresholds should remain unchanged
        assert data["memory_threshold"] == sample_device.memory_threshold

    def test_update_thresholds_invalid_device(self, client):
        """Test updating thresholds for non-existent device"""
        response = client.put(
            "/device/192.168.99.99/thresholds",
            json={"cpu_threshold": 75.0}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_interface_threshold(self, client, sample_device, sample_interface):
        """Test updating interface threshold"""
        response = client.put(
            f"/device/{sample_device.ip_address}/interface/{sample_interface.if_index}/threshold",
            json={"threshold_value": 1000}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data

    def test_acknowledge_device_alert(self, client, sample_device):
        """Test acknowledging a device alert"""
        response = client.put(
            f"/device/{sample_device.ip_address}/alert/cpu/acknowledge"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "acknowledged"
        assert "acknowledged_at" in data

    def test_resolve_device_alert(self, client, sample_device):
        """Test resolving a device alert"""
        # First acknowledge
        client.put(f"/device/{sample_device.ip_address}/alert/cpu/acknowledge")

        # Then resolve
        response = client.put(
            f"/device/{sample_device.ip_address}/alert/cpu/resolve"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "clear"

    def test_device_response_schema(self, client, sample_device):
        """Test that device response matches expected schema"""
        response = client.get(f"/device/{sample_device.ip_address}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify all required fields are present
        required_fields = [
            "id", "ip_address", "hostname", "vendor", "is_reachable",
            "cpu_threshold", "memory_threshold", "failure_threshold",
            "cpu_alert_state", "memory_alert_state", "reachability_alert_state",
            "maintenance_mode"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
