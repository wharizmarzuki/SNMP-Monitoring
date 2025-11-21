"""
Integration tests for query endpoints
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.query
class TestQueryEndpoints:
    """Test query API endpoints"""

    def test_get_network_summary_empty(self, client):
        """Test network summary with no devices"""
        response = client.get("/query/network-summary")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_devices"] == 0
        assert data["devices_up"] == 0
        assert data["devices_down"] == 0

    def test_get_network_summary(self, client, sample_devices):
        """Test network summary with multiple devices"""
        response = client.get("/query/network-summary")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_devices"] == 5
        assert data["devices_up"] > 0
        assert data["devices_down"] >= 0
        assert data["total_devices"] == data["devices_up"] + data["devices_down"]

    def test_get_top_cpu_devices(self, client, sample_devices):
        """Test getting top CPU devices"""
        response = client.get("/query/top-devices?metric=cpu")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should return devices ordered by CPU usage
        for device in data:
            assert "hostname" in device
            assert "ip_address" in device
            assert "value" in device

    def test_get_top_memory_devices(self, client, sample_devices):
        """Test getting top memory devices"""
        response = client.get("/query/top-devices?metric=memory")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_device_metrics(self, client, sample_device, sample_metric):
        """Test getting device metrics"""
        response = client.get(f"/query/device/{sample_device.ip_address}/metrics")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            metric = data[0]
            assert "timestamp" in metric
            assert "cpu_utilization" in metric
            assert "memory_utilization" in metric

    def test_get_device_metrics_not_found(self, client):
        """Test getting metrics for non-existent device"""
        response = client.get("/query/device/192.168.99.99/metrics")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_interface_summary(self, client, sample_device, sample_interface):
        """Test getting interface summary for a device"""
        response = client.get(f"/query/device/{sample_device.ip_address}/interfaces/summary")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_interface_summary_not_found(self, client):
        """Test getting interface summary for non-existent device"""
        response = client.get("/query/device/192.168.99.99/interfaces/summary")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_active_alerts_empty(self, client):
        """Test getting active alerts when none exist"""
        response = client.get("/query/alerts/active")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_network_throughput(self, client):
        """Test getting network throughput"""
        response = client.get("/query/network-throughput")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_query_response_schemas(self, client, sample_devices):
        """Test that query responses match expected schemas"""
        # Test network summary schema
        response = client.get("/query/network-summary")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        required_fields = ["total_devices", "devices_up", "devices_down", "active_alerts"]
        for field in required_fields:
            assert field in data, f"Missing required field in network summary: {field}"
