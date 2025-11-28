# Network Connectivity Testing Guide

## 📋 Overview

This document provides comprehensive testing procedures to verify network connectivity in the GNS3 simulation.

---

## 🔌 Layer 1 & 2 Testing

### Test 1: Physical Link Status

**On each device, verify interfaces are up:**

```bash
# MAIN-RTR
MAIN-RTR# show ip interface brief

Interface              IP-Address      OK? Method Status                Protocol
FastEthernet0/0        DHCP            YES DHCP   up                    up
FastEthernet0/1        192.168.254.1   YES manual up                    up

# Expected: Status and Protocol both "up"
```

```bash
# CORE-SW
CORE-SW# show interfaces status

Port      Name               Status       Vlan       Duplex  Speed Type
Gi0/0     Uplink to MAIN-R   connected    trunk      auto    auto  10/100/1000BaseTX
Gi0/1     To ADMIN-SW        connected    trunk      auto    auto  10/100/1000BaseTX
Gi0/3     To LAB-SW1         connected    trunk      auto    auto  10/100/1000BaseTX
Gi1/0     To LIB-SW          connected    trunk      auto    auto  10/100/1000BaseTX

# Expected: All ports "connected"
```

**✅ PASS Criteria:**
- All connected interfaces show "up/up" status
- No interfaces in "down/down" state

---

### Test 2: CDP Neighbor Discovery

**Verify CDP neighbors are visible:**

```bash
# On MAIN-RTR
MAIN-RTR# show cdp neighbors

Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID
CORE-SW          Fas 0/1           150        S I         WS-C2960  Gig 0/0

# Expected: CORE-SW visible
```

```bash
# On CORE-SW
CORE-SW# show cdp neighbors

Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID
MAIN-RTR         Gig 0/0           175        R           CISCO3725 Fas 0/1
ADMIN-SW         Gig 0/1           142        S I         WS-C2960  Gig 0/0
LAB-SW1          Gig 0/3           158        S I         WS-C2960  Gig 0/0
LIB-SW           Gig 1/0           133        S I         WS-C2960  Eth 0/0

# Expected: All 4 neighbors visible
```

**✅ PASS Criteria:**
- All physical connections show CDP neighbors
- Device names match topology

---

### Test 3: Spanning Tree Verification

**Verify CORE-SW is root bridge:**

```bash
# On CORE-SW
CORE-SW# show spanning-tree summary

Switch is in rapid-pvst mode
Root bridge for: VLAN0001, VLAN0010, VLAN0020, VLAN0030, VLAN0040, VLAN0099
Extended system ID   : enabled
Portfast Default     : disabled
PortFast BPDU Guard Default: disabled

# Expected: Root bridge for all VLANs
```

**Verify other switches see CORE-SW as root:**

```bash
# On ADMIN-SW
ADMIN-SW# show spanning-tree root

                                        Root    Hello Max Fwd
Vlan                   Root ID          Cost    Time  Age Dly  Root Port
---------------- -------------------- --------- ----- --- ---  ------------
VLAN0010         4096 0011.2233.4455       4    2     20  15   Gi0/0
VLAN0099         4096 0011.2233.4455       4    2     20  15   Gi0/0

# Expected: Root port pointing to CORE-SW
```

**✅ PASS Criteria:**
- CORE-SW is root for all VLANs
- No blocking ports (in this tree topology)
- All switches converged to CORE-SW

---

## 🌐 Layer 3 Testing

### Test 4: ICMP Reachability from Router

**From MAIN-RTR, ping all management IPs:**

```bash
# MAIN-RTR testing
MAIN-RTR# ping 192.168.254.10
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 192.168.254.10, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms

MAIN-RTR# ping 192.168.254.20
!!!!!  # ADMIN-SW

MAIN-RTR# ping 192.168.254.25
!!!!!  # SERVER-SW

MAIN-RTR# ping 192.168.254.30
!!!!!  # LAB-SW1

MAIN-RTR# ping 192.168.254.31
!!!!!  # LAB-SW2

MAIN-RTR# ping 192.168.254.32
!!!!!  # LAB-SW3

MAIN-RTR# ping 192.168.254.40
!!!!!  # LIB-SW
```

**Automated Test Script:**

```bash
# Create test script on MAIN-RTR
MAIN-RTR# configure terminal
MAIN-RTR(config)# do for ip 10 20 25 30 31 32 40
MAIN-RTR(config)# do ping 192.168.254.$ip repeat 2
```

**✅ PASS Criteria:**
- All pings return "!!!!!" (100% success)
- Round-trip time < 10ms
- No timeouts or packet loss

---

### Test 5: Traceroute Path Verification

**Test routing path:**

```bash
# From MAIN-RTR to LAB-SW2 (should go through CORE-SW and LAB-SW1)
MAIN-RTR# traceroute 192.168.254.31

Type escape sequence to abort.
Tracing the route to 192.168.254.31
VRF info: (vrf in name/id, vrf out name/id)
  1 192.168.254.10 4 msec 4 msec *    # CORE-SW
  2 192.168.254.31 8 msec 4 msec 4 msec  # LAB-SW2

# Expected: 1-2 hops maximum
```

**✅ PASS Criteria:**
- Traceroute completes successfully
- Path goes through expected devices
- No routing loops

---

### Test 6: ARP Table Verification

**Check ARP entries:**

```bash
# On MAIN-RTR
MAIN-RTR# show ip arp

Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.254.1           -   aabb.cc00.0110  ARPA   FastEthernet0/1
Internet  192.168.254.10          2   aabb.cc00.0220  ARPA   FastEthernet0/1
Internet  192.168.254.20          5   aabb.cc00.0330  ARPA   FastEthernet0/1

# Expected: All directly connected devices visible
```

**Clear and refresh ARP:**

```bash
MAIN-RTR# clear ip arp
MAIN-RTR# ping 192.168.254.10
MAIN-RTR# show ip arp
# Should re-populate
```

**✅ PASS Criteria:**
- ARP entries for all reachable IPs
- MAC addresses resolved correctly

---

## 🔒 VLAN Testing

### Test 7: VLAN Configuration Verification

**On CORE-SW, verify all VLANs exist:**

```bash
CORE-SW# show vlan brief

VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active
10   ADMIN_STAFF                      active
20   STUDENT_LABS                     active
30   LIBRARY                          active
40   SERVERS                          active
99   MANAGEMENT                       active

# Expected: All 5 VLANs configured
```

**Verify VLAN on trunk ports:**

```bash
CORE-SW# show interfaces trunk

Port        Mode         Encapsulation  Status        Native vlan
Gi0/0       on           802.1q         trunking      99
Gi0/1       on           802.1q         trunking      99
Gi0/3       on           802.1q         trunking      99
Gi1/0       on           802.1q         trunking      99

Port        Vlans allowed on trunk
Gi0/0       10,20,30,40,99
Gi0/1       10,99
Gi0/3       20,99
Gi1/0       30,99

# Expected: Correct VLANs on each trunk
```

**✅ PASS Criteria:**
- All VLANs created on all switches
- Trunks allow correct VLANs
- No VLAN mismatches

---

### Test 8: VLAN Trunk Negotiation

**Verify trunk encapsulation:**

```bash
# On IOSvL2 switches
CORE-SW# show interfaces GigabitEthernet0/1 switchport

Name: Gi0/1
Switchport: Enabled
Administrative Mode: trunk
Operational Mode: trunk
Administrative Trunking Encapsulation: dot1q
Operational Trunking Encapsulation: dot1q
Negotiation of Trunking: Off

# Expected: dot1q encapsulation active
```

**✅ PASS Criteria:**
- All trunks using 802.1q
- Trunks operational
- No DTP negotiation issues

---

## 📡 SNMP Testing

### Test 9: SNMP Community Access

**From SNMP server:**

```bash
# Test SNMP v2c community access
snmpget -v2c -c public 192.168.254.1 1.3.6.1.2.1.1.5.0

# Expected:
SNMPv2-MIB::sysName.0 = STRING: MAIN-RTR

# Test incorrect community (should fail)
snmpget -v2c -c wrongcommunity 192.168.254.1 1.3.6.1.2.1.1.5.0

# Expected: Timeout (no response)
```

**Test all devices:**

```bash
# Test script
for ip in 192.168.254.{1,10,20,25,30,31,32,40}; do
    name=$(snmpget -v2c -c public -Oqv $ip 1.3.6.1.2.1.1.5.0 2>/dev/null)
    if [ -n "$name" ]; then
        echo "✓ $ip - $name - SNMP OK"
    else
        echo "✗ $ip - SNMP FAILED"
    fi
done
```

**Expected Output:**
```
✓ 192.168.254.1 - MAIN-RTR - SNMP OK
✓ 192.168.254.10 - CORE-SW - SNMP OK
✓ 192.168.254.20 - ADMIN-SW - SNMP OK
✓ 192.168.254.25 - SERVER-SW - SNMP OK
✓ 192.168.254.30 - LAB-SW1 - SNMP OK
✓ 192.168.254.31 - LAB-SW2 - SNMP OK
✓ 192.168.254.32 - LAB-SW3 - SNMP OK
✓ 192.168.254.40 - LIB-SW - SNMP OK
```

**✅ PASS Criteria:**
- All devices respond to SNMP queries
- Community string authentication works
- No SNMP timeouts

---

## 🚀 Performance Testing

### Test 10: Bandwidth Test (Optional)

**Using iperf between router and switch:**

```bash
# On SNMP server (iperf server)
iperf -s -p 5001

# On MAIN-RTR (if iperf available)
# Or from another GNS3 host
iperf -c 192.168.254.100 -p 5001 -t 10

# Expected: Gigabit speeds (800+ Mbps on GE interfaces)
```

**✅ PASS Criteria:**
- Throughput matches interface speed
- No packet loss during test
- Latency < 10ms

---

### Test 11: Load Testing

**Generate traffic and monitor:**

```bash
# On MAIN-RTR
MAIN-RTR# ping 192.168.254.40 repeat 10000

# While pinging, check interface stats
CORE-SW# show interfaces GigabitEthernet0/0 | include packets
  5 minute input rate 1000 bits/sec, 2 packets/sec
  5 minute output rate 1000 bits/sec, 2 packets/sec
  12345 packets input, 789000 bytes
  12346 packets output, 789100 bytes
```

**✅ PASS Criteria:**
- No interface errors
- No drops or overruns
- Consistent packet rates

---

## 📊 Comprehensive Test Matrix

### Complete Test Checklist

| Test # | Test Name | Target | Expected Result | Status |
|--------|-----------|--------|-----------------|--------|
| 1 | Physical Link Status | All devices | All interfaces up/up | [ ] |
| 2 | CDP Neighbors | All switches | All neighbors visible | [ ] |
| 3 | Spanning Tree | CORE-SW | Root bridge for all VLANs | [ ] |
| 4 | ICMP Reachability | MAIN-RTR → All | 100% ping success | [ ] |
| 5 | Traceroute | MAIN-RTR → LAB-SW2 | Correct path | [ ] |
| 6 | ARP Resolution | MAIN-RTR | All IPs in ARP table | [ ] |
| 7 | VLAN Configuration | All switches | All VLANs present | [ ] |
| 8 | Trunk Status | All trunks | 802.1q operational | [ ] |
| 9 | SNMP Access | SNMP Server → All | All respond to queries | [ ] |
| 10 | Bandwidth | Optional | Gigabit speeds | [ ] |
| 11 | Load Testing | Interfaces | No errors under load | [ ] |

---

## 🐛 Common Issues and Fixes

### Issue: Interface Down

**Symptoms:**
```bash
Interface Status: down
Protocol Status: down
```

**Fix:**
```bash
Router(config)# interface FastEthernet0/1
Router(config-if)# no shutdown
Router(config-if)# end
```

---

### Issue: No CDP Neighbors

**Symptoms:**
```bash
Router# show cdp neighbors
% CDP is not enabled
```

**Fix:**
```bash
Router(config)# cdp run
Router(config)# interface FastEthernet0/1
Router(config-if)# cdp enable
```

---

### Issue: VLAN Mismatch

**Symptoms:**
```
%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch
```

**Fix:**
```bash
# Ensure both ends use same native VLAN
Switch(config)# interface GigabitEthernet0/1
Switch(config-if)# switchport trunk native vlan 99
```

---

### Issue: Ping Fails

**Symptoms:**
```bash
.....
Success rate is 0 percent (0/5)
```

**Troubleshooting:**
```bash
# 1. Check interface status
show ip interface brief

# 2. Check routing
show ip route

# 3. Check ARP
show ip arp

# 4. Check for ACLs
show ip access-lists

# 5. Verify VLAN
show vlan brief
```

---

## 📈 Test Results Template

### Test Execution Log

```
Date: _______________
Tester: _______________
GNS3 Version: _______________

Test Results:
[ ] Layer 1/2 Tests Complete - All interfaces up
[ ] Layer 3 Tests Complete - All pings successful
[ ] VLAN Tests Complete - All VLANs configured
[ ] SNMP Tests Complete - All devices responding
[ ] Performance Tests Complete - No errors

Issues Found:
1. _______________
2. _______________

Resolution:
1. _______________
2. _______________

Sign-off: _______________
```

---

## ✅ Final Verification

**All systems operational when:**
- ✅ All 8 devices powered on and responsive
- ✅ All management IPs pingable (192.168.254.x)
- ✅ SNMP queries successful on all devices
- ✅ CDP neighbors visible on all connections
- ✅ Spanning tree converged to CORE-SW
- ✅ No interface errors or drops
- ✅ All VLANs created and trunking
- ✅ SNMP server can discover and poll all devices

**Network Ready for Monitoring! 🎉**

---

**Next Steps:**
- [SNMP Verification Tests](snmp-verification.md)
- [Acceptance Testing](acceptance-tests.md)
