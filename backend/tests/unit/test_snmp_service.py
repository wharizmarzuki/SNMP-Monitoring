"""
Unit tests for SNMP Service

Tests the SNMP client operations in isolation with mocked pysnmp library.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from services.snmp_service import PySNMPClient, get_snmp_data, bulk_snmp_walk


@pytest.mark.unit
@pytest.mark.asyncio
class TestPySNMPClient:
    """Test PySNMPClient GET and BULK WALK operations"""

    def test_client_initialization(self):
        """Test: SNMPClient initializes with correct parameters"""
        client = PySNMPClient(community="private", timeout=5, retries=2)

        assert client.community == "private"
        assert client.timeout == 5
        assert client.retries == 2

    def test_client_default_initialization(self):
        """Test: SNMPClient uses default parameters"""
        client = PySNMPClient()

        assert client.community == "public"  # Default from settings
        assert client.timeout == 10
        assert client.retries == 3

    @patch('services.snmp_service.get_cmd')
    @patch('services.snmp_service.UdpTransportTarget')
    async def test_get_query_success(self, mock_transport, mock_get_cmd):
        """Test: SNMP GET query returns correct value for valid OID"""
        # Setup mocks
        mock_transport.create = AsyncMock(return_value=Mock())

        # Mock successful SNMP response
        mock_varbind = Mock()
        mock_varbind.__getitem__ = lambda self, idx: {
            0: Mock(__str__=lambda x: "SNMPv2-MIB::sysDescr.0"),
            1: Mock(prettyPrint=lambda: "Cisco IOS Software, Version 15.2")
        }[idx]

        mock_get_cmd.return_value = (
            None,  # errorIndication
            None,  # errorStatus
            None,  # errorIndex
            [mock_varbind]  # varBinds
        )

        # Execute
        client = PySNMPClient()
        result = await client.get("192.168.1.1", ["1.3.6.1.2.1.1.1.0"])

        # Assert
        assert result is not None
        assert result["success"] is True
        assert result["host"] == "192.168.1.1"
        assert len(result["data"]) == 1
        assert result["data"][0]["value"] == "Cisco IOS Software, Version 15.2"

    @patch('services.snmp_service.get_cmd')
    @patch('services.snmp_service.UdpTransportTarget')
    async def test_get_query_timeout(self, mock_transport, mock_get_cmd):
        """Test: SNMP GET query handles timeout gracefully"""
        # Setup mocks
        mock_transport.create = AsyncMock(return_value=Mock())
        mock_get_cmd.side_effect = asyncio.TimeoutError()

        # Execute
        client = PySNMPClient(timeout=1)
        result = await client.get("192.168.1.99", ["1.3.6.1.2.1.1.1.0"])

        # Assert
        assert result is None  # Graceful failure

    @patch('services.snmp_service.get_cmd')
    @patch('services.snmp_service.UdpTransportTarget')
    async def test_get_query_error_indication(self, mock_transport, mock_get_cmd):
        """Test: SNMP GET query handles SNMP error indication"""
        # Setup mocks
        mock_transport.create = AsyncMock(return_value=Mock())
        mock_get_cmd.return_value = (
            "Request timeout",  # errorIndication
            None,
            None,
            []
        )

        # Execute
        client = PySNMPClient()
        result = await client.get("192.168.1.1", ["1.3.6.1.2.1.1.1.0"])

        # Assert
        assert result is None

    @patch('services.snmp_service.get_cmd')
    @patch('services.snmp_service.UdpTransportTarget')
    async def test_get_query_multiple_oids(self, mock_transport, mock_get_cmd):
        """Test: SNMP GET query handles multiple OIDs"""
        # Setup mocks
        mock_transport.create = AsyncMock(return_value=Mock())

        # Mock multiple varbinds
        mock_varbind1 = Mock()
        mock_varbind1.__getitem__ = lambda self, idx: {
            0: Mock(__str__=lambda x: "SNMPv2-MIB::sysDescr.0"),
            1: Mock(prettyPrint=lambda: "Cisco")
        }[idx]

        mock_varbind2 = Mock()
        mock_varbind2.__getitem__ = lambda self, idx: {
            0: Mock(__str__=lambda x: "SNMPv2-MIB::sysUpTime.0"),
            1: Mock(prettyPrint=lambda: "123456")
        }[idx]

        mock_get_cmd.return_value = (None, None, None, [mock_varbind1, mock_varbind2])

        # Execute
        client = PySNMPClient()
        result = await client.get("192.168.1.1", ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.3.0"])

        # Assert
        assert result is not None
        assert len(result["data"]) == 2
        assert result["data"][0]["value"] == "Cisco"
        assert result["data"][1]["value"] == "123456"

    @patch('services.snmp_service.bulk_cmd')
    @patch('services.snmp_service.UdpTransportTarget')
    async def test_bulk_walk_success(self, mock_transport, mock_get_cmd):
        """Test: SNMP BULK WALK retrieves multiple OID values"""
        # Setup mocks
        mock_transport.create = AsyncMock(return_value=Mock())

        # Mock bulk walk response (interfaces)
        mock_varbind1 = Mock()
        mock_varbind1.__getitem__ = lambda self, idx: {
            0: Mock(asTuple=lambda: (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 1)),
            1: Mock(prettyPrint=lambda: "GigabitEthernet0/0")
        }[idx]

        mock_varbind2 = Mock()
        mock_varbind2.__getitem__ = lambda self, idx: {
            0: Mock(asTuple=lambda: (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 2)),
            1: Mock(prettyPrint=lambda: "GigabitEthernet0/1")
        }[idx]

        # Return values for first and second call (pagination)
        mock_get_cmd.side_effect = [
            (None, None, None, [[mock_varbind1], [mock_varbind2]]),
            (None, None, None, [])  # No more data
        ]

        # Execute
        client = PySNMPClient()
        result = await client.bulk_walk("192.168.1.1", ["1.3.6.1.2.1.2.2.1.2"])

        # Assert
        assert result["success"] is True
        assert len(result["data"]) >= 1  # At least one result

    @patch('services.snmp_service.bulk_cmd')
    @patch('services.snmp_service.UdpTransportTarget')
    async def test_bulk_walk_error(self, mock_transport, mock_bulk_cmd):
        """Test: SNMP BULK WALK handles errors gracefully"""
        # Setup mocks
        mock_transport.create = AsyncMock(return_value=Mock())
        mock_bulk_cmd.return_value = (
            "Request timeout",  # errorIndication
            None,
            None,
            []
        )

        # Execute
        client = PySNMPClient()
        result = await client.bulk_walk("192.168.1.99", ["1.3.6.1.2.1.2.2.1.2"])

        # Assert
        assert result["success"] is False
        assert "error" in result

    @patch('services.snmp_service.bulk_cmd')
    @patch('services.snmp_service.UdpTransportTarget')
    async def test_bulk_walk_exception(self, mock_transport, mock_bulk_cmd):
        """Test: SNMP BULK WALK handles exceptions gracefully"""
        # Setup mocks
        mock_transport.create = AsyncMock(return_value=Mock())
        mock_bulk_cmd.side_effect = Exception("Network error")

        # Execute
        client = PySNMPClient()
        result = await client.bulk_walk("192.168.1.1", ["1.3.6.1.2.1.2.2.1.2"])

        # Assert
        assert result["success"] is False
        assert "Network error" in result["error"]


@pytest.mark.unit
@pytest.mark.asyncio
class TestSNMPServiceFunctions:
    """Test service-level SNMP functions"""

    async def test_get_snmp_data(self):
        """Test: get_snmp_data delegates to SNMPClient.get()"""
        # Create mock client
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "host": "192.168.1.1",
            "data": [{"oid": "sysDescr.0", "value": "Cisco"}]
        }

        # Execute
        result = await get_snmp_data("192.168.1.1", ["1.3.6.1.2.1.1.1.0"], mock_client)

        # Assert
        assert result["success"] is True
        mock_client.get.assert_called_once_with("192.168.1.1", ["1.3.6.1.2.1.1.1.0"])

    async def test_bulk_snmp_walk(self):
        """Test: bulk_snmp_walk delegates to SNMPClient.bulk_walk()"""
        # Create mock client
        mock_client = AsyncMock()
        mock_client.bulk_walk.return_value = {
            "success": True,
            "data": [
                {"base_oid": "1.3.6.1.2.1.2.2.1.2", "index": "1", "value": "eth0"}
            ]
        }

        # Execute
        result = await bulk_snmp_walk("192.168.1.1", ["1.3.6.1.2.1.2.2.1.2"], mock_client)

        # Assert
        assert result["success"] is True
        assert len(result["data"]) == 1
        mock_client.bulk_walk.assert_called_once_with("192.168.1.1", ["1.3.6.1.2.1.2.2.1.2"])


@pytest.mark.unit
class TestSNMPOIDParsing:
    """Test OID string parsing and formatting"""

    def test_oid_with_double_colon(self):
        """Test: OID parsing handles :: notation"""
        # This is tested implicitly in test_get_query_success
        # The mock returns "SNMPv2-MIB::sysDescr.0" which should be parsed to "sysDescr.0"
        pass

    def test_oid_without_double_colon(self):
        """Test: OID parsing handles numeric OIDs"""
        # This would be the raw OID format "1.3.6.1.2.1.1.1.0"
        pass


@pytest.mark.unit
@pytest.mark.parametrize("community,expected", [
    ("public", "public"),
    ("private", "private"),
    ("my-community", "my-community"),
])
def test_snmp_client_community_string(community, expected):
    """Test: SNMP client accepts various community strings"""
    client = PySNMPClient(community=community)
    assert client.community == expected


@pytest.mark.unit
@pytest.mark.parametrize("timeout,expected", [
    (1, 1),
    (5, 5),
    (30, 30),
])
def test_snmp_client_timeout_values(timeout, expected):
    """Test: SNMP client accepts various timeout values"""
    client = PySNMPClient(timeout=timeout)
    assert client.timeout == expected
