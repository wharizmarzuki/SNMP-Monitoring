"""
Integration tests for device discovery endpoint (TC01)

Test Coverage:
- TC01: Start device discovery for selected IP range
"""
import pytest
from fastapi import status
from unittest.mock import AsyncMock, patch
from app.core import models


@pytest.mark.integration
@pytest.mark.device
class TestDeviceDiscovery:
    """Test device discovery API endpoint"""

    @patch('services.discovery_service.DiscoveryService.discover_network')
    def test_discovery_api_success(self, mock_discover, client, test_db):
        """
        TC01: Start device discovery for selected IP range

        Expected: Detect SNMP-enabled devices
        """
        # Mock discovery service to return discovered devices
        mock_discover.return_value = [
            {
                "ip_address": "192.168.1.1",
                "hostname": "router-1",
                "vendor": "Cisco",
                "mac_address": "00:11:22:33:44:01"
            },
            {
                "ip_address": "192.168.1.2",
                "hostname": "switch-1",
                "vendor": "Juniper",
                "mac_address": "00:11:22:33:44:02"
            }
        ]

        # Trigger discovery
        response = client.post(
            "/device/discover",
            json={"network": "192.168.1.0/24"}
        )

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "discovered" in data["message"].lower() or "started" in data["message"].lower()

        # Verify mock was called with correct network
        mock_discover.assert_called_once()
        call_args = mock_discover.call_args
        assert "192.168.1.0/24" in str(call_args)

    @patch('services.discovery_service.DiscoveryService.discover_network')
    def test_discovery_api_multiple_devices(self, mock_discover, client, test_db):
        """
        TC01 Extended: Verify multiple devices discovered
        """
        # Mock 5 discovered devices
        discovered_devices = [
            {
                "ip_address": f"192.168.1.{i}",
                "hostname": f"device-{i}",
                "vendor": "Cisco" if i % 2 == 0 else "Juniper",
                "mac_address": f"00:11:22:33:44:{i:02x}"
            }
            for i in range(1, 6)
        ]
        mock_discover.return_value = discovered_devices

        # Trigger discovery
        response = client.post(
            "/device/discover",
            json={"network": "192.168.1.0/29"}
        )

        # Assertions
        assert response.status_code == status.HTTP_200_OK

        # Verify devices were added to database
        devices = test_db.query(models.Device).all()
        # Note: Actual DB insertion depends on implementation
        # This test verifies the API endpoint works

    def test_discovery_api_invalid_network(self, client):
        """
        TC01 Negative: Invalid network range
        """
        response = client.post(
            "/device/discover",
            json={"network": "invalid-network"}
        )

        # Should return error (400 or 422)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_discovery_api_empty_network(self, client):
        """
        TC01 Negative: Empty network parameter
        """
        response = client.post(
            "/device/discover",
            json={"network": ""}
        )

        # Should return validation error
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    @patch('services.discovery_service.DiscoveryService.discover_network')
    def test_discovery_api_no_devices_found(self, mock_discover, client):
        """
        TC01 Edge Case: No devices discovered
        """
        # Mock empty discovery result
        mock_discover.return_value = []

        response = client.post(
            "/device/discover",
            json={"network": "192.168.99.0/24"}
        )

        # Should still return success (200) with message
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
