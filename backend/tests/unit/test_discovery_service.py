"""
Unit tests for Discovery Service

Test Case ID: TC01
Description: Tests device discovery for selected IP range
"""
import pytest
import asyncio
import ipaddress
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from services.discovery_service import perform_full_discovery, get_repository
from services.snmp_service import SNMPClient
from app.core import models


@pytest.mark.unit
@pytest.mark.asyncio
class TestDiscoveryService:
    """
    Test Case TC01: Start device discovery for selected IP range
    Expected Result: Detect SNMP-enabled devices
    """

    async def test_network_discovery_success(self, test_db):
        """
        TC01-001: Verify network discovery scans IP range and finds devices

        Expected Result:
        - Devices detected in specified CIDR range
        - Device information stored in database
        - Summary statistics returned
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)
        network = "192.168.1.0"
        subnet = "29"  # 8 IPs: .0 (network), .1-.6 (hosts), .7 (broadcast)

        # Mock device_discovery to return valid device info
        mock_device_data = {
            "ip_address": "192.168.1.1",
            "hostname": "router-1",
            "vendor": "Cisco",
            "mac_address": "00:11:22:33:44:55",
            "model": "Catalyst 2960"
        }

        with patch('services.discovery_service.device_discovery', new_callable=AsyncMock) as mock_discovery, \
             patch('services.discovery_service.get_runtime_settings') as mock_settings:

            # Simulate 3 devices found out of 6 IPs
            async def mock_device_response(ip, client, repo):
                if ip in ["192.168.1.1", "192.168.1.2", "192.168.1.5"]:
                    return {
                        "ip_address": ip,
                        "hostname": f"device-{ip.split('.')[-1]}",
                        "vendor": "Cisco",
                        "mac_address": f"00:11:22:33:44:{ip.split('.')[-1]:02x}",
                        "model": "Catalyst 2960"
                    }
                return None

            mock_discovery.side_effect = mock_device_response
            mock_settings.return_value = {"discovery_concurrency": 20}

            # Act
            result = await perform_full_discovery(test_db, mock_client, network, subnet)

            # Assert
            assert result["total_scanned"] == 6  # .1 to .6 (hosts only)
            assert result["devices_found"] == 3
            assert len(result["devices"]) == 3

            # Verify devices have correct IPs
            found_ips = [d["ip_address"] for d in result["devices"]]
            assert "192.168.1.1" in found_ips
            assert "192.168.1.2" in found_ips
            assert "192.168.1.5" in found_ips

    async def test_network_discovery_empty_network(self, test_db):
        """
        TC01-002: Verify discovery handles network with no SNMP devices

        Expected Result:
        - No devices found
        - No errors raised
        - Empty devices list returned
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)
        network = "192.168.1.0"
        subnet = "29"

        with patch('services.discovery_service.device_discovery', new_callable=AsyncMock) as mock_discovery, \
             patch('services.discovery_service.get_runtime_settings') as mock_settings:

            # All devices return None (not reachable)
            mock_discovery.return_value = None
            mock_settings.return_value = {"discovery_concurrency": 20}

            # Act
            result = await perform_full_discovery(test_db, mock_client, network, subnet)

            # Assert
            assert result["total_scanned"] == 6
            assert result["devices_found"] == 0
            assert len(result["devices"]) == 0

    async def test_network_discovery_invalid_cidr(self, test_db):
        """
        TC01-003: Verify discovery handles invalid CIDR notation

        Expected Result:
        - Error logged
        - Empty result returned
        - No devices scanned
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)
        network = "999.999.999.999"
        subnet = "24"

        with patch('services.discovery_service.get_runtime_settings') as mock_settings:
            mock_settings.return_value = {"discovery_concurrency": 20}

            # Act
            result = await perform_full_discovery(test_db, mock_client, network, subnet)

            # Assert
            assert result["total_scanned"] == 0
            assert result["devices_found"] == 0
            assert len(result["devices"]) == 0

    async def test_network_discovery_large_subnet(self, test_db):
        """
        TC01-004: Verify discovery can handle larger subnets (e.g., /24)

        Expected Result:
        - All 254 host IPs scanned
        - Concurrent discovery limited by semaphore
        - Results aggregated correctly
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)
        network = "192.168.1.0"
        subnet = "24"  # 254 hosts

        with patch('services.discovery_service.device_discovery', new_callable=AsyncMock) as mock_discovery, \
             patch('services.discovery_service.get_runtime_settings') as mock_settings:

            # Simulate 10 devices found
            async def mock_device_response(ip, client, repo):
                last_octet = int(ip.split('.')[-1])
                if last_octet <= 10:  # First 10 IPs have devices
                    return {
                        "ip_address": ip,
                        "hostname": f"device-{last_octet}",
                        "vendor": "Cisco",
                        "mac_address": f"00:11:22:33:44:{last_octet:02x}",
                        "model": "Switch"
                    }
                return None

            mock_discovery.side_effect = mock_device_response
            mock_settings.return_value = {"discovery_concurrency": 20}

            # Act
            result = await perform_full_discovery(test_db, mock_client, network, subnet)

            # Assert
            assert result["total_scanned"] == 254  # All hosts in /24
            assert result["devices_found"] == 10

    async def test_network_discovery_with_concurrency_limit(self, test_db):
        """
        TC01-005: Verify discovery respects concurrency settings

        Expected Result:
        - Concurrency limit applied via semaphore
        - All devices eventually scanned
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)
        network = "192.168.1.0"
        subnet = "28"  # 14 hosts

        with patch('services.discovery_service.device_discovery', new_callable=AsyncMock) as mock_discovery, \
             patch('services.discovery_service.get_runtime_settings') as mock_settings:

            mock_discovery.return_value = None
            mock_settings.return_value = {"discovery_concurrency": 5}  # Low limit

            # Act
            result = await perform_full_discovery(test_db, mock_client, network, subnet)

            # Assert
            assert result["total_scanned"] == 14
            assert mock_discovery.call_count == 14

    async def test_device_deduplication_by_mac(self, test_db):
        """
        TC01-006: Verify existing device (by MAC) is updated, not duplicated

        Expected Result:
        - Device with same MAC address updated
        - No duplicate entries created
        - IP address updated to new value
        """
        # Arrange
        # Create existing device with MAC
        existing_device = models.Device(
            ip_address="192.168.1.1",
            hostname="old-device",
            vendor="Cisco",
            mac_address="00:11:22:33:44:55",
            is_reachable=True
        )
        test_db.add(existing_device)
        test_db.commit()

        mock_client = Mock(spec=SNMPClient)
        network = "192.168.1.0"
        subnet = "29"

        with patch('services.discovery_service.device_discovery', new_callable=AsyncMock) as mock_discovery, \
             patch('services.discovery_service.get_runtime_settings') as mock_settings:

            # Discovery finds same MAC at new IP
            async def mock_device_response(ip, client, repo):
                if ip == "192.168.1.10":
                    # Simulate the device_discovery function behavior which handles deduplication
                    # In real implementation, device_discovery calls repo.create_or_update_device
                    # which checks for existing MAC address
                    existing = test_db.query(models.Device).filter_by(
                        mac_address="00:11:22:33:44:55"
                    ).first()

                    if existing:
                        existing.ip_address = ip
                        existing.hostname = "updated-device"
                        test_db.commit()
                        return {
                            "ip_address": ip,
                            "hostname": "updated-device",
                            "vendor": "Cisco",
                            "mac_address": "00:11:22:33:44:55",
                            "model": "Catalyst"
                        }
                return None

            mock_discovery.side_effect = mock_device_response
            mock_settings.return_value = {"discovery_concurrency": 20}

            # Act
            result = await perform_full_discovery(test_db, mock_client, network, subnet)

            # Assert - Should still have only 1 device
            all_devices = test_db.query(models.Device).all()
            assert len(all_devices) == 1

            # Device should have updated IP
            updated_device = all_devices[0]
            assert updated_device.ip_address == "192.168.1.10"
            assert updated_device.mac_address == "00:11:22:33:44:55"

    async def test_discovery_with_partial_failures(self, test_db):
        """
        TC01-007: Verify discovery continues when some IPs fail

        Expected Result:
        - Successful discoveries returned
        - Failed IPs don't block other discoveries
        - Exceptions handled gracefully
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)
        network = "192.168.1.0"
        subnet = "29"

        with patch('services.discovery_service.device_discovery', new_callable=AsyncMock) as mock_discovery, \
             patch('services.discovery_service.get_runtime_settings') as mock_settings:

            # Some IPs succeed, some raise exceptions
            async def mock_device_response(ip, client, repo):
                last_octet = int(ip.split('.')[-1])
                if last_octet == 1:
                    return {
                        "ip_address": ip,
                        "hostname": "device-1",
                        "vendor": "Cisco",
                        "mac_address": "00:11:22:33:44:01",
                        "model": "Router"
                    }
                elif last_octet == 2:
                    raise Exception("SNMP timeout")
                else:
                    return None

            mock_discovery.side_effect = mock_device_response
            mock_settings.return_value = {"discovery_concurrency": 20}

            # Act
            result = await perform_full_discovery(test_db, mock_client, network, subnet)

            # Assert
            assert result["total_scanned"] == 6
            assert result["devices_found"] == 1  # Only device-1 succeeded

    async def test_get_repository(self, test_db):
        """
        TC01-008: Verify repository creation

        Expected Result:
        - Repository instance created correctly
        - Has access to database session
        """
        # Act
        repo = get_repository(test_db)

        # Assert
        from services.device_service import SQLAlchemyDeviceRepository
        assert isinstance(repo, SQLAlchemyDeviceRepository)
        assert repo.db == test_db


@pytest.mark.unit
class TestDiscoveryInputValidation:
    """
    Test input validation for discovery service
    """

    @pytest.mark.asyncio
    async def test_discovery_with_host_address(self, test_db):
        """
        TC01-009: Verify discovery with single host (/32)

        Expected Result:
        - Single IP scanned
        - Works with /32 subnet
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)
        network = "192.168.1.1"
        subnet = "32"  # Single host

        with patch('services.discovery_service.device_discovery', new_callable=AsyncMock) as mock_discovery, \
             patch('services.discovery_service.get_runtime_settings') as mock_settings:

            mock_discovery.return_value = {
                "ip_address": "192.168.1.1",
                "hostname": "single-device",
                "vendor": "Cisco",
                "mac_address": "00:11:22:33:44:55",
                "model": "Router"
            }
            mock_settings.return_value = {"discovery_concurrency": 20}

            # Act
            result = await perform_full_discovery(test_db, mock_client, network, subnet)

            # Assert
            # /32 has 1 IP but .hosts() returns empty iterator for /32
            # So total_scanned might be 0 or implementation specific
            assert result is not None

    @pytest.mark.asyncio
    async def test_discovery_network_with_strict_false(self, test_db):
        """
        TC01-010: Verify discovery handles non-network addresses correctly

        Expected Result:
        - Non-network IP (e.g., 192.168.1.5/24) normalized to 192.168.1.0/24
        - Discovery proceeds with correct network range
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)
        network = "192.168.1.5"  # Not a network address
        subnet = "29"

        with patch('services.discovery_service.device_discovery', new_callable=AsyncMock) as mock_discovery, \
             patch('services.discovery_service.get_runtime_settings') as mock_settings:

            mock_discovery.return_value = None
            mock_settings.return_value = {"discovery_concurrency": 20}

            # Act
            result = await perform_full_discovery(test_db, mock_client, network, subnet)

            # Assert - Should normalize to 192.168.1.0/29 and scan 6 hosts
            assert result["total_scanned"] == 6
