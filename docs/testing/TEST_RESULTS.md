# Test Execution Report

**Generated**: 2025-12-04 07:34:48
**Status**: ❌ FAILED

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 158 |
| **✅ Passed** | 155 (98.1%) |
| **❌ Failed** | 3 |
| **⏭️ Skipped** | 0 |
| **⏱️ Duration** | 5.64s |
| **📈 Coverage** | 69.5% |

---

## 🎯 Test Case Mapping

### TC01: Device Discovery

### TC01 - Device Discovery

| Test | Status | Duration |
|------|--------|----------|
| `test_network_discovery_success` | ❌ FAILED | 0.001s |
| `test_network_discovery_empty_network` | ✅ PASSED | 0.003s |
| `test_network_discovery_invalid_cidr` | ✅ PASSED | 0.002s |
| `test_network_discovery_large_subnet` | ✅ PASSED | 0.021s |
| `test_network_discovery_with_concurrency_limit` | ✅ PASSED | 0.003s |
| `test_device_deduplication_by_mac` | ✅ PASSED | 0.010s |
| `test_discovery_with_partial_failures` | ✅ PASSED | 0.002s |
| `test_get_repository` | ✅ PASSED | 0.000s |
| `test_discovery_with_host_address` | ✅ PASSED | 0.001s |
| `test_discovery_network_with_strict_false` | ✅ PASSED | 0.002s |

### TC02 - SNMP Polling

| Test | Status | Duration |
|------|--------|----------|
| `test_poll_device_success_cisco` | ✅ PASSED | 0.002s |
| `test_poll_device_timeout` | ✅ PASSED | 0.004s |
| `test_poll_device_recovery` | ✅ PASSED | 0.001s |
| `test_poll_device_alert_triggering` | ✅ PASSED | 0.002s |
| `test_poll_interfaces_success` | ✅ PASSED | 0.011s |
| `test_perform_full_poll_with_multiple_devices` | ❌ FAILED | 0.013s |
| `test_calculate_interface_speed` | ✅ PASSED | 0.000s |
| `test_calculate_interface_speed_missing` | ✅ PASSED | 0.000s |
| `test_clear_interface_alerts` | ✅ PASSED | 0.005s |
| `test_polling_interval_update` | ✅ PASSED | 0.005s |
| `test_polling_concurrency_update` | ✅ PASSED | 0.005s |

### TC03 - Alert System

| Test | Status | Duration |
|------|--------|----------|
| `test_alert_state_transitions` | ✅ PASSED | 0.023s |
| `test_acknowledge_cpu_alert` | ✅ PASSED | 0.010s |
| `test_acknowledge_memory_alert` | ✅ PASSED | 0.011s |
| `test_acknowledge_reachability_alert` | ✅ PASSED | 0.010s |
| `test_resolve_cpu_alert` | ✅ PASSED | 0.016s |
| `test_resolve_memory_alert` | ✅ PASSED | 0.016s |
| `test_alert_not_found` | ✅ PASSED | 0.007s |
| `test_interface_alert_acknowledge` | ✅ PASSED | 0.013s |
| `test_interface_alert_resolve` | ✅ PASSED | 0.021s |
| `test_alert_response_format` | ✅ PASSED | 0.009s |
| `test_get_recipients_empty` | ✅ PASSED | 0.006s |
| `test_create_recipient` | ✅ PASSED | 0.008s |
| `test_create_duplicate_recipient` | ✅ PASSED | 0.007s |
| `test_get_all_recipients` | ✅ PASSED | 0.005s |
| `test_delete_recipient` | ✅ PASSED | 0.010s |
| `test_delete_nonexistent_recipient` | ✅ PASSED | 0.005s |
| `test_acknowledge_device_alert` | ✅ PASSED | 0.010s |
| `test_resolve_device_alert` | ✅ PASSED | 0.016s |
| `test_get_active_alerts_empty` | ✅ PASSED | 0.014s |

### TC04 - Configuration

| Test | Status | Duration |
|------|--------|----------|
| `test_send_email_missing_configuration` | ✅ PASSED | 0.001s |

### Other Tests

| Test | Status | Duration |
|------|--------|----------|
| `test_login_with_valid_credentials_returns_token` | ✅ PASSED | 0.197s |
| `test_login_with_invalid_username_fails` | ✅ PASSED | 0.007s |
| `test_login_with_invalid_password_fails` | ✅ PASSED | 0.196s |
| `test_protected_endpoint_without_token_blocked` | ✅ PASSED | 0.003s |
| `test_protected_endpoint_with_valid_token_allowed` | ✅ PASSED | 0.008s |
| `test_protected_endpoint_with_invalid_token_blocked` | ✅ PASSED | 0.004s |
| `test_protected_endpoint_with_malformed_header_blocked` | ✅ PASSED | 0.004s |
| `test_device_endpoints_require_auth` | ✅ PASSED | 0.010s |
| `test_query_endpoints_require_auth` | ✅ PASSED | 0.003s |
| `test_recipient_endpoints_require_auth` | ✅ PASSED | 0.008s |
| `test_auth_headers_allow_device_access` | ✅ PASSED | 0.008s |
| `test_auth_headers_allow_query_access` | ✅ PASSED | 0.033s |
| `test_auth_headers_allow_recipient_access` | ✅ PASSED | 0.006s |
| `test_get_all_devices_empty` | ✅ PASSED | 0.007s |
| `test_get_all_devices` | ✅ PASSED | 0.006s |
| `test_get_device_by_ip` | ✅ PASSED | 0.007s |
| `test_get_device_not_found` | ✅ PASSED | 0.008s |
| `test_update_device_thresholds` | ✅ PASSED | 0.010s |
| `test_update_device_thresholds_partial` | ✅ PASSED | 0.009s |
| `test_update_thresholds_invalid_device` | ✅ PASSED | 0.008s |
| `test_update_interface_threshold` | ✅ PASSED | 0.013s |
| `test_device_response_schema` | ✅ PASSED | 0.006s |
| `test_get_network_summary_empty` | ✅ PASSED | 0.030s |
| `test_get_network_summary` | ✅ PASSED | 0.029s |
| `test_get_top_cpu_devices` | ✅ PASSED | 0.008s |
| `test_get_top_memory_devices` | ✅ PASSED | 0.007s |
| `test_get_device_metrics` | ✅ PASSED | 0.012s |
| `test_get_device_metrics_not_found` | ✅ PASSED | 0.008s |
| `test_get_interface_summary` | ✅ PASSED | 0.012s |
| `test_get_interface_summary_not_found` | ✅ PASSED | 0.007s |
| `test_get_network_throughput` | ✅ PASSED | 0.013s |
| `test_query_response_schemas` | ✅ PASSED | 0.028s |
| `test_cache_initialization_success` | ✅ PASSED | 0.003s |
| `test_cache_initialization_disabled` | ✅ PASSED | 0.001s |
| `test_cache_initialization_connection_failure` | ✅ PASSED | 0.001s |
| `test_cache_initialization_custom_host_port` | ✅ PASSED | 0.001s |
| `test_cache_get_hit` | ✅ PASSED | 0.001s |
| `test_cache_get_miss` | ✅ PASSED | 0.002s |
| `test_cache_get_when_unavailable` | ✅ PASSED | 0.001s |
| `test_cache_get_json_decode_error` | ✅ PASSED | 0.001s |
| `test_cache_set_success` | ✅ PASSED | 0.001s |
| `test_cache_set_when_unavailable` | ✅ PASSED | 0.001s |
| `test_cache_set_default_ttl` | ✅ PASSED | 0.001s |
| `test_cache_set_complex_data` | ✅ PASSED | 0.001s |
| `test_cache_delete_success` | ✅ PASSED | 0.001s |
| `test_cache_delete_when_unavailable` | ✅ PASSED | 0.001s |
| `test_cache_delete_pattern_success` | ✅ PASSED | 0.001s |
| `test_cache_clear_all_success` | ✅ PASSED | 0.001s |
| `test_cached_decorator_cache_miss` | ✅ PASSED | 0.001s |
| `test_cached_decorator_cache_hit` | ✅ PASSED | 0.001s |
| `test_cached_decorator_custom_ttl` | ✅ PASSED | 0.001s |
| `test_cache_handles_none_value` | ✅ PASSED | 0.001s |
| `test_cache_handles_empty_string_key` | ✅ PASSED | 0.001s |
| `test_extract_vendor_cisco` | ✅ PASSED | 0.000s |
| `test_extract_vendor_juniper` | ✅ PASSED | 0.000s |
| `test_extract_vendor_hp` | ✅ PASSED | 0.000s |
| `test_extract_vendor_3com` | ✅ PASSED | 0.000s |
| `test_extract_vendor_dell` | ✅ PASSED | 0.000s |
| `test_extract_vendor_unknown` | ✅ PASSED | 0.000s |
| `test_extract_vendor_invalid_format` | ✅ PASSED | 0.000s |
| `test_extract_vendor_missing_vendor_id` | ✅ PASSED | 0.000s |
| `test_extract_vendor_short_oid` | ✅ PASSED | 0.000s |
| `test_extract_vendor_empty_string` | ✅ PASSED | 0.000s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.9.1.685-Cisco]` | ✅ PASSED | 0.000s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.2636.1.1.1.2.20-Juniper]` | ✅ PASSED | 0.000s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.11.2.3.7.11.17-HP]` | ✅ PASSED | 0.000s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.43.1.8.15-3Com]` | ✅ PASSED | 0.000s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.674.10895.3028-Dell]` | ✅ PASSED | 0.000s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.4413.1.1.1-Broadcom]` | ✅ PASSED | 0.000s |
| `test_extract_vendor_various_oids[1.3.6.1.4.1.6876.1.1-VMware]` | ✅ PASSED | 0.000s |
| `test_format_mac_address_standard` | ✅ PASSED | 0.000s |
| `test_format_mac_address_lowercase` | ✅ PASSED | 0.000s |
| `test_format_mac_address_mixed_case` | ✅ PASSED | 0.000s |
| `test_format_mac_address_all_zeros` | ✅ PASSED | 0.000s |
| `test_format_mac_address_all_fs` | ✅ PASSED | 0.000s |
| `test_format_mac_address_leading_zeros` | ✅ PASSED | 0.000s |
| `test_format_mac_address_various_inputs[0x001122334455-00:11:22:33:44:55]` | ✅ PASSED | 0.000s |
| `test_format_mac_address_various_inputs[0xAABBCCDDEEFF-AA:BB:CC:DD:EE:FF]` | ✅ PASSED | 0.000s |
| `test_format_mac_address_various_inputs[0x123456789ABC-12:34:56:78:9A:BC]` | ✅ PASSED | 0.000s |
| `test_format_mac_address_various_inputs[0x000000000001-00:00:00:00:00:01]` | ✅ PASSED | 0.000s |
| `test_format_mac_address_various_inputs[0xfedcba987654-FE:DC:BA:98:76:54]` | ✅ PASSED | 0.000s |
| `test_format_mac_address_short_value` | ✅ PASSED | 0.000s |
| `test_format_mac_address_odd_length` | ✅ PASSED | 0.000s |
| `test_vendor_mapping_has_common_vendors` | ✅ PASSED | 0.000s |
| `test_device_info_extraction` | ✅ PASSED | 0.000s |
| `test_multiple_device_info_extractions[1.3.6.1.4.1.9.1.1-0xaabbccddeeff-Cisco]` | ✅ PASSED | 0.000s |
| `test_multiple_device_info_extractions[1.3.6.1.4.1.2636.1.1-0x112233445566-Juniper]` | ✅ PASSED | 0.000s |
| `test_multiple_device_info_extractions[1.3.6.1.4.1.11.2.3-0x123456789abc-HP]` | ✅ PASSED | 0.000s |
| `test_send_email_success` | ✅ PASSED | 0.003s |
| `test_send_email_no_recipients` | ✅ PASSED | 0.001s |
| `test_send_email_smtp_connection_failure` | ✅ PASSED | 0.001s |
| `test_send_email_authentication_failure` | ✅ PASSED | 0.003s |
| `test_send_email_multiple_recipients` | ✅ PASSED | 0.048s |
| `test_send_email_correct_headers` | ✅ PASSED | 0.002s |
| `test_send_email_background` | ✅ PASSED | 0.001s |
| `test_send_email_body_content` | ✅ PASSED | 0.002s |
| `test_send_email_with_special_characters_in_subject` | ✅ PASSED | 0.002s |
| `test_send_email_none_recipients` | ✅ PASSED | 0.001s |
| `test_client_initialization` | ✅ PASSED | 0.000s |
| `test_client_default_initialization` | ✅ PASSED | 0.000s |
| `test_get_query_success` | ✅ PASSED | 0.073s |
| `test_get_query_timeout` | ✅ PASSED | 0.070s |
| `test_get_query_error_indication` | ✅ PASSED | 0.068s |
| `test_get_query_multiple_oids` | ✅ PASSED | 0.068s |
| `test_bulk_walk_success` | ❌ FAILED | 0.073s |
| `test_bulk_walk_error` | ✅ PASSED | 0.072s |
| `test_bulk_walk_exception` | ✅ PASSED | 0.069s |
| `test_get_snmp_data` | ✅ PASSED | 0.001s |
| `test_bulk_snmp_walk` | ✅ PASSED | 0.001s |
| `test_oid_with_double_colon` | ✅ PASSED | 0.000s |
| `test_oid_without_double_colon` | ✅ PASSED | 0.000s |
| `test_snmp_client_community_string[public-public]` | ✅ PASSED | 0.000s |
| `test_snmp_client_community_string[private-private]` | ✅ PASSED | 0.000s |
| `test_snmp_client_community_string[my-community-my-community]` | ✅ PASSED | 0.000s |
| `test_snmp_client_timeout_values[1-1]` | ✅ PASSED | 0.000s |
| `test_snmp_client_timeout_values[5-5]` | ✅ PASSED | 0.000s |
| `test_snmp_client_timeout_values[30-30]` | ✅ PASSED | 0.000s |

---

## ❌ Failed Tests Details

### tests/unit/test_discovery_service.py::TestDiscoveryService::test_network_discovery_success

```
backend/tests/unit/test_discovery_service.py:54: in test_network_discovery_success
    mac_address=f"00:11:22:33:44:{ip.split('.')[-1]:02x}",
                                 ^^^^^^^^^^^^^^^^^^^^^^^
E   ValueError: Unknown format code 'x' for object of type 'str'
```

### tests/unit/test_polling_service.py::TestPollingService::test_perform_full_poll_with_multiple_devices

```
backend/tests/unit/test_polling_service.py:272: in test_perform_full_poll_with_multiple_devices
    assert mock_get.called, "get_snmp_data should have been called"
E   AssertionError: get_snmp_data should have been called
E   assert False
E    +  where False = <AsyncMock name='get_snmp_data' id='140096510024096'>.called
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
| `settings.py` | 92.3% |

---

## 📝 Test Case Status Summary

| Test Case ID | Description | Status |
|--------------|-------------|--------|
| **TC01** | Device Discovery | ❌ Fail |
| **TC02** | SNMP Polling | ❌ Fail |
| **TC03** | Alert Triggering | ✅ Pass |
| **TC04** | Configuration Changes | ✅ Pass |
| **TC05** | Device Details View | ⏳ Pending |
| **TC06** | Alert History | ⏳ Pending |
| **TC07** | Invalid SNMP String | ⏳ Pending |

---

**Report End**
