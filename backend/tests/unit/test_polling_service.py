"""
Unit tests for Polling Service

Test Case ID: TC02, TC04
Description: Tests SNMP polling functionality and configuration changes
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from services.polling_service import (
    poll_device,
    poll_interfaces,
    perform_full_poll,
    calculate_interface_speed,
    clear_interface_alerts
)
from services.snmp_service import SNMPClient, PySNMPClient
from app.core import models


@pytest.mark.unit
@pytest.mark.asyncio
class TestPollingService:
    """
    Test Case TC02: Poll device every 30 seconds
    Test Case TC04: Change polling interval in settings
    """

    async def test_poll_device_success_cisco(self, test_db, sample_device):
        """
        TC02-001: Verify successful polling of Cisco device

        Expected Result:
        - Accurate SNMP metrics returned
        - CPU and memory utilization calculated correctly
        - Device marked as reachable
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)

        # Mock SNMP response with Cisco vendor OIDs
        mock_snmp_response = {
            "success": True,
            "data": [
                {"oid": "1.3.6.1.2.1.1.5.0", "value": "test-device"},
                {"oid": "1.3.6.1.2.1.1.3.0", "value": "86400"},
                {"oid": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1", "value": "45.5"},  # CPU
                {"oid": "1.3.6.1.4.1.9.9.48.1.1.1.5.1", "value": "500000000"},  # Used memory
                {"oid": "1.3.6.1.4.1.9.9.48.1.1.1.6.1", "value": "1500000000"}  # Free memory
            ]
        }

        with patch('services.polling_service.get_snmp_data', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_snmp_response

            # Act
            result = await poll_device(sample_device, mock_client, test_db)

            # Assert
            assert result is True, "Poll should succeed"
            assert sample_device.is_reachable is True
            assert sample_device.consecutive_failures == 0
            assert sample_device.last_poll_success is not None

            # Verify metrics were saved
            test_db.flush()
            metrics = test_db.query(models.DeviceMetric).filter_by(
                device_id=sample_device.id
            ).all()
            assert len(metrics) == 1
            assert metrics[0].cpu_utilization == 45.5

    async def test_poll_device_timeout(self, test_db, sample_device):
        """
        TC02-002: Verify polling handles unreachable device

        Expected Result:
        - Device marked as unreachable after failure_threshold
        - No metrics inserted
        - Consecutive failures incremented
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)
        sample_device.failure_threshold = 2
        sample_device.consecutive_failures = 1  # Already has 1 failure

        # Mock SNMP failure
        with patch('services.polling_service.get_snmp_data', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"success": False}

            # Act
            result = await poll_device(sample_device, mock_client, test_db)

            # Assert
            assert result is False, "Poll should fail"
            assert sample_device.consecutive_failures == 2
            assert sample_device.is_reachable is False  # Should be marked unreachable

            # Verify no metrics saved
            metrics = test_db.query(models.DeviceMetric).filter_by(
                device_id=sample_device.id
            ).all()
            assert len(metrics) == 0

    async def test_poll_device_recovery(self, test_db, sample_device):
        """
        TC02-003: Verify device recovery after being unreachable

        Expected Result:
        - Device marked as reachable
        - Consecutive failures reset to 0
        - Metrics collection resumes
        """
        # Arrange
        sample_device.is_reachable = False
        sample_device.consecutive_failures = 5
        mock_client = Mock(spec=SNMPClient)

        mock_snmp_response = {
            "success": True,
            "data": [
                {"oid": "1.3.6.1.2.1.1.5.0", "value": "test-device"},
                {"oid": "1.3.6.1.2.1.1.3.0", "value": "86400"},
                {"oid": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1", "value": "30.0"},
                {"oid": "1.3.6.1.4.1.9.9.48.1.1.1.5.1", "value": "300000000"},
                {"oid": "1.3.6.1.4.1.9.9.48.1.1.1.6.1", "value": "1700000000"}
            ]
        }

        with patch('services.polling_service.get_snmp_data', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_snmp_response

            # Act
            result = await poll_device(sample_device, mock_client, test_db)

            # Assert
            assert result is True
            assert sample_device.is_reachable is True
            assert sample_device.consecutive_failures == 0

    async def test_poll_device_alert_triggering(self, test_db, sample_device):
        """
        TC02-004: Verify alert triggering when threshold exceeded

        Expected Result:
        - Alert state changes from 'clear' to 'triggered'
        - CPU threshold breach detected
        """
        # Arrange
        sample_device.cpu_threshold = 80.0
        sample_device.cpu_alert_state = "clear"
        mock_client = Mock(spec=SNMPClient)

        # Mock SNMP response with high CPU
        mock_snmp_response = {
            "success": True,
            "data": [
                {"oid": "1.3.6.1.2.1.1.5.0", "value": "test-device"},
                {"oid": "1.3.6.1.2.1.1.3.0", "value": "86400"},
                {"oid": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1", "value": "85.0"},  # High CPU
                {"oid": "1.3.6.1.4.1.9.9.48.1.1.1.5.1", "value": "500000000"},
                {"oid": "1.3.6.1.4.1.9.9.48.1.1.1.6.1", "value": "1500000000"}
            ]
        }

        with patch('services.polling_service.get_snmp_data', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_snmp_response

            # Act
            result = await poll_device(sample_device, mock_client, test_db)

            # Assert
            assert result is True
            assert sample_device.cpu_alert_state == "triggered"

    async def test_poll_interfaces_success(self, test_db, sample_device):
        """
        TC02-005: Verify interface polling collects interface metrics

        Expected Result:
        - Interface metrics collected
        - Interface speed calculated
        - Interface added to database
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)

        # Mock bulk walk response for interfaces
        mock_bulk_response = {
            "success": True,
            "data": [
                {"base_oid": "1.3.6.1.2.1.2.2.1.2", "index": "1", "value": "GigabitEthernet0/0"},
                {"base_oid": "1.3.6.1.2.1.2.2.1.5", "index": "1", "value": "1000000000"},  # 1 Gbps
                {"base_oid": "1.3.6.1.2.1.2.2.1.7", "index": "1", "value": "1"},  # admin up
                {"base_oid": "1.3.6.1.2.1.2.2.1.8", "index": "1", "value": "1"},  # oper up
                {"base_oid": "1.3.6.1.2.1.2.2.1.10", "index": "1", "value": "1000000"},
                {"base_oid": "1.3.6.1.2.1.2.2.1.16", "index": "1", "value": "2000000"},
                {"base_oid": "1.3.6.1.2.1.2.2.1.14", "index": "1", "value": "0"},
                {"base_oid": "1.3.6.1.2.1.2.2.1.20", "index": "1", "value": "0"},
                {"base_oid": "1.3.6.1.2.1.2.2.1.13", "index": "1", "value": "0"},
                {"base_oid": "1.3.6.1.2.1.2.2.1.19", "index": "1", "value": "0"}
            ]
        }

        with patch('services.polling_service.bulk_snmp_walk', new_callable=AsyncMock) as mock_walk:
            mock_walk.return_value = mock_bulk_response

            # Act
            await poll_interfaces(sample_device, mock_client, test_db)

            # Assert
            test_db.flush()
            interfaces = test_db.query(models.Interface).filter_by(
                device_id=sample_device.id
            ).all()
            assert len(interfaces) == 1
            assert interfaces[0].if_name == "GigabitEthernet0/0"
            assert interfaces[0].speed_bps == 1000000000

    async def test_perform_full_poll_with_multiple_devices(self, test_db, sample_devices):
        """
        TC02-006: Verify full polling cycle with multiple devices

        Expected Result:
        - All devices polled concurrently
        - Success/failure counts accurate
        """
        # Arrange
        mock_client = Mock(spec=SNMPClient)

        # Mock successful SNMP response
        mock_snmp_response = {
            "success": True,
            "data": [
                {"oid": "1.3.6.1.2.1.1.5.0", "value": "device"},
                {"oid": "1.3.6.1.2.1.1.3.0", "value": "86400"},
                {"oid": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1", "value": "50.0"},
                {"oid": "1.3.6.1.4.1.9.9.48.1.1.1.5.1", "value": "500000000"},
                {"oid": "1.3.6.1.4.1.9.9.48.1.1.1.6.1", "value": "1500000000"}
            ]
        }

        mock_bulk_response = {"success": True, "data": []}

        with patch('services.polling_service.get_snmp_data', new_callable=AsyncMock) as mock_get, \
             patch('services.polling_service.bulk_snmp_walk', new_callable=AsyncMock) as mock_walk, \
             patch('services.polling_service.get_runtime_settings') as mock_settings:

            mock_get.return_value = mock_snmp_response
            mock_walk.return_value = mock_bulk_response
            mock_settings.return_value = {"polling_concurrency": 5}

            # Act
            await perform_full_poll(test_db, mock_client)

            # Assert
            # Verify all devices were attempted to poll
            assert mock_get.call_count >= len(sample_devices)

    def test_calculate_interface_speed(self):
        """
        TC02-007: Verify interface speed calculation

        Expected Result:
        - Speed calculated correctly from ifSpeed OID
        """
        # Arrange
        raw_data = {
            "1.3.6.1.2.1.2.2.1.5": "1000000000"  # ifSpeed
        }

        # Act
        speed_bps, speed_source = calculate_interface_speed(raw_data)

        # Assert
        assert speed_bps == 1000000000
        assert speed_source == "ifSpeed"

    def test_calculate_interface_speed_missing(self):
        """
        TC02-008: Verify interface speed handling when OID not available

        Expected Result:
        - Returns None gracefully
        """
        # Arrange
        raw_data = {}

        # Act
        speed_bps, speed_source = calculate_interface_speed(raw_data)

        # Assert
        assert speed_bps is None
        assert speed_source is None

    def test_clear_interface_alerts(self, test_db, sample_device, sample_interface):
        """
        TC02-009: Verify interface alerts cleared when device unreachable

        Expected Result:
        - All interface alerts set to 'clear'
        - Alert timestamps cleared
        """
        # Arrange
        sample_interface.oper_status_alert_state = "triggered"
        sample_interface.packet_drop_alert_state = "triggered"
        test_db.commit()

        # Act
        clear_interface_alerts(sample_device, test_db)
        test_db.flush()

        # Assert
        test_db.refresh(sample_interface)
        assert sample_interface.oper_status_alert_state == "clear"
        assert sample_interface.packet_drop_alert_state == "clear"
        assert sample_interface.oper_status_acknowledged_at is None
        assert sample_interface.packet_drop_acknowledged_at is None


@pytest.mark.unit
class TestPollingConfiguration:
    """
    Test Case TC04: Change polling interval in settings
    """

    def test_polling_interval_update(self, test_db):
        """
        TC04-001: Verify polling interval configuration change

        Expected Result:
        - Polling service reads updated interval from settings
        - Configuration change affects next poll cycle
        """
        # Arrange
        config_model = models.Config(
            key="polling_interval",
            value="30",
            description="Polling interval in seconds"
        )
        test_db.add(config_model)
        test_db.commit()

        # Act
        from app.config.settings import get_runtime_settings
        runtime_config = get_runtime_settings(test_db)

        # Assert
        assert runtime_config["polling_interval"] == 30

    def test_polling_concurrency_update(self, test_db):
        """
        TC04-002: Verify polling concurrency configuration

        Expected Result:
        - Concurrent polling limit configurable
        - Settings persisted in database
        """
        # Arrange
        config_model = models.Config(
            key="polling_concurrency",
            value="10",
            description="Number of concurrent polling tasks"
        )
        test_db.add(config_model)
        test_db.commit()

        # Act
        from app.config.settings import get_runtime_settings
        runtime_config = get_runtime_settings(test_db)

        # Assert
        assert runtime_config["polling_concurrency"] == 10
