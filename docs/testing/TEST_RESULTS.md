# Test Execution Report

**Generated**: 2025-12-04 06:58:40
**Status**: ❌ FAILED

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 158 |
| **✅ Passed** | 134 (84.8%) |
| **❌ Failed** | 24 |
| **⏭️ Skipped** | 0 |
| **⏱️ Duration** | 12.79s |
| **📈 Coverage** | 67.5% |

---

## 🎯 Test Case Mapping

### TC01: Device Discovery

### TC01 - Device Discovery

| Test | Status | Duration |
|------|--------|----------|
| `test_network_discovery_success` | ❌ FAILED | 0.006s |
| `test_network_discovery_empty_network` | ✅ PASSED | 0.007s |
| `test_network_discovery_invalid_cidr` | ✅ PASSED | 0.003s |
| `test_network_discovery_large_subnet` | ✅ PASSED | 0.055s |
| `test_network_discovery_with_concurrency_limit` | ✅ PASSED | 0.009s |
| `test_device_deduplication_by_mac` | ❌ FAILED | 0.019s |
| `test_discovery_with_partial_failures` | ✅ PASSED | 0.008s |
| `test_get_repository` | ✅ PASSED | 0.001s |
| `test_discovery_with_host_address` | ✅ PASSED | 0.005s |
| `test_discovery_network_with_strict_false` | ✅ PASSED | 0.008s |

### TC02 - SNMP Polling

| Test | Status | Duration |
|------|--------|----------|
| `test_poll_device_success_cisco` | ❌ FAILED | 0.004s |
| `test_poll_device_timeout` | ✅ PASSED | 0.008s |
| `test_poll_device_recovery` | ❌ FAILED | 0.005s |
| `test_poll_device_alert_triggering` | ❌ FAILED | 0.008s |
| `test_poll_interfaces_success` | ✅ PASSED | 0.030s |
| `test_perform_full_poll_with_multiple_devices` | ❌ FAILED | 0.035s |
| `test_calculate_interface_speed` | ✅ PASSED | 0.000s |
| `test_calculate_interface_speed_missing` | ✅ PASSED | 0.000s |
| `test_clear_interface_alerts` | ✅ PASSED | 0.017s |
| `test_polling_interval_update` | ❌ FAILED | 0.001s |
| `test_polling_concurrency_update` | ❌ FAILED | 0.001s |

### TC03 - Alert System

| Test | Status | Duration |
|------|--------|----------|
| `test_alert_state_transitions` | ❌ FAILED | 0.030s |
| `test_acknowledge_cpu_alert` | ❌ FAILED | 0.006s |
| `test_acknowledge_memory_alert` | ❌ FAILED | 0.007s |
| `test_acknowledge_reachability_alert` | ❌ FAILED | 0.010s |
| `test_resolve_cpu_alert` | ❌ FAILED | 0.016s |
| `test_resolve_memory_alert` | ❌ FAILED | 0.018s |
| `test_alert_not_found` | ✅ PASSED | 0.009s |
| `test_interface_alert_acknowledge` | ❌ FAILED | 0.013s |
| `test_interface_alert_resolve` | ❌ FAILED | 0.017s |
| `test_alert_response_format` | ❌ FAILED | 0.007s |
| `test_get_recipients_empty` | ✅ PASSED | 0.013s |
| `test_create_recipient` | ✅ PASSED | 0.025s |
| `test_create_duplicate_recipient` | ✅ PASSED | 0.015s |
| `test_get_all_recipients` | ✅ PASSED | 0.015s |
| `test_delete_recipient` | ✅ PASSED | 0.024s |
| `test_delete_nonexistent_recipient` | ✅ PASSED | 0.012s |
| `test_acknowledge_device_alert` | ❌ FAILED | 0.008s |
| `test_resolve_device_alert` | ❌ FAILED | 0.013s |
| `test_get_active_alerts_empty` | ✅ PASSED | 0.037s |

### TC04 - Configuration

| Test | Status | Duration |
|------|--------|----------|
| `test_send_email_missing_configuration` | ✅ PASSED | 0.002s |

### Other Tests

| Test | Status | Duration |
|------|--------|----------|
| `test_login_with_valid_credentials_returns_token` | ✅ PASSED | 0.420s |
| `test_login_with_invalid_username_fails` | ✅ PASSED | 0.015s |
| `test_login_with_invalid_password_fails` | ✅ PASSED | 0.436s |
| `test_protected_endpoint_without_token_blocked` | ✅ PASSED | 0.008s |
| `test_protected_endpoint_with_valid_token_allowed` | ✅ PASSED | 0.023s |
| `test_protected_endpoint_with_invalid_token_blocked` | ✅ PASSED | 0.010s |
| `test_protected_endpoint_with_malformed_header_blocked` | ✅ PASSED | 0.007s |
| `test_device_endpoints_require_auth` | ✅ PASSED | 0.023s |
| `test_query_endpoints_require_auth` | ✅ PASSED | 0.007s |
| `test_recipient_endpoints_require_auth` | ✅ PASSED | 0.013s |
| `test_auth_headers_allow_device_access` | ✅ PASSED | 0.016s |
| `test_auth_headers_allow_query_access` | ✅ PASSED | 0.156s |
| `test_auth_headers_allow_recipient_access` | ✅ PASSED | 0.015s |
| `test_get_all_devices_empty` | ✅ PASSED | 0.026s |
| `test_get_all_devices` | ✅ PASSED | 0.015s |
| `test_get_device_by_ip` | ✅ PASSED | 0.013s |
| `test_get_device_not_found` | ✅ PASSED | 0.016s |
| `test_update_device_thresholds` | ✅ PASSED | 0.025s |
| `test_update_device_thresholds_partial` | ✅ PASSED | 0.024s |
| `test_update_thresholds_invalid_device` | ✅ PASSED | 0.019s |
| `test_update_interface_threshold` | ✅ PASSED | 0.030s |
| `test_device_response_schema` | ✅ PASSED | 0.018s |
| `test_get_network_summary_empty` | ✅ PASSED | 0.064s |
| `test_get_network_summary` | ✅ PASSED | 0.077s |
| `test_get_top_cpu_devices` | ✅ PASSED | 0.021s |
| `test_get_top_memory_devices` | ✅ PASSED | 0.015s |
| `test_get_device_metrics` | ✅ PASSED | 0.022s |
| `test_get_device_metrics_not_found` | ✅ PASSED | 0.016s |
| `test_get_interface_summary` | ✅ PASSED | 0.031s |
| `test_get_interface_summary_not_found` | ✅ PASSED | 0.014s |
| `test_get_network_throughput` | ✅ PASSED | 0.027s |
| `test_query_response_schemas` | ✅ PASSED | 0.070s |
| `test_cache_initialization_success` | ✅ PASSED | 0.007s |
| `test_cache_initialization_disabled` | ✅ PASSED | 0.002s |
| `test_cache_initialization_connection_failure` | ✅ PASSED | 0.002s |
| `test_cache_initialization_custom_host_port` | ✅ PASSED | 0.003s |
| `test_cache_get_hit` | ✅ PASSED | 0.003s |
| `test_cache_get_miss` | ✅ PASSED | 0.003s |
| `test_cache_get_when_unavailable` | ✅ PASSED | 0.002s |
| `test_cache_get_json_decode_error` | ✅ PASSED | 0.005s |
| `test_cache_set_success` | ✅ PASSED | 0.003s |
| `test_cache_set_when_unavailable` | ✅ PASSED | 0.002s |
| `test_cache_set_default_ttl` | ✅ PASSED | 0.003s |
| `test_cache_set_complex_data` | ✅ PASSED | 0.003s |
| `test_cache_delete_success` | ✅ PASSED | 0.003s |
| `test_cache_delete_when_unavailable` | ✅ PASSED | 0.002s |
| `test_cache_delete_pattern_success` | ✅ PASSED | 0.003s |
| `test_cache_clear_all_success` | ✅ PASSED | 0.004s |
| `test_cached_decorator_cache_miss` | ✅ PASSED | 0.002s |
| `test_cached_decorator_cache_hit` | ✅ PASSED | 0.002s |
| `test_cached_decorator_custom_ttl` | ✅ PASSED | 0.002s |
| `test_cache_handles_none_value` | ✅ PASSED | 0.003s |
| `test_cache_handles_empty_string_key` | ✅ PASSED | 0.003s |
| `test_extract_vendor_cisco` | ❌ FAILED | 0.001s |
| `test_extract_vendor_juniper` | ❌ FAILED | 0.001s |
| `test_extract_vendor_hp` | ✅ PASSED | 0.000s |
| `test_extract_vendor_3com` | ✅ PASSED | 0.000s |
| `test_extract_vendor_dell` | ✅ PASSED | 0.001s |
| `test_extract_vendor_unknown` | ✅ PASSED | 0.001s |
| `test_extract_vendor_invalid_format` | ✅ PASSED | 0.000s |
| `test_extract_vendor_missing_vendor_id` | ✅ PASSED | 0.000s |
| `test_extract_vendor_short_oid` | ✅ PASSED | 0.000s |
| `test_extract_vendor_empty_string` | ✅ PASSED | 0.000s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.9.1.685-Cisco Systems]` | ❌ FAILED | 0.001s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.2636.1.1.1.2.20-Juniper Networks]` | ❌ FAILED | 0.001s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.11.2.3.7.11.17-HP]` | ✅ PASSED | 0.001s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.43.1.8.15-3Com]` | ✅ PASSED | 0.000s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.674.10895.3028-Dell]` | ✅ PASSED | 0.001s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.4413.1.1.1-Broadcom]` | ✅ PASSED | 0.001s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.6876.1.1-VMware]` | ✅ PASSED | 0.000s |
| `test_format_mac_address_standard` | ✅ PASSED | 0.000s |
| `test_format_mac_address_lowercase` | ✅ PASSED | 0.000s |
| `test_format_mac_address_mixed_case` | ✅ PASSED | 0.002s |
| `test_format_mac_address_all_zeros` | ✅ PASSED | 0.000s |
| `test_format_mac_address_all_fs` | ✅ PASSED | 0.001s |
| `test_format_mac_address_leading_zeros` | ✅ PASSED | 0.000s |
| `test_format_mac_address_various_inputs[0x001122334455-00:11:22:33:44:55]` | ✅ PASSED | 0.001s |
| `test_format_mac_address_various_inputs[0xAABBCCDDEEFF-AA:BB:CC:DD:EE:FF]` | ✅ PASSED | 0.000s |
| `test_format_mac_address_various_inputs[0x123456789ABC-12:34:56:78:9A:BC]` | ✅ PASSED | 0.001s |
| `test_format_mac_address_various_inputs[0x000000000001-00:00:00:00:00:01]` | ✅ PASSED | 0.000s |
| `test_format_mac_address_various_inputs[0xfedcba987654-FE:DC:BA:98:76:54]` | ✅ PASSED | 0.001s |
| `test_format_mac_address_short_value` | ✅ PASSED | 0.001s |
| `test_format_mac_address_odd_length` | ✅ PASSED | 0.001s |
| `test_vendor_mapping_has_common_vendors` | ✅ PASSED | 0.001s |
| `test_device_info_extraction` | ✅ PASSED | 0.001s |
| `test_multiple_device_info_extractions[1.3.6.1.4.1.9.1.1-0xaabbccddeeff-Cisco]` | ✅ PASSED | 0.001s |
| `test_multiple_device_info_extractions[1.3.6.1.4.1.2636.1.1-0x112233445566-Juniper]` | ✅ PASSED | 0.001s |
| `test_multiple_device_info_extractions[1.3.6.1.4.1.11.2.3-0x123456789abc-HP]` | ✅ PASSED | 0.000s |
| `test_send_email_success` | ✅ PASSED | 0.008s |
| `test_send_email_no_recipients` | ✅ PASSED | 0.001s |
| `test_send_email_smtp_connection_failure` | ✅ PASSED | 0.002s |
| `test_send_email_authentication_failure` | ✅ PASSED | 0.004s |
| `test_send_email_multiple_recipients` | ✅ PASSED | 0.006s |
| `test_send_email_correct_headers` | ✅ PASSED | 0.005s |
| `test_send_email_background` | ✅ PASSED | 0.003s |
| `test_send_email_body_content` | ✅ PASSED | 0.007s |
| `test_send_email_with_special_characters_in_subject` | ✅ PASSED | 0.115s |
| `test_send_email_none_recipients` | ✅ PASSED | 0.001s |
| `test_client_initialization` | ✅ PASSED | 0.000s |
| `test_client_default_initialization` | ✅ PASSED | 0.001s |
| `test_get_query_success` | ✅ PASSED | 0.156s |
| `test_get_query_timeout` | ✅ PASSED | 0.191s |
| `test_get_query_error_indication` | ✅ PASSED | 0.148s |
| `test_get_query_multiple_oids` | ✅ PASSED | 0.134s |
| `test_bulk_walk_success` | ❌ FAILED | 0.141s |
| `test_bulk_walk_error` | ✅ PASSED | 0.143s |
| `test_bulk_walk_exception` | ✅ PASSED | 0.167s |
| `test_get_snmp_data` | ✅ PASSED | 0.003s |
| `test_bulk_snmp_walk` | ✅ PASSED | 0.003s |
| `test_oid_with_double_colon` | ✅ PASSED | 0.001s |
| `test_oid_without_double_colon` | ✅ PASSED | 0.001s |
| `test_snmp_client_community_string[public-public]` | ✅ PASSED | 0.000s |
| `test_snmp_client_community_string[private-private]` | ✅ PASSED | 0.001s |
| `test_snmp_client_community_string[my-community-my-community]` | ✅ PASSED | 0.000s |
| `test_snmp_client_timeout_values[1-1]` | ✅ PASSED | 0.000s |
| `test_snmp_client_timeout_values[5-5]` | ✅ PASSED | 0.000s |
| `test_snmp_client_timeout_values[30-30]` | ✅ PASSED | 0.000s |

---

## ❌ Failed Tests Details

### tests/test_alerts.py::TestAlertWorkflow::test_alert_state_transitions

```
backend/tests/test_alerts.py:23: in test_alert_state_transitions
    assert response.status_code == status.HTTP_200_OK
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
E    +  and   200 = status.HTTP_200_OK
```

### tests/test_alerts.py::TestAlertWorkflow::test_acknowledge_cpu_alert

```
backend/tests/test_alerts.py:40: in test_acknowledge_cpu_alert
    assert response.status_code == status.HTTP_200_OK
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
E    +  and   200 = status.HTTP_200_OK
```

### tests/test_alerts.py::TestAlertWorkflow::test_acknowledge_memory_alert

```
backend/tests/test_alerts.py:51: in test_acknowledge_memory_alert
    assert response.status_code == status.HTTP_200_OK
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
E    +  and   200 = status.HTTP_200_OK
```

### tests/test_alerts.py::TestAlertWorkflow::test_acknowledge_reachability_alert

```
backend/tests/test_alerts.py:60: in test_acknowledge_reachability_alert
    assert response.status_code == status.HTTP_200_OK
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
E    +  and   200 = status.HTTP_200_OK
```

### tests/test_alerts.py::TestAlertWorkflow::test_resolve_cpu_alert

```
backend/tests/test_alerts.py:73: in test_resolve_cpu_alert
    assert response.status_code == status.HTTP_200_OK
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
E    +  and   200 = status.HTTP_200_OK
```

### tests/test_alerts.py::TestAlertWorkflow::test_resolve_memory_alert

```
backend/tests/test_alerts.py:86: in test_resolve_memory_alert
    assert response.status_code == status.HTTP_200_OK
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
E    +  and   200 = status.HTTP_200_OK
```

### tests/test_alerts.py::TestAlertWorkflow::test_interface_alert_acknowledge

```
backend/tests/test_alerts.py:100: in test_interface_alert_acknowledge
    assert response.status_code == status.HTTP_200_OK
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
E    +  and   200 = status.HTTP_200_OK
```

### tests/test_alerts.py::TestAlertWorkflow::test_interface_alert_resolve

```
backend/tests/test_alerts.py:115: in test_interface_alert_resolve
    assert response.status_code == status.HTTP_200_OK
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
E    +  and   200 = status.HTTP_200_OK
```

### tests/test_alerts.py::TestAlertWorkflow::test_alert_response_format

```
backend/tests/test_alerts.py:124: in test_alert_response_format
    assert response.status_code == status.HTTP_200_OK
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
E    +  and   200 = status.HTTP_200_OK
```

### tests/test_devices.py::TestDeviceEndpoints::test_acknowledge_device_alert

```
backend/tests/test_devices.py:95: in test_acknowledge_device_alert
    assert response.status_code == status.HTTP_200_OK
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
E    +  and   200 = status.HTTP_200_OK
```

### tests/test_devices.py::TestDeviceEndpoints::test_resolve_device_alert

```
backend/tests/test_devices.py:109: in test_resolve_device_alert
    assert response.status_code == status.HTTP_200_OK
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
E    +  and   200 = status.HTTP_200_OK
```

### tests/unit/test_device_service.py::TestExtractVendor::test_extract_vendor_cisco

```
backend/tests/unit/test_device_service.py:18: in test_extract_vendor_cisco
    assert result == "Cisco Systems"
E   AssertionError: assert 'Cisco' == 'Cisco Systems'
E     
E     - Cisco Systems
E     + Cisco
```

### tests/unit/test_device_service.py::TestExtractVendor::test_extract_vendor_juniper

```
backend/tests/unit/test_device_service.py:24: in test_extract_vendor_juniper
    assert result == "Juniper Networks"
E   AssertionError: assert 'Juniper' == 'Juniper Networks'
E     
E     - Juniper Networks
E     + Juniper
```

### tests/unit/test_device_service.py::TestExtractVendor::test_extract_vendor_various_oids[1.3.6.1.4.1.9.1.685-Cisco Systems]

```
backend/tests/unit/test_device_service.py:86: in test_extract_vendor_various_oids
    assert expected_vendor in result or result.startswith("Unknown")
E   AssertionError: assert ('Cisco Systems' in 'Cisco' or False)
E    +  where False = <built-in method startswith of str object at 0x748e90e8ff30>('Unknown')
E    +    where <built-in method startswith of str object at 0x748e90e8ff30> = 'Cisco'.startswith
```

### tests/unit/test_device_service.py::TestExtractVendor::test_extract_vendor_various_oids[1.3.6.1.4.1.2636.1.1.1.2.20-Juniper Networks]

```
backend/tests/unit/test_device_service.py:86: in test_extract_vendor_various_oids
    assert expected_vendor in result or result.startswith("Unknown")
E   AssertionError: assert ('Juniper Networks' in 'Juniper' or False)
E    +  where False = <built-in method startswith of str object at 0x748e90d70030>('Unknown')
E    +    where <built-in method startswith of str object at 0x748e90d70030> = 'Juniper'.startswith
```

### tests/unit/test_discovery_service.py::TestDiscoveryService::test_network_discovery_success

```
backend/tests/unit/test_discovery_service.py:70: in test_network_discovery_success
    assert result["devices_found"] == 3
E   assert 0 == 3
```

### tests/unit/test_discovery_service.py::TestDiscoveryService::test_device_deduplication_by_mac

```
backend/tests/unit/test_discovery_service.py:262: in test_device_deduplication_by_mac
    assert updated_device.ip_address == "192.168.1.10"
E   AssertionError: assert '192.168.1.1' == '192.168.1.10'
E     
E     - 192.168.1.10
E     ?            -
E     + 192.168.1.1
```

### tests/unit/test_polling_service.py::TestPollingService::test_poll_device_success_cisco

```
backend/tests/unit/test_polling_service.py:61: in test_poll_device_success_cisco
    assert result is True, "Poll should succeed"
E   AssertionError: Poll should succeed
E   assert False is True
```

### tests/unit/test_polling_service.py::TestPollingService::test_poll_device_recovery

```
backend/tests/unit/test_polling_service.py:138: in test_poll_device_recovery
    assert result is True
E   assert False is True
```

### tests/unit/test_polling_service.py::TestPollingService::test_poll_device_alert_triggering

```
backend/tests/unit/test_polling_service.py:174: in test_poll_device_alert_triggering
    assert result is True
E   assert False is True
```

### tests/unit/test_polling_service.py::TestPollingService::test_perform_full_poll_with_multiple_devices

```
backend/tests/unit/test_polling_service.py:259: in test_perform_full_poll_with_multiple_devices
    assert mock_get.call_count >= len(sample_devices)
E   AssertionError: assert 0 >= 5
E    +  where 0 = <AsyncMock name='get_snmp_data' id='128155515266464'>.call_count
E    +  and   5 = len([<app.core.models.Device object at 0x748e8c1e9bb0>, <app.core.models.Device object at 0x748e8c1e8410>, <app.core.models.Device object at 0x748e8c1ead20>, <app.core.models.Device object at 0x748e8c1e9280>, <app.c
```

### tests/unit/test_polling_service.py::TestPollingConfiguration::test_polling_interval_update

```
backend/tests/unit/test_polling_service.py:337: in test_polling_interval_update
    config_model = models.Config(
                   ^^^^^^^^^^^^^
E   AttributeError: module 'app.core.models' has no attribute 'Config'
```

### tests/unit/test_polling_service.py::TestPollingConfiguration::test_polling_concurrency_update

```
backend/tests/unit/test_polling_service.py:361: in test_polling_concurrency_update
    config_model = models.Config(
                   ^^^^^^^^^^^^^
E   AttributeError: module 'app.core.models' has no attribute 'Config'
```

### tests/unit/test_snmp_service.py::TestPySNMPClient::test_bulk_walk_success

```
backend/tests/unit/test_snmp_service.py:163: in test_bulk_walk_success
    assert result["success"] is True
E   assert False is True
```


---

## 📈 Coverage Report

| Module | Coverage |
|--------|----------|
| `__init__.py` | 100.0% |
| `__init__.py` | 100.0% |
| `__init__.py` | 100.0% |
| `recipients.py` | 100.0% |
| `models.py` | 100.0% |
| `schemas.py` | 100.0% |
| `__init__.py` | 100.0% |
| `discovery_service.py` | 100.0% |
| `email_service.py` | 100.0% |
| `security.py` | 90.9% |

---

## 📝 Test Case Status Summary

| Test Case ID | Description | Status |
|--------------|-------------|--------|
| **TC01** | Device Discovery | ❌ Fail |
| **TC02** | SNMP Polling | ❌ Fail |
| **TC03** | Alert Triggering | ❌ Fail |
| **TC04** | Configuration Changes | ✅ Pass |
| **TC05** | Device Details View | ⏳ Pending |
| **TC06** | Alert History | ⏳ Pending |
| **TC07** | Invalid SNMP String | ⏳ Pending |

---

**Report End**
