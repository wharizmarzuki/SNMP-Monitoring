# Test Cases
**SNMP Network Monitoring System**

---

## Document Information

| Field | Details |
|-------|---------|
| **Document Name** | Test Cases - SNMP Monitoring System |
| **Reference Number** | TC-SNMP-001 |
| **Version** | 1.0.0 |
| **Last Updated** | 2025-12-02 |
| **Related Documents** | [Test Plan](TEST_PLAN.md) |

---

## Table of Contents

1. [Test Case Template](#test-case-template)
2. [Backend Service Tests](#backend-service-tests)
   - [SNMP Service Tests](#snmp-service-tests)
   - [Discovery Service Tests](#discovery-service-tests)
   - [Polling Service Tests](#polling-service-tests)
   - [Alert Service Tests](#alert-service-tests)
   - [Email Service Tests](#email-service-tests)
   - [Device Service Tests](#device-service-tests)
3. [API Integration Tests](#api-integration-tests)
   - [Authentication Tests](#authentication-tests)
   - [Device Management Tests](#device-management-tests)
   - [Alert Management Tests](#alert-management-tests)
   - [Query Endpoint Tests](#query-endpoint-tests)
4. [Frontend Tests](#frontend-tests)
   - [Component Tests](#component-tests)
   - [End-to-End Tests](#end-to-end-tests)
5. [Non-Functional Tests](#non-functional-tests)
   - [Performance Tests](#performance-tests)
   - [Security Tests](#security-tests)
   - [Reliability Tests](#reliability-tests)

---

## Test Case Template

```markdown
### TC-XXX-NNN: [Test Case Title]

**Test ID**: TC-XXX-NNN
**Requirement**: REQ-XXX
**Priority**: P0/P1/P2/P3
**Test Type**: Unit/Integration/E2E/Performance/Security
**Status**: ✅ Pass / ❌ Fail / ⏳ Pending / 🚫 Blocked

**Objective**: Brief description of what this test validates

**Preconditions**:
- Condition 1
- Condition 2

**Test Steps**:
1. Step 1
2. Step 2
3. Step 3

**Expected Result**:
- Expected outcome 1
- Expected outcome 2

**Actual Result**: (Fill during execution)

**Test Data**:
- Input data or fixtures used

**Notes**: Any additional information
```

---

## Backend Service Tests

### SNMP Service Tests

#### TC-SNMP-001: SNMP GET Query Success

**Test ID**: TC-SNMP-001
**Requirement**: REQ-002
**Priority**: P0
**Test Type**: Unit
**Status**: ⏳ Pending
**Location**: `backend/tests/unit/test_snmp_service.py::TestSNMPService::test_get_query_success`

**Objective**: Verify that SNMP GET query returns correct value for a valid OID

**Preconditions**:
- Mock SNMP device available
- Valid OID (e.g., `1.3.6.1.2.1.1.1.0` for sysDescr)

**Test Steps**:
1. Create SNMPClient instance
2. Call `get(host="192.168.1.1", oids=["1.3.6.1.2.1.1.1.0"])`
3. Parse response

**Expected Result**:
- Response contains `success: True`
- Data array has one element
- Value is a non-empty string
- No errors or exceptions

**Test Data**:
- Host: `192.168.1.1`
- OID: `1.3.6.1.2.1.1.1.0` (sysDescr)
- Mocked response: `"Cisco IOS Software, Version 15.2"`

---

#### TC-SNMP-002: SNMP GET Query Timeout

**Test ID**: TC-SNMP-002
**Requirement**: REQ-002
**Priority**: P0
**Test Type**: Unit
**Status**: ⏳ Pending
**Location**: `backend/tests/unit/test_snmp_service.py::TestSNMPService::test_get_query_timeout`

**Objective**: Verify that SNMP GET query handles timeout gracefully

**Preconditions**:
- Mock SNMP device simulating timeout
- Timeout set to 1 second

**Test Steps**:
1. Create SNMPClient with `timeout=1`
2. Mock asyncio.TimeoutError
3. Call `get(host="192.168.1.99", oids=["1.3.6.1.2.1.1.1.0"])`

**Expected Result**:
- Returns `None` (no exception raised)
- No partial data returned
- Graceful handling

**Test Data**:
- Host: `192.168.1.99` (unreachable)
- Timeout: 1 second

---

#### TC-SNMP-003: SNMP Bulk Walk Success

**Test ID**: TC-SNMP-003
**Requirement**: REQ-002
**Priority**: P1
**Test Type**: Unit
**Status**: ⏳ Pending
**Location**: `backend/tests/unit/test_snmp_service.py::TestSNMPService::test_bulk_walk_success`

**Objective**: Verify bulk walk retrieves multiple OID values

**Preconditions**:
- Mock SNMP device with multiple interfaces
- OID for interface table

**Test Steps**:
1. Create SNMPClient instance
2. Call `bulk_walk(host="192.168.1.1", oids=["1.3.6.1.2.1.2.2.1.2"])`
3. Verify multiple results returned

**Expected Result**:
- Response contains multiple interface names
- All values are strings
- No duplicate entries

**Test Data**:
- Host: `192.168.1.1`
- OID: `1.3.6.1.2.1.2.2.1.2` (ifDescr table)
- Expected: `["GigabitEthernet0/0", "GigabitEthernet0/1", "Vlan1"]`

---

### Discovery Service Tests

#### TC-DISC-001: Network Discovery Success

**Test ID**: TC-DISC-001
**Requirement**: REQ-001
**Priority**: P0
**Test Type**: Unit
**Status**: ⏳ Pending
**Location**: `backend/tests/unit/test_discovery_service.py::TestDiscoveryService::test_network_discovery_success`

**Objective**: Verify network discovery scans CIDR range and finds devices

**Preconditions**:
- Mock SNMP responses for 3 devices in range
- Network: `192.168.1.0/29` (8 IPs)

**Test Steps**:
1. Create DiscoveryService instance
2. Call `discover_network(network="192.168.1.0/29")`
3. Wait for completion
4. Check discovered devices

**Expected Result**:
- 3 devices discovered
- Each device has: ip, hostname, mac, vendor
- Devices inserted into database
- Discovery completes within 10 seconds

**Test Data**:
- Network: `192.168.1.0/29`
- Responsive IPs: `192.168.1.1`, `192.168.1.2`, `192.168.1.5`

---

#### TC-DISC-002: Device Deduplication by MAC

**Test ID**: TC-DISC-002
**Requirement**: REQ-001
**Priority**: P1
**Test Type**: Unit
**Status**: ⏳ Pending
**Location**: `backend/tests/unit/test_discovery_service.py::TestDiscoveryService::test_device_deduplication`

**Objective**: Verify existing device (by MAC) is updated, not duplicated

**Preconditions**:
- Device with MAC `00:11:22:33:44:55` exists at `192.168.1.1`
- Same device now at `192.168.1.10` (DHCP change)

**Test Steps**:
1. Insert device with MAC `00:11:22:33:44:55` at `192.168.1.1`
2. Run discovery, find same MAC at `192.168.1.10`
3. Check database

**Expected Result**:
- Only 1 device in database
- IP updated to `192.168.1.10`
- MAC remains `00:11:22:33:44:55`
- Other fields updated

**Test Data**:
- Original: IP=`192.168.1.1`, MAC=`00:11:22:33:44:55`
- Updated: IP=`192.168.1.10`, MAC=`00:11:22:33:44:55`

---

### Polling Service Tests

#### TC-POLL-001: Scheduled Polling Execution

**Test ID**: TC-POLL-001
**Requirement**: REQ-002
**Priority**: P0
**Test Type**: Unit
**Status**: ⏳ Pending
**Location**: `backend/tests/unit/test_polling_service.py::TestPollingService::test_scheduled_polling`

**Objective**: Verify polling service collects metrics on schedule

**Preconditions**:
- 2 devices in database
- Polling interval: 5 seconds (for test)

**Test Steps**:
1. Start polling service with 5s interval
2. Wait 10 seconds
3. Check metrics table
4. Stop polling

**Expected Result**:
- Metrics collected for both devices
- 2 polling cycles executed (approx)
- Metrics include: CPU, memory, uptime
- No errors logged

**Test Data**:
- Devices: `192.168.1.1`, `192.168.1.2`
- Interval: 5 seconds

---

#### TC-POLL-002: Polling with Unreachable Device

**Test ID**: TC-POLL-002
**Requirement**: REQ-002
**Priority**: P0
**Test Type**: Unit
**Status**: ⏳ Pending
**Location**: `backend/tests/unit/test_polling_service.py::TestPollingService::test_polling_unreachable_device`

**Objective**: Verify polling handles unreachable devices gracefully

**Preconditions**:
- Device exists but SNMP is unreachable

**Test Steps**:
1. Mock SNMP timeout for device
2. Execute polling cycle
3. Check device reachability status

**Expected Result**:
- Device marked as `is_reachable=False`
- No metrics inserted for unreachable device
- Polling continues for other devices
- No exceptions raised

**Test Data**:
- Device: `192.168.1.99` (unreachable)

---

### Alert Service Tests

#### TC-ALERT-001: CPU Alert Triggering

**Test ID**: TC-ALERT-001
**Requirement**: REQ-003
**Priority**: P0
**Test Type**: Unit
**Status**: ✅ Pass (Integration test exists)
**Location**: `backend/tests/integration/test_alerts.py::TestAlertWorkflow::test_alert_state_transitions`

**Objective**: Verify alert triggers when CPU exceeds threshold

**Preconditions**:
- Device with CPU threshold = 80%
- Current CPU = 50%

**Test Steps**:
1. Update device CPU to 85%
2. Run alert check logic
3. Verify alert state

**Expected Result**:
- Alert state changes from `clear` to `triggered`
- Alert timestamp recorded
- Email notification queued
- Device `cpu_alert_state` = `triggered`

**Test Data**:
- Threshold: 80%
- Current CPU: 85%

---

#### TC-ALERT-002: Alert State Transition Complete Flow

**Test ID**: TC-ALERT-002
**Requirement**: REQ-003
**Priority**: P0
**Test Type**: Unit
**Status**: ✅ Pass (Integration test exists)
**Location**: `backend/tests/integration/test_alerts.py`

**Objective**: Verify complete alert lifecycle: clear → triggered → acknowledged → clear

**Preconditions**:
- Device with CPU threshold = 80%

**Test Steps**:
1. Set CPU to 85% (trigger)
2. Acknowledge alert via API
3. Set CPU to 70% (resolve)
4. Resolve alert via API

**Expected Result**:
- State transitions: `clear` → `triggered` → `acknowledged` → `clear`
- Timestamps recorded for each transition
- Email sent on trigger
- Final state is `clear`

**Test Data**:
- Threshold: 80%
- Trigger value: 85%
- Clear value: 70%

---

### Email Service Tests

#### TC-EMAIL-001: Email Sending Success

**Test ID**: TC-EMAIL-001
**Requirement**: REQ-004
**Priority**: P1
**Test Type**: Unit
**Status**: ⏳ Pending
**Location**: `backend/tests/unit/test_email_service.py::TestEmailService::test_send_email_success`

**Objective**: Verify email is sent successfully via SMTP

**Preconditions**:
- Mock SMTP server available
- Valid recipient email

**Test Steps**:
1. Create EmailService instance
2. Call `send_alert_email(to="admin@example.com", subject="Test", body="Alert")`
3. Verify SMTP interaction

**Expected Result**:
- Email sent to SMTP server
- No exceptions raised
- Return value indicates success
- Correct headers (From, To, Subject)

**Test Data**:
- Recipient: `admin@example.com`
- Subject: `Test Alert`
- Body: `Device 192.168.1.1 CPU > 80%`

---

#### TC-EMAIL-002: Email Sending SMTP Failure

**Test ID**: TC-EMAIL-002
**Requirement**: REQ-004
**Priority**: P1
**Test Type**: Unit
**Status**: ⏳ Pending
**Location**: `backend/tests/unit/test_email_service.py::TestEmailService::test_send_email_smtp_failure`

**Objective**: Verify email service handles SMTP failures gracefully

**Preconditions**:
- Mock SMTP connection failure

**Test Steps**:
1. Create EmailService instance
2. Mock SMTP to raise connection error
3. Call `send_alert_email(...)`

**Expected Result**:
- Exception caught and logged
- Return value indicates failure
- No system crash
- Error message logged

**Test Data**:
- SMTP Error: `ConnectionRefusedError`

---

### Device Service Tests

#### TC-DEV-001: Create Device Success

**Test ID**: TC-DEV-001
**Requirement**: REQ-006
**Priority**: P0
**Test Type**: Unit
**Status**: ⏳ Pending
**Location**: `backend/tests/unit/test_device_service.py::TestDeviceService::test_create_device_success`

**Objective**: Verify device creation with valid data

**Preconditions**:
- Empty database
- Valid device info

**Test Steps**:
1. Create DeviceRepository instance
2. Call `create_device(device_info)` with valid data
3. Query database

**Expected Result**:
- Device inserted successfully
- ID auto-generated
- MAC address formatted correctly (`XX:XX:XX:XX:XX:XX`)
- Vendor extracted from OID
- Default thresholds applied

**Test Data**:
```python
DeviceInfo(
    hostname="router-1",
    ip_address="192.168.1.1",
    mac_address="0x001122334455",
    vendor="1.3.6.1.4.1.9",  # Cisco
    priority="high"
)
```

---

#### TC-DEV-002: Extract Vendor from OID

**Test ID**: TC-DEV-002
**Requirement**: REQ-006
**Priority**: P1
**Test Type**: Unit
**Status**: ⏳ Pending
**Location**: `backend/tests/unit/test_device_service.py::TestDeviceService::test_extract_vendor`

**Objective**: Verify vendor name extracted from SNMP OID

**Preconditions**:
- Known vendor OIDs

**Test Steps**:
1. Call `extract_vendor("1.3.6.1.4.1.9.x.x.x")`
2. Verify vendor name

**Expected Result**:
- Returns `"Cisco"`

**Test Data**:
| OID | Expected Vendor |
|-----|----------------|
| `1.3.6.1.4.1.9` | Cisco |
| `1.3.6.1.4.1.2636` | Juniper |
| `1.3.6.1.4.1.43` | 3Com |
| `1.3.6.1.4.1.99999` | Unknown (99999) |

---

## API Integration Tests

### Authentication Tests

#### TC-AUTH-001: Login with Valid Credentials

**Test ID**: TC-AUTH-001
**Requirement**: REQ-005
**Priority**: P0
**Test Type**: Integration
**Status**: ✅ Pass
**Location**: `backend/tests/integration/test_auth.py::TestAuthenticationFlow::test_login_with_valid_credentials_returns_token`

**Objective**: Verify user can login with correct username/password

**Preconditions**:
- User exists: `username=testuser, password=testpass`

**Test Steps**:
1. POST `/auth/login` with valid credentials
2. Parse response

**Expected Result**:
- HTTP 200 OK
- Response contains `access_token`
- Token is valid JWT
- Token type is `bearer`

**Test Data**:
```json
{
  "username": "testuser",
  "password": "testpass"
}
```

---

#### TC-AUTH-002: Protected Endpoint Requires Token

**Test ID**: TC-AUTH-002
**Requirement**: REQ-005
**Priority**: P0
**Test Type**: Integration
**Status**: ✅ Pass
**Location**: `backend/tests/integration/test_auth.py::TestAuthenticationFlow::test_protected_endpoint_without_token_blocked`

**Objective**: Verify protected endpoints reject requests without token

**Preconditions**:
- None

**Test Steps**:
1. GET `/device/` without Authorization header
2. Check response

**Expected Result**:
- HTTP 403 Forbidden
- No device data returned

**Test Data**:
- No authorization header

---

### Device Management Tests

#### TC-DEVICE-001: Get All Devices

**Test ID**: TC-DEVICE-001
**Requirement**: REQ-006
**Priority**: P0
**Test Type**: Integration
**Status**: ✅ Pass
**Location**: `backend/tests/integration/test_devices.py::TestDeviceEndpoints::test_get_all_devices`

**Objective**: Verify GET /device/ returns all devices

**Preconditions**:
- 5 devices in database

**Test Steps**:
1. GET `/device/`
2. Parse JSON response

**Expected Result**:
- HTTP 200 OK
- Array of 5 devices
- Each device has: ip_address, hostname, vendor, is_reachable

**Test Data**:
- 5 sample devices from fixture

---

#### TC-DEVICE-002: Update Device Thresholds

**Test ID**: TC-DEVICE-002
**Requirement**: REQ-007
**Priority**: P1
**Test Type**: Integration
**Status**: ✅ Pass
**Location**: `backend/tests/integration/test_devices.py::TestDeviceEndpoints::test_update_device_thresholds`

**Objective**: Verify device thresholds can be updated

**Preconditions**:
- Device exists at `192.168.1.100`

**Test Steps**:
1. PUT `/device/192.168.1.100/thresholds`
2. Body: `{"cpu_threshold": 75.0, "memory_threshold": 90.0}`
3. Verify update

**Expected Result**:
- HTTP 200 OK
- Thresholds updated in database
- Response reflects new values

**Test Data**:
```json
{
  "cpu_threshold": 75.0,
  "memory_threshold": 90.0,
  "failure_threshold": 5
}
```

---

## Frontend Tests

### Component Tests

#### TC-COMP-001: Dashboard Renders KPIs

**Test ID**: TC-COMP-001
**Requirement**: REQ-008
**Priority**: P0
**Test Type**: Component
**Status**: ⏳ Pending
**Location**: `frontend/src/components/__tests__/Dashboard.test.tsx::test_displays_network_summary_kpis`

**Objective**: Verify dashboard displays network summary KPIs

**Preconditions**:
- Mock API returns network summary

**Test Steps**:
1. Render `<Dashboard />` component
2. Wait for API call
3. Check DOM elements

**Expected Result**:
- "Total Devices" label visible
- "Devices Up" label visible
- "Devices Down" label visible
- "Devices in Alert" label visible
- Values displayed correctly

**Test Data**:
```json
{
  "total_devices": 10,
  "devices_up": 8,
  "devices_down": 2,
  "devices_in_alert": 3
}
```

---

### End-to-End Tests

#### TC-E2E-001: Login to Dashboard Workflow

**Test ID**: TC-E2E-001
**Requirement**: REQ-005, REQ-008
**Priority**: P0
**Test Type**: E2E
**Status**: ⏳ Pending
**Location**: `frontend/e2e/auth.spec.ts::test_user_can_login_and_access_dashboard`

**Objective**: Verify complete login flow and dashboard access

**Preconditions**:
- Backend running at `http://localhost:8000`
- Frontend running at `http://localhost:3000`
- Admin user exists

**Test Steps**:
1. Navigate to `http://localhost:3000`
2. Fill username field: `admin`
3. Fill password field: `password`
4. Click "Login" button
5. Wait for redirect

**Expected Result**:
- Redirected to `/dashboard`
- Dashboard page loads
- Network overview visible
- No JavaScript errors in console

**Test Data**:
- Username: `admin`
- Password: `password`

---

## Non-Functional Tests

### Performance Tests

#### TC-PERF-001: API Response Time Under Load

**Test ID**: TC-PERF-001
**Requirement**: Non-functional
**Priority**: P1
**Test Type**: Performance
**Status**: ⏳ Pending
**Location**: `backend/tests/performance/locustfile.py`

**Objective**: Verify API response times under 100 concurrent users

**Preconditions**:
- 100 devices in database
- Locust installed

**Test Steps**:
1. Start backend
2. Run: `locust -f locustfile.py --users 100 --spawn-rate 10`
3. Run for 5 minutes
4. Analyze results

**Expected Result**:
- 95th percentile response time < 200ms
- 99th percentile response time < 500ms
- Zero failed requests
- No memory leaks

**Test Data**:
- Users: 100
- Spawn rate: 10/sec
- Duration: 5 minutes

---

### Security Tests

#### TC-SEC-001: SQL Injection Protection

**Test ID**: TC-SEC-001
**Requirement**: Security
**Priority**: P0
**Test Type**: Security
**Status**: ⏳ Pending
**Location**: `backend/tests/security/test_security.py::TestSecurity::test_sql_injection_protection`

**Objective**: Verify SQL injection attempts are blocked

**Preconditions**:
- API running

**Test Steps**:
1. GET `/device/192.168.1.1'; DROP TABLE devices; --`
2. Check response

**Expected Result**:
- HTTP 400 or 404 (not 500)
- No database modification
- No error stack trace exposed

**Test Data**:
- Malicious input: `192.168.1.1'; DROP TABLE devices; --`

---

#### TC-SEC-002: JWT Token Tampering

**Test ID**: TC-SEC-002
**Requirement**: Security
**Priority**: P0
**Test Type**: Security
**Status**: ⏳ Pending
**Location**: `backend/tests/security/test_security.py::TestSecurity::test_jwt_tampering`

**Objective**: Verify tampered JWT tokens are rejected

**Preconditions**:
- Valid JWT token obtained

**Test Steps**:
1. Get valid token
2. Modify payload (change username)
3. GET `/device/` with tampered token

**Expected Result**:
- HTTP 401 Unauthorized
- No access granted

**Test Data**:
- Tampered token with username changed

---

## Test Execution Summary

| Category | Total | Implemented | Passing | Pending |
|----------|-------|-------------|---------|---------|
| **Unit Tests** | 20 | 0 | 0 | 20 |
| **Integration Tests** | 28 | 28 | 27 | 1 |
| **Component Tests** | 10 | 0 | 0 | 10 |
| **E2E Tests** | 5 | 0 | 0 | 5 |
| **Performance Tests** | 3 | 0 | 0 | 3 |
| **Security Tests** | 5 | 0 | 0 | 5 |
| **TOTAL** | **71** | **28** | **27** | **43** |

**Current Coverage**: 39% (28/71 tests implemented)
**Target Coverage**: 100% (71/71 tests implemented)

---

**Document End**
