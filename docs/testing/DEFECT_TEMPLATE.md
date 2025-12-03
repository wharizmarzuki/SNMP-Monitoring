# Defect Report Template

**Use this template when creating GitHub Issues for bugs found during testing.**

---

## Bug Report

**Title**: [BUG] Brief description of the issue

### Classification

| Field | Value |
|-------|-------|
| **Severity** | Critical / High / Medium / Low |
| **Priority** | P0 / P1 / P2 / P3 |
| **Component** | Backend Service / API / Frontend / Database / Security |
| **Test Case** | TC-XXX-NNN (if applicable) |
| **Found In** | Version/Branch |
| **Environment** | Development / Staging / Production |

### Description

**Brief Summary**:
Clear, one-sentence description of the defect.

**Detailed Description**:
Provide detailed explanation of what went wrong, including:
- What functionality is affected
- Impact on users/system
- Any error messages or stack traces

### Steps to Reproduce

1. Step 1
2. Step 2
3. Step 3
4. ...

**Frequency**: Always / Sometimes / Rarely (X out of Y attempts)

### Expected vs Actual Behavior

**Expected Behavior**:
What should happen according to requirements/specifications.

**Actual Behavior**:
What actually happens.

### Test Environment

| Item | Details |
|------|---------|
| **Operating System** | Linux / macOS / Windows + version |
| **Python Version** | 3.12.x |
| **Node Version** | 18.x (if frontend) |
| **Browser** | Chrome / Firefox / Edge + version (if frontend) |
| **Database** | SQLite / PostgreSQL |
| **Redis** | Enabled / Disabled |

### Evidence

**Screenshots**:
[Attach screenshots if UI bug]

**Logs**:
```
[Paste relevant log output]
```

**Stack Trace**:
```
[Paste full stack trace if exception]
```

**Test Output**:
```bash
# Paste pytest output
```

### Additional Context

- Related issues: #123, #456
- Workaround (if any):
- Additional notes:

---

## Severity Definitions

| Severity | Definition | Examples |
|----------|-----------|----------|
| **Critical** | System unusable, data loss, security breach | - Authentication bypass<br>- Database corruption<br>- Production outage |
| **High** | Major functionality broken, no workaround | - SNMP polling stopped<br>- Alerts not triggering<br>- Dashboard not loading |
| **Medium** | Functionality impaired, workaround exists | - Threshold update fails<br>- Slow response times<br>- Chart rendering issues |
| **Low** | Minor issue, cosmetic, enhancement | - UI misalignment<br>- Typo<br>- Logging verbosity |

## Priority Definitions

| Priority | Definition | Resolution Target |
|----------|-----------|------------------|
| **P0** | Must fix before release | 24 hours |
| **P1** | Should fix before release | 3 days |
| **P2** | Fix in next release | 7 days |
| **P3** | Fix when convenient | Next sprint |

---

## Example Defect Reports

### Example 1: Critical Security Issue

```markdown
**Title**: [BUG] SQL Injection vulnerability in device search

**Severity**: Critical
**Priority**: P0
**Component**: Backend API
**Test Case**: TC-SEC-001
**Found In**: v1.0.0-rc1
**Environment**: Staging

**Description**:
SQL injection vulnerability allows unauthorized database access through
device search endpoint. Attacker can retrieve all user credentials.

**Steps to Reproduce**:
1. POST /device/search
2. Body: `{"query": "'; DROP TABLE users; --"}`
3. Observe database modification

**Expected**: Query sanitized, error returned
**Actual**: SQL executed, table dropped

**Environment**:
- OS: Ubuntu 22.04
- Python: 3.12.0
- Database: SQLite 3.40.0

**Evidence**:
Stack Trace:
```
sqlite3.OperationalError: no such table: users
```

**Additional Context**:
OWASP Top 10 - Injection vulnerability
Requires immediate hotfix
```

---

### Example 2: High Priority Functional Bug

```markdown
**Title**: [BUG] Alert not triggered when CPU exceeds threshold

**Severity**: High
**Priority**: P0
**Component**: Alert Service
**Test Case**: TC-ALERT-001
**Found In**: develop branch (commit abc123)
**Environment**: Development

**Description**:
CPU threshold breach does not trigger alert state transition.
Device remains in "clear" state despite CPU > threshold.

**Steps to Reproduce**:
1. Create device with CPU threshold = 80%
2. Poll device, receive CPU = 85%
3. Run alert check service
4. Check device.cpu_alert_state

**Frequency**: Always (10/10 attempts)

**Expected**: device.cpu_alert_state = "triggered"
**Actual**: device.cpu_alert_state = "clear"

**Environment**:
- OS: macOS 14.0
- Python: 3.12.0
- Database: SQLite in-memory (test)

**Evidence**:
Test Output:
```bash
FAILED tests/unit/test_alert_service.py::TestAlertService::test_cpu_threshold_breach
AssertionError: assert 'clear' == 'triggered'
```

**Additional Context**:
- Alert service logs show threshold comparison logic not executing
- Suspect issue in `alert_service.py:_check_cpu_threshold()`
- Blocking 3 other test cases
```

---

### Example 3: Medium Priority UI Bug

```markdown
**Title**: [BUG] Dashboard chart not rendering on mobile devices

**Severity**: Medium
**Priority**: P1
**Component**: Frontend
**Test Case**: TC-COMP-002
**Found In**: v1.0.0
**Environment**: Production

**Description**:
Network summary chart on dashboard does not render on mobile
devices (screen width < 768px). Chart area shows blank white space.

**Steps to Reproduce**:
1. Open dashboard on mobile device or resize browser to < 768px
2. Scroll to "Network Summary" section
3. Observe chart area

**Frequency**: Always on mobile, never on desktop

**Expected**: Chart renders responsively, scaled to fit screen
**Actual**: Blank white space, no chart visible

**Environment**:
- Browser: Chrome Mobile 120.0
- Device: iPhone 13, Samsung Galaxy S21
- Screen width: 375px - 412px

**Evidence**:
Screenshot: [Attach screenshot showing blank chart area]

Browser Console:
```
TypeError: Cannot read property 'width' of null at Chart.render()
```

**Additional Context**:
- Desktop rendering works perfectly
- Suspect Recharts library responsive config issue
- Workaround: View on desktop
- Affects ~30% of users (mobile traffic)
```

---

### Example 4: Low Priority Cosmetic Issue

```markdown
**Title**: [BUG] Typo in alert email subject line

**Severity**: Low
**Priority**: P2
**Component**: Email Service
**Test Case**: N/A (found during manual testing)
**Found In**: v1.0.0
**Environment**: All

**Description**:
Email subject for CPU alerts contains typo: "Devce CPU Alert"
instead of "Device CPU Alert".

**Steps to Reproduce**:
1. Trigger CPU alert
2. Check received email subject line

**Expected**: "Device CPU Alert - 192.168.1.1"
**Actual**: "Devce CPU Alert - 192.168.1.1"

**Environment**:
- All environments

**Evidence**:
Code location: `services/email_service.py:45`
```python
subject = f"Devce CPU Alert - {device.ip_address}"
```

**Additional Context**:
- Simple typo fix
- Low priority, does not affect functionality
- Can be fixed in next release
```

---

## Defect Workflow

```
┌─────────┐
│ Found   │ Tester discovers bug during testing
└────┬────┘
     │
     v
┌─────────┐
│ Reported│ GitHub Issue created using this template
└────┬────┘
     │
     v
┌─────────┐
│ Triaged │ Test Lead assigns Severity/Priority
└────┬────┘
     │
     v
┌─────────┐
│ Assigned│ Developer assigned, work begins
└────┬────┘
     │
     v
┌─────────┐
│ Fixed   │ Code merged, fix deployed to test environment
└────┬────┘
     │
     v
┌─────────┐
│ Verified│ Tester confirms fix resolves issue
└────┬────┘
     │
     v
┌─────────┐
│ Closed  │ Issue closed with resolution notes
└─────────┘
```

---

## GitHub Issue Labels

Use these labels when creating issues:

| Label | Usage |
|-------|-------|
| `bug` | All defect reports |
| `critical` | Severity: Critical |
| `high-priority` | Priority: P0 |
| `medium-priority` | Priority: P1 |
| `low-priority` | Priority: P2/P3 |
| `backend` | Backend service/API bug |
| `frontend` | UI/Frontend bug |
| `security` | Security vulnerability |
| `performance` | Performance issue |
| `test-failure` | Test is failing |
| `flaky-test` | Intermittent test failure |
| `blocked` | Cannot proceed, dependency issue |
| `needs-investigation` | Root cause unclear |

---

**Document End**
