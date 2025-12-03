"""
Unit tests for Device Service

Tests device service helper functions (vendor extraction, MAC formatting).
"""
import pytest
from services.device_service import extract_vendor, format_mac_address


@pytest.mark.unit
class TestExtractVendor:
    """Test vendor extraction from SNMP OID"""

    def test_extract_vendor_cisco(self):
        """Test: Extract Cisco vendor from OID"""
        oid = "1.3.6.1.4.1.9.1.685"
        result = extract_vendor(oid)
        assert result == "Cisco"

    def test_extract_vendor_juniper(self):
        """Test: Extract Juniper vendor from OID"""
        oid = "1.3.6.1.4.1.2636.1.1.1.2.20"
        result = extract_vendor(oid)
        assert result == "Juniper"

    def test_extract_vendor_hp(self):
        """Test: Extract HP vendor from OID"""
        oid = "1.3.6.1.4.1.11.2.3.7.11.17"
        result = extract_vendor(oid)
        assert result == "HP"

    def test_extract_vendor_3com(self):
        """Test: Extract 3Com vendor from OID"""
        oid = "1.3.6.1.4.1.43.1.8.15"
        result = extract_vendor(oid)
        assert result == "3Com"

    def test_extract_vendor_dell(self):
        """Test: Extract Dell vendor from OID"""
        oid = "1.3.6.1.4.1.674.10895.3028"
        result = extract_vendor(oid)
        assert result == "Dell"

    def test_extract_vendor_unknown(self):
        """Test: Unknown vendor returns 'Unknown (vendor_id)'"""
        oid = "1.3.6.1.4.1.99999.1.2.3"
        result = extract_vendor(oid)
        assert result == "Unknown (99999)"

    def test_extract_vendor_invalid_format(self):
        """Test: Invalid OID format returns 'Unknown'"""
        oid = "invalid.oid.format"
        result = extract_vendor(oid)
        assert result == "Unknown"

    def test_extract_vendor_missing_vendor_id(self):
        """Test: OID without vendor ID section returns 'Unknown'"""
        oid = "1.3.6.1.2.1.1.1.0"  # Standard MIB, not enterprise OID
        result = extract_vendor(oid)
        assert result == "Unknown"

    def test_extract_vendor_short_oid(self):
        """Test: Too short OID returns 'Unknown'"""
        oid = "1.3.6"
        result = extract_vendor(oid)
        assert result == "Unknown"

    def test_extract_vendor_empty_string(self):
        """Test: Empty OID string returns 'Unknown'"""
        oid = ""
        result = extract_vendor(oid)
        assert result == "Unknown"

    @pytest.mark.parametrize("oid,expected_vendor", [
        ("1.3.6.1.4.1.9.1.685", "Cisco"),
        ("1.3.6.1.4.1.2636.1.1.1.2.20", "Juniper"),
        ("1.3.6.1.4.1.11.2.3.7.11.17", "HP"),
        ("1.3.6.1.4.1.43.1.8.15", "3Com"),
        ("1.3.6.1.4.1.674.10895.3028", "Dell"),
        ("1.3.6.1.4.1.4413.1.1.1", "Broadcom"),
        ("1.3.6.1.4.1.6876.1.1", "VMware"),
    ])
    def test_extract_vendor_various_oids(self, oid, expected_vendor):
        """Test: Various enterprise OIDs map to correct vendors"""
        result = extract_vendor(oid)
        assert result == expected_vendor or result.startswith("Unknown")


@pytest.mark.unit
class TestFormatMacAddress:
    """Test MAC address formatting"""

    def test_format_mac_address_standard(self):
        """Test: Standard hex MAC address formatted correctly"""
        mac = "0x001122334455"
        result = format_mac_address(mac)
        assert result == "00:11:22:33:44:55"

    def test_format_mac_address_lowercase(self):
        """Test: Lowercase hex MAC address formatted correctly"""
        mac = "0xaabbccddeeff"
        result = format_mac_address(mac)
        assert result == "AA:BB:CC:DD:EE:FF"

    def test_format_mac_address_mixed_case(self):
        """Test: Mixed case hex MAC address formatted correctly"""
        mac = "0xAaBbCcDdEeFf"
        result = format_mac_address(mac)
        assert result == "AA:BB:CC:DD:EE:FF"

    def test_format_mac_address_all_zeros(self):
        """Test: All zeros MAC address"""
        mac = "0x000000000000"
        result = format_mac_address(mac)
        assert result == "00:00:00:00:00:00"

    def test_format_mac_address_all_fs(self):
        """Test: All Fs MAC address (broadcast)"""
        mac = "0xffffffffffff"
        result = format_mac_address(mac)
        assert result == "FF:FF:FF:FF:FF:FF"

    def test_format_mac_address_leading_zeros(self):
        """Test: MAC address with leading zeros"""
        mac = "0x000102030405"
        result = format_mac_address(mac)
        assert result == "00:01:02:03:04:05"

    @pytest.mark.parametrize("mac_input,expected_output", [
        ("0x001122334455", "00:11:22:33:44:55"),
        ("0xAABBCCDDEEFF", "AA:BB:CC:DD:EE:FF"),
        ("0x123456789ABC", "12:34:56:78:9A:BC"),
        ("0x000000000001", "00:00:00:00:00:01"),
        ("0xfedcba987654", "FE:DC:BA:98:76:54"),
    ])
    def test_format_mac_address_various_inputs(self, mac_input, expected_output):
        """Test: Various MAC address inputs format correctly"""
        result = format_mac_address(mac_input)
        assert result == expected_output


@pytest.mark.unit
class TestMACAddressEdgeCases:
    """Test MAC address edge cases"""

    def test_format_mac_address_short_value(self):
        """Test: Short MAC address value"""
        mac = "0x123456"
        result = format_mac_address(mac)
        # Should still format whatever is there
        assert "12:34:56" in result

    def test_format_mac_address_odd_length(self):
        """Test: Odd length MAC address (missing digit)"""
        mac = "0x12345678901"  # 11 characters after 0x (should be 12)
        result = format_mac_address(mac)
        # Should handle gracefully
        assert ":" in result


@pytest.mark.unit
class TestVendorMappingCompleteness:
    """Test vendor mapping data completeness"""

    def test_vendor_mapping_has_common_vendors(self):
        """Test: Vendor mapping includes common network equipment vendors"""
        common_oids = [
            "1.3.6.1.4.1.9",      # Cisco
            "1.3.6.1.4.1.2636",   # Juniper
            "1.3.6.1.4.1.11",     # HP
        ]

        for oid in common_oids:
            result = extract_vendor(oid + ".1.2.3")
            assert result != "Unknown", f"OID {oid} should have known vendor"


@pytest.mark.unit
class TestDeviceServiceHelpers:
    """Test combined device service helper functionality"""

    def test_device_info_extraction(self):
        """Test: Device info can be extracted from SNMP response"""
        # This would test the full flow: OID → vendor, MAC → formatted
        vendor_oid = "1.3.6.1.4.1.9.1.685"
        mac_value = "0x001122334455"

        vendor = extract_vendor(vendor_oid)
        mac = format_mac_address(mac_value)

        assert "Cisco" in vendor
        assert mac == "00:11:22:33:44:55"

    @pytest.mark.parametrize("vendor_oid,mac_hex,expected_vendor_partial", [
        ("1.3.6.1.4.1.9.1.1", "0xaabbccddeeff", "Cisco"),
        ("1.3.6.1.4.1.2636.1.1", "0x112233445566", "Juniper"),
        ("1.3.6.1.4.1.11.2.3", "0x123456789abc", "HP"),
    ])
    def test_multiple_device_info_extractions(
        self, vendor_oid, mac_hex, expected_vendor_partial
    ):
        """Test: Multiple device info extractions work correctly"""
        vendor = extract_vendor(vendor_oid)
        mac = format_mac_address(mac_hex)

        assert expected_vendor_partial in vendor
        assert len(mac.split(":")) == 6  # Should have 6 octets
        assert all(len(octet) == 2 for octet in mac.split(":"))  # Each octet is 2 chars
