# Cisco Switch OID Compatibility Report

## OID Mismatch Analysis and Recommended Replacements

| Category | Current OID | Purpose | Issue | Status | Recommended Replacement | Compatibility |
|----------|-------------|---------|-------|--------|------------------------|---------------|
| **CPU Monitoring** | `1.3.6.1.4.1.9.9.109.1.1.1.1.5.1` | cpmCPUTotal5min | Uses deprecated OID with limited range (0-100 but truncated) | ⚠️ **DEPRECATED** | `1.3.6.1.4.1.9.9.109.1.1.1.1.8.1` (cpmCPUTotal5minRev) | Full 0-100% range, better accuracy |
| **Memory Monitoring** | `1.3.6.1.4.1.9.9.48.1.1.1.5.1` | Memory Pool 1 (Free) | Works but using "free" instead of "used" | ✅ **OK** | `1.3.6.1.4.1.9.9.48.1.1.1.5.1` (Keep as-is) | Standard across Cisco devices |
| **Memory Monitoring** | `1.3.6.1.4.1.9.9.48.1.1.1.5.2` | Memory Pool 2 (Free) | Works but pool 2 may not exist on all switches | ⚠️ **VARIES** | Use only Pool 1, or walk to discover available pools | Pool 2 doesn't exist on all models |
| **Memory Monitoring** | `1.3.6.1.4.1.9.9.48.1.1.1.5.13` | Memory Pool 13 (Used) | Pool 13 doesn't exist on most switches | ❌ **FAILS** | `1.3.6.1.4.1.9.9.48.1.1.1.5.1` (ciscoMemoryPoolUsed for Pool 1) | Use Pool 1 "Used" metric instead |
| **Device Model** | `1.3.6.1.2.1.47.1.1.1.1.13.1` | entPhysicalModelName | Hardcoded index `.1` may not be chassis on all devices | ⚠️ **VARIES** | Walk `1.3.6.1.2.1.47.1.1.1.1.13` and filter by entPhysicalClass=3 (chassis) | More reliable across models |
| **Discovery** | `1.3.6.1.2.1.1.5.0` | sysName (hostname) | No issues | ✅ **OK** | No change needed | Universal support |
| **Discovery** | `1.3.6.1.2.1.2.2.1.6.1` | MAC Address | Hardcoded interface index `.1` | ⚠️ **VARIES** | Walk `1.3.6.1.2.1.2.2.1.6` to find first physical interface | More reliable |
| **Discovery** | `1.3.6.1.2.1.1.2.0` | sysObjectID (vendor) | No issues | ✅ **OK** | No change needed | Universal support |
| **Interfaces** | `1.3.6.1.2.1.2.2.1.*` | IF-MIB (all interface OIDs) | No issues | ✅ **OK** | No change needed | Universal IF-MIB support |

---

## Detailed Issue Breakdown

### 1. ❌ **CRITICAL: Memory Pool Configuration**

**Current Implementation** (`backend/services/polling_service.py:148-153`):
```python
pool_1 = float(vendor_data.get("memory_pool_1", 0))  # Free memory pool 1
pool_2 = float(vendor_data.get("memory_pool_2", 0))  # Free memory pool 2
used_mem = float(vendor_data.get("memory_pool_13", 0))  # Used memory pool 13
total_mem = pool_1 + pool_2
if total_mem > 0:
    mem_val = (used_mem / total_mem) * 100
```

**Problem:**
- Pool 13 doesn't exist on most Cisco Catalyst switches
- Pool 2 may not exist on some models
- This will result in `mem_val = 0` or incorrect calculations

**Recommended Fix:**
```python
# Option A: Use Pool 1 only (Processor Memory)
used_mem = float(vendor_data.get("memory_pool_1_used", 0))
free_mem = float(vendor_data.get("memory_pool_1_free", 0))
total_mem = used_mem + free_mem
if total_mem > 0:
    mem_val = (used_mem / total_mem) * 100

# Update VENDOR_OIDS to:
"memory_pool_1_used": "1.3.6.1.4.1.9.9.48.1.1.1.5.1",
"memory_pool_1_free": "1.3.6.1.4.1.9.9.48.1.1.1.6.1",
```

---

### 2. ⚠️ **WARNING: Deprecated CPU OID**

**Current Implementation** (`backend/app/core/schemas.py:138`):
```python
"cpu_utilization": "1.3.6.1.4.1.9.9.109.1.1.1.1.5.1",
```

**Problem:**
- `cpmCPUTotal5min` (.5) is deprecated
- Limited accuracy and range handling

**Recommended Fix:**
```python
# Use the revised version with full 0-100 range
"cpu_utilization": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1",  # cpmCPUTotal5minRev
```

**Alternative Options:**
| OID | Metric | Time Period | Status |
|-----|--------|-------------|--------|
| `1.3.6.1.4.1.9.9.109.1.1.1.1.6.1` | cpmCPUTotal5secRev | 5 seconds | ✅ Recommended for real-time |
| `1.3.6.1.4.1.9.9.109.1.1.1.1.7.1` | cpmCPUTotal1minRev | 1 minute | ✅ Good balance |
| `1.3.6.1.4.1.9.9.109.1.1.1.1.8.1` | cpmCPUTotal5minRev | 5 minutes | ✅ Most stable |

---

### 3. ⚠️ **WARNING: Hardcoded Indexes**

**Current Issues:**
1. **MAC Address Discovery** - Uses `.1` assuming first interface
2. **Model Name** - Uses `.1` assuming chassis is at index 1

**Recommended Approach:**
Instead of hardcoded indexes, use SNMP walk to discover:
- Walk interface table to find first physical interface
- Walk entPhysicalTable to find chassis entity

---

## Updated OID Configuration

### Recommended `VENDOR_OIDS` for Cisco:

```python
VENDOR_OIDS = {
    "Cisco": {
        # CPU - Use 5-minute revised version for stability
        "cpu_utilization": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1",

        # Memory - Pool 1 (Processor Memory) - Most compatible
        "memory_pool_used": "1.3.6.1.4.1.9.9.48.1.1.1.5.1",
        "memory_pool_free": "1.3.6.1.4.1.9.9.48.1.1.1.6.1",
    },
}
```

### Updated Memory Calculation Logic:

```python
# For Cisco devices
if vendor == "Cisco":
    used_mem = float(vendor_data.get("memory_pool_used", 0))
    free_mem = float(vendor_data.get("memory_pool_free", 0))
    total_mem = used_mem + free_mem
    if total_mem > 0:
        mem_val = (used_mem / total_mem) * 100
```

---

## Testing Commands

### Verify OID Support on Your Cisco Switch:

```bash
# Test CPU OIDs (current vs recommended)
snmpget -v2c -c public <switch-ip> 1.3.6.1.4.1.9.9.109.1.1.1.1.5.1  # Current (deprecated)
snmpget -v2c -c public <switch-ip> 1.3.6.1.4.1.9.9.109.1.1.1.1.8.1  # Recommended

# Test Memory OIDs (current configuration)
snmpget -v2c -c public <switch-ip> 1.3.6.1.4.1.9.9.48.1.1.1.5.1   # Pool 1 Free
snmpget -v2c -c public <switch-ip> 1.3.6.1.4.1.9.9.48.1.1.1.5.2   # Pool 2 Free (may not exist)
snmpget -v2c -c public <switch-ip> 1.3.6.1.4.1.9.9.48.1.1.1.5.13  # Pool 13 Used (likely fails)

# Test Memory OIDs (recommended configuration)
snmpget -v2c -c public <switch-ip> 1.3.6.1.4.1.9.9.48.1.1.1.5.1   # Pool 1 Used
snmpget -v2c -c public <switch-ip> 1.3.6.1.4.1.9.9.48.1.1.1.6.1   # Pool 1 Free

# Walk memory pools to see what's available
snmpwalk -v2c -c public <switch-ip> 1.3.6.1.4.1.9.9.48.1.1.1

# Walk CPU table
snmpwalk -v2c -c public <switch-ip> 1.3.6.1.4.1.9.9.109.1.1.1.1

# Test ENTITY-MIB model name
snmpget -v2c -c public <switch-ip> 1.3.6.1.2.1.47.1.1.1.1.13.1
snmpwalk -v2c -c public <switch-ip> 1.3.6.1.2.1.47.1.1.1.1.13
```

---

## Priority Fixes

### Priority 1 - Critical (Will cause failures):
1. ❌ Fix Memory Pool 13 issue - **will fail on most switches**

### Priority 2 - High (Should be updated):
2. ⚠️ Update CPU OID to non-deprecated version
3. ⚠️ Update memory calculation to use Pool 1 only

### Priority 3 - Medium (Nice to have):
4. ⚠️ Make MAC address discovery more robust
5. ⚠️ Make model name discovery more robust

---

## Compatibility Matrix

| Switch Model | Current Config Works? | With Recommended Changes |
|--------------|----------------------|--------------------------|
| Catalyst 2960 | ⚠️ Partial (CPU may work, Memory fails) | ✅ Full support |
| Catalyst 3750 | ⚠️ Partial (CPU varies, Memory fails) | ✅ Full support |
| Catalyst 9200 | ⚠️ Partial (Memory fails) | ✅ Full support |
| Catalyst 9300 | ⚠️ Partial (Memory fails) | ✅ Full support |
| Catalyst 9400 | ⚠️ Partial (Memory fails) | ✅ Full support |

---

## Implementation Files to Update

1. **`backend/app/core/schemas.py`** (Lines 136-143)
   - Update CPU OID from `.5.1` to `.8.1`
   - Replace memory pool OIDs

2. **`backend/services/polling_service.py`** (Lines 142-154)
   - Update memory calculation logic
   - Use single memory pool approach

---

## References

- [Cisco PROCESS-MIB Documentation](https://oidref.com/1.3.6.1.4.1.9.9.109)
- [Cisco MEMORY-POOL-MIB Documentation](https://oidref.com/1.3.6.1.4.1.9.9.48)
- [Collect CPU Utilization on Cisco IOS Devices](https://www.cisco.com/c/en/us/support/docs/ip/simple-network-management-protocol-snmp/15215-collect-cpu-util-snmp.html)
