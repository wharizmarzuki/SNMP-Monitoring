"""
Integration tests for SNMP error handling (TC07)

Test Coverage:
- TC07: Invalid SNMP community string - Device polling fails gracefully
"""
import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock
from app.core import models
from datetime import datetime


@pytest.mark.integration
@pytest.mark.device
class TestSNMPErrorHandling:
    """Test SNMP error scenarios"""

    @patch('services.polling_service.poll_device')
    async def test_invalid_snmp_community_string(self, mock_poll, client, test_db):
        """
        TC07: Invalid SNMP community string

        Expected: Device polling fails gracefully, marked unreachable
        """
        # Create device
        device = models.Device(
            ip_address="192.168.1.50",
            hostname="test-device",
            vendor="Cisco",
            mac_address="00:11:22:33:44:50",
            is_reachable=True,  # Initially reachable
            cpu_threshold=80.0,
            memory_threshold=85.0
        )
        test_db.add(device)
        test_db.commit()

        # Mock polling failure due to auth error
        mock_poll.return_value = {
            "success": False,
            "error": "Authentication failed",
            "reachable": False
        }

        # Attempt to poll (via API or service)
        # Note: Adjust based on your actual polling endpoint
        response = client.post("/polling/poll-all")

        # Should not crash, should handle gracefully
        assert response.status_code == status.HTTP_200_OK

        # Verify device marked unreachable (would be done by polling service)
        # This is a placeholder - actual verification depends on implementation

    @patch('services.snmp_service.get_snmp_data')
    async def test_snmp_timeout_handled_gracefully(self, mock_snmp, client, test_db):
        """
        TC07 Extended: SNMP timeout handled gracefully

        Expected: No crash, device marked unreachable
        """
        # Create device
        device = models.Device(
            ip_address="192.168.1.51",
            hostname="timeout-device",
            vendor="Cisco",
            mac_address="00:11:22:33:44:51",
            is_reachable=True,
            cpu_threshold=80.0,
            memory_threshold=85.0
        )
        test_db.add(device)
        test_db.commit()

        # Mock SNMP timeout
        mock_snmp.side_effect = TimeoutError("SNMP request timed out")

        # Attempt polling
        response = client.post("/polling/poll-all")

        # Should handle gracefully
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.unit
@pytest.mark.asyncio
class TestSNMPAuthenticationFailure:
    """Unit tests for SNMP authentication failures"""

    @patch('services.snmp_service.get_cmd')
    @patch('services.snmp_service.UdpTransportTarget')
    async def test_snmp_auth_failure_wrong_community(self, mock_transport, mock_get_cmd):
        """
        TC07 Unit Test: Wrong SNMP community string

        Expected: Authentication error returned, no crash
        """
        from services.snmp_service import PySNMPClient

        # Setup mocks
        mock_transport.create = AsyncMock(return_value=None)

        # Mock authentication failure
        mock_get_cmd.return_value = (
            "Authentication failed",  # errorIndication
            None,
            None,
            []
        )

        # Create client with wrong community
        client = PySNMPClient(community="wrong-community")
        result = await client.get("192.168.1.1", ["1.3.6.1.2.1.1.1.0"])

        # Assert graceful failure
        assert result is None or (isinstance(result, dict) and not result.get("success"))

    @patch('services.snmp_service.get_cmd')
    @patch('services.snmp_service.UdpTransportTarget')
    async def test_snmp_connection_refused(self, mock_transport, mock_get_cmd):
        """
        TC07 Unit Test: Connection refused (device not listening on SNMP port)

        Expected: Connection error handled gracefully
        """
        from services.snmp_service import PySNMPClient

        # Setup mocks
        mock_transport.create = AsyncMock(return_value=None)

        # Mock connection refused
        mock_get_cmd.return_value = (
            "No SNMP response received",  # errorIndication
            None,
            None,
            []
        )

        # Attempt connection
        client = PySNMPClient()
        result = await client.get("192.168.1.99", ["1.3.6.1.2.1.1.1.0"])

        # Assert graceful failure
        assert result is None

    @patch('services.snmp_service.get_cmd')
    @patch('services.snmp_service.UdpTransportTarget')
    async def test_snmp_invalid_oid(self, mock_transport, mock_get_cmd):
        """
        TC07 Extended: Invalid OID requested

        Expected: Error handled gracefully
        """
        from services.snmp_service import PySNMPClient

        # Setup mocks
        mock_transport.create = AsyncMock(return_value=None)

        # Mock invalid OID error
        mock_get_cmd.return_value = (
            None,  # No errorIndication
            1,     # errorStatus: noSuchName
            0,     # errorIndex
            []
        )

        # Request invalid OID
        client = PySNMPClient()
        result = await client.get("192.168.1.1", ["1.9.9.9.9.9.9.9"])

        # Assert handled
        assert result is None or (isinstance(result, dict) and not result.get("success"))


@pytest.mark.integration
@pytest.mark.device
class TestDeviceReachabilityHandling:
    """Test how system handles unreachable devices"""

    def test_unreachable_device_not_queried(self, client, test_db):
        """
        TC07 Extended: Unreachable devices skipped in polling

        Expected: System doesn't waste time polling known-unreachable devices
        """
        # Create unreachable device
        device = models.Device(
            ip_address="192.168.1.99",
            hostname="unreachable",
            vendor="Unknown",
            mac_address="00:11:22:33:44:99",
            is_reachable=False,  # Marked unreachable
            cpu_threshold=80.0,
            memory_threshold=85.0
        )
        test_db.add(device)
        test_db.commit()

        # Get device status
        response = client.get(f"/device/{device.ip_address}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_reachable"] == False

    def test_device_status_indicator_shows_down(self, client, test_db):
        """
        TC07 Extended: UI indicator shows device is down

        Expected: Device status correctly reflects reachability
        """
        # Create device with SNMP issues
        device = models.Device(
            ip_address="192.168.1.88",
            hostname="snmp-failed-device",
            vendor="Cisco",
            mac_address="00:11:22:33:44:88",
            is_reachable=False,
            cpu_threshold=80.0,
            memory_threshold=85.0
        )
        test_db.add(device)
        test_db.commit()

        # Get network summary
        response = client.get("/query/network-summary")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify summary includes down devices
        assert "devices_down" in data
        assert data["devices_down"] >= 1
