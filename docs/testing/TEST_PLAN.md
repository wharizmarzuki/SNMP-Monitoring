# Test Plan
**SNMP Network Monitoring System**

---

## Document Control

| Field | Details |
|-------|---------|
| **Document Name** | Test Plan - SNMP Monitoring System |
| **Reference Number** | TP-SNMP-001 |
| **Version** | 1.0.0 |
| **Project Code** | SNMP-MON |
| **Status** | Active |
| **Date Released** | 2025-12-02 |

### Document Approval

| Role | Name | Position | Signature | Date |
|------|------|----------|-----------|------|
| **Prepared By** | Claude | Test Engineer | _________ | 2025-12-02 |
| **Reviewed By** | TBD | QA Lead | _________ | ________ |
| **Approved By** | TBD | Project Manager | _________ | ________ |

---

## Version History

| Version | Release Date | Section | Amendments |
|---------|-------------|---------|------------|
| 1.0.0 | 2025-12-02 | All | Initial creation - Complete test plan following IEEE 829 |

---

## Distribution List

| Version | Release Date | Copy No | Recipient Name | Department | Issue Date | Return Date |
|---------|-------------|---------|----------------|------------|------------|-------------|
| 1.0.0 | 2025-12-02 | 001 | Development Team | Engineering | 2025-12-02 | N/A |

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 [Purpose](#11-purpose)
   - 1.2 [Scope](#12-scope)
   - 1.3 [References](#13-references)
2. [Test Plans](#2-test-plans)
   - 2.1 [Test Items](#21-test-items)
   - 2.2 [Test Traceability Matrix](#22-test-traceability-matrix)
   - 2.3 [Features to be Tested](#23-features-to-be-tested)
   - 2.4 [Features Not to be Tested](#24-features-not-to-be-tested)
   - 2.5 [Test Approach or Test Strategy](#25-test-approach-or-test-strategy)
   - 2.6 [Item Pass/Fail Criteria](#26-item-passfail-criteria)
   - 2.7 [Suspension Criteria and Resumption Requirements](#27-suspension-criteria-and-resumption-requirements)
   - 2.8 [Test Deliverables](#28-test-deliverables)
   - 2.9 [Entry Criteria](#29-entry-criteria)
   - 2.10 [Exit Criteria](#210-exit-criteria)
3. [Test Management](#3-test-management)
   - 3.1 [Planned Tasks and Activities](#31-planned-tasks-and-activities)
   - 3.2 [Environment & Infrastructure](#32-environment--infrastructure)
   - 3.3 [Responsibility and Authority](#33-responsibility-and-authority)
   - 3.4 [Resources and Allocation](#34-resources-and-allocation)
   - 3.5 [Training](#35-training)
   - 3.6 [Schedules, Estimates and Costs](#36-schedules-estimates-and-costs)
   - 3.7 [Risk and Contingency](#37-risk-and-contingency)
4. [General](#4-general)
   - 4.1 [Metrics](#41-metrics)
   - 4.2 [Glossary](#42-glossary)
   - 4.3 [Incident Classification](#43-incident-classification)

---

## 1. Introduction

### 1.1 Purpose

The purpose of this Test Plan is to establish a comprehensive testing strategy for the **SNMP Network Monitoring System**, ensuring:

- **Reliability**: System correctly monitors network devices via SNMP
- **Accuracy**: Metrics collection and alert triggering are precise
- **Performance**: System handles 100+ devices with <200ms API response times
- **Security**: Authentication and authorization mechanisms are robust
- **Usability**: Frontend UI is intuitive and responsive

This plan defines the test scope, approach, resources, schedule, and deliverables to validate all functional and non-functional requirements before production deployment.

### 1.2 Scope

**System Under Test**: SNMP Network Monitoring System v1.0

**In Scope:**
- ✅ Backend API (FastAPI) - 18 REST endpoints
- ✅ SNMP Services (device discovery, polling, OID queries)
- ✅ Device Management (CRUD operations, threshold configuration)
- ✅ Alert System (state machine, email notifications)
- ✅ Frontend UI (Dashboard, Device Details, Alerts, Settings)
- ✅ Authentication/Authorization (JWT-based)
- ✅ Database Layer (SQLite with SQLAlchemy ORM)
- ✅ Cache Layer (Redis integration)
- ✅ Background Workers (discovery, polling schedulers)

**Out of Scope:**
- ❌ Third-party library internals (pysnmp, FastAPI, React)
- ❌ Operating system level testing
- ❌ Network infrastructure (routers, switches)
- ❌ Browser compatibility (focus on modern browsers: Chrome, Firefox, Edge)

**Testing Levels:**
- Unit Testing (70% coverage target)
- Integration Testing (80% coverage target)
- End-to-End Testing (100% critical paths)
- Performance Testing (load, stress)
- Security Testing (OWASP Top 10)

### 1.3 References

| Document | Location | Description |
|----------|----------|-------------|
| **System README** | `/README.md` | System overview and quick start guide |
| **API Documentation** | `http://localhost:8000/docs` | Interactive Swagger/OpenAPI documentation |
| **Deployment Guide** | `/DEPLOYMENT.md` | Production deployment procedures |
| **Database Design** | `/docs/diagrams/database-design.md` | Database schema and relationships |
| **OID Compatibility Report** | `/OID_COMPATIBILITY_REPORT.md` | Cisco SNMP OID analysis |
| **Project Review Report** | `/PROJECT_REVIEW_REPORT.md` | System architecture review |
| **IEEE 829 Standard** | External | Software Test Documentation Standard |
| **OWASP Top 10** | https://owasp.org/Top10 | Web application security risks |

---

## 2. Test Plans

### 2.1 Test Items

The following components will be tested:

#### **2.1.1 Backend Services**

| Service | File | Description | Risk Level |
|---------|------|-------------|------------|
| **SNMP Service** | `backend/services/snmp_service.py` | SNMP GET/WALK operations, OID parsing | **HIGH** |
| **Discovery Service** | `backend/services/discovery_service.py` | Network scanning, device detection | **HIGH** |
| **Polling Service** | `backend/services/polling_service.py` | Scheduled metric collection | **HIGH** |
| **Alert Service** | `backend/services/alert_service.py` | Alert state machine, threshold checking | **HIGH** |
| **Email Service** | `backend/services/email_service.py` | SMTP notification delivery | **MEDIUM** |
| **Device Service** | `backend/services/device_service.py` | Device CRUD, MAC/vendor parsing | **MEDIUM** |

#### **2.1.2 API Endpoints**

| Endpoint Group | Count | Examples | Risk Level |
|---------------|-------|----------|------------|
| **Device Management** | 6 | `GET /device/`, `PUT /device/{ip}/thresholds` | **HIGH** |
| **Query/Analytics** | 5 | `GET /query/network-summary`, `GET /query/top-devices` | **MEDIUM** |
| **Alert Management** | 4 | `PUT /device/{ip}/alert/{type}/acknowledge` | **HIGH** |
| **Authentication** | 2 | `POST /auth/login`, `GET /auth/me` | **CRITICAL** |
| **Recipients** | 3 | `GET /recipients/`, `POST /recipients/` | **LOW** |

#### **2.1.3 Frontend Components**

| Component | Location | Description | Risk Level |
|-----------|----------|-------------|------------|
| **Dashboard** | `frontend/src/app/dashboard/page.tsx` | Network summary, KPIs, charts | **HIGH** |
| **Device List** | `frontend/src/components/DeviceList.tsx` | Device table with status | **MEDIUM** |
| **Device Details** | `frontend/src/app/devices/[ip]/page.tsx` | Detailed metrics, thresholds | **MEDIUM** |
| **Alert Panel** | `frontend/src/components/AlertPanel.tsx` | Active alerts display | **HIGH** |
| **Login Form** | `frontend/src/app/login/page.tsx` | Authentication form | **CRITICAL** |
| **Settings** | `frontend/src/app/settings/page.tsx` | Alert recipients, discovery trigger | **MEDIUM** |

#### **2.1.4 Database Models**

| Model | Description | Risk Level |
|-------|-------------|------------|
| **Device** | Core device entity | **HIGH** |
| **DeviceMetric** | Time-series metrics | **MEDIUM** |
| **Interface** | Network interface data | **MEDIUM** |
| **AlertRecipient** | Email notification list | **LOW** |
| **User** | Authentication credentials | **CRITICAL** |

### 2.2 Test Traceability Matrix

| Requirement ID | Feature | Test Cases | Test Type | Priority | Status |
|---------------|---------|------------|-----------|----------|--------|
| **REQ-001** | Device Discovery | TC-DISC-001, TC-DISC-002, TC-DISC-003 | Integration, Unit | P0 | ✅ Pass |
| **REQ-002** | SNMP Polling | TC-POLL-001, TC-POLL-002, TC-POLL-003 | Unit | P0 | ⏳ Pending |
| **REQ-003** | Alert Triggering | TC-ALERT-001 to TC-ALERT-008 | Integration | P0 | ✅ Pass |
| **REQ-004** | Email Notifications | TC-EMAIL-001, TC-EMAIL-002 | Unit | P1 | ⏳ Pending |
| **REQ-005** | User Authentication | TC-AUTH-001 to TC-AUTH-007 | Integration | P0 | ✅ Pass |
| **REQ-006** | Device CRUD | TC-DEV-001 to TC-DEV-006 | Integration | P0 | ✅ Pass |
| **REQ-007** | Threshold Configuration | TC-DEV-007, TC-DEV-008 | Integration | P1 | ✅ Pass |
| **REQ-008** | Dashboard Metrics | TC-QUERY-001, TC-QUERY-002 | Integration | P1 | ✅ Pass |
| **REQ-009** | Interface Monitoring | TC-INTF-001, TC-INTF-002 | Integration | P2 | ⏳ Pending |
| **REQ-010** | Cache Performance | TC-CACHE-001, TC-CACHE-002 | Unit | P2 | ⏳ Pending |

**Legend:**
- ✅ Pass: All tests passing
- ❌ Fail: Tests failing
- ⏳ Pending: Tests not yet implemented
- 🚫 Blocked: Tests blocked by dependencies

### 2.3 Features to be Tested

The following features are **HIGH RISK** and require comprehensive testing:

#### **Critical Features (P0)**

1. **Device Discovery** ⚠️ **HIGH RISK**
   - Network range scanning (CIDR notation)
   - SNMP device detection
   - Concurrent discovery (20 threads)
   - Device deduplication (by MAC address)
   - **Why High Risk**: Core functionality, network-intensive
   - **Test Coverage**: Unit (services), Integration (API), E2E (UI trigger)

2. **SNMP Polling** ⚠️ **HIGH RISK**
   - Scheduled metric collection (60s interval)
   - CPU/Memory/Uptime OID queries
   - Timeout and retry handling
   - Polling state management
   - **Why High Risk**: Real-time operations, external dependencies
   - **Test Coverage**: Unit (SNMP client), Integration (polling workflow)

3. **Alert State Machine** ⚠️ **HIGH RISK**
   - Threshold breach detection
   - State transitions: `clear` → `triggered` → `acknowledged` → `clear`
   - Email notification triggering
   - Alert persistence
   - **Why High Risk**: Business-critical alerting logic
   - **Test Coverage**: Integration (state transitions), Unit (threshold logic)

4. **Authentication & Authorization** ⚠️ **CRITICAL**
   - JWT token generation and validation
   - Password hashing (bcrypt)
   - Protected endpoint access control
   - Token expiration handling
   - **Why Critical**: Security vulnerability exposure
   - **Test Coverage**: Integration (auth flow), Security (bypass attempts)

#### **Important Features (P1)**

5. **Email Notification Delivery** ⚠️ **MEDIUM RISK**
   - SMTP connection and sending
   - Email template rendering
   - Delivery error handling
   - **Test Coverage**: Unit (mocked SMTP), Reliability (SLA testing)

6. **Device Threshold Configuration** ⚠️ **MEDIUM RISK**
   - CPU/Memory threshold updates
   - Per-interface packet drop thresholds
   - Validation (0-100% range)
   - **Test Coverage**: Integration (API endpoints)

7. **Dashboard Analytics** ⚠️ **MEDIUM RISK**
   - Network summary aggregation
   - Top devices by CPU/Memory
   - Active alerts count
   - **Test Coverage**: Integration (query endpoints), E2E (UI rendering)

### 2.4 Features Not to be Tested

The following are **excluded** from testing scope:

#### **Low Risk / Stable Components**

1. **Third-Party Libraries** - Low Risk
   - `pysnmp` SNMP protocol implementation
   - `FastAPI` web framework routing
   - `SQLAlchemy` ORM query generation
   - `React/Next.js` framework internals
   - **Reason**: Well-tested by maintainers, stable, documented

2. **Static Content** - Low Risk
   - CSS styling (Tailwind CSS)
   - Image assets
   - Favicon and manifest files
   - **Reason**: No business logic

3. **Development Tools** - Low Risk
   - Setup scripts (`setup.sh`)
   - Makefile commands
   - Environment validation scripts
   - **Reason**: Development-time only, not production code

4. **External Services** - Out of Scope
   - SMTP server (Gmail) reliability
   - Redis server internals
   - SQLite database engine
   - **Reason**: Third-party dependencies, tested upstream

### 2.5 Test Approach or Test Strategy

We will employ a **multi-layered testing pyramid** approach:

```
           ╱╲  E2E Tests (10%)
          ╱  ╲  Critical user workflows
         ╱────╲
        ╱ Integ ╲ Integration Tests (20%)
       ╱  Tests  ╲ API + Database + Services
      ╱──────────╲
     ╱   Unit     ╲ Unit Tests (70%)
    ╱    Tests     ╲ Service layer, utilities
   ╱────────────────╲
```

#### **Level 1: Unit Tests (70% of test suite)**

**Target Coverage**: ≥70% line coverage

**Approach**:
- Test service layer functions in isolation
- Mock external dependencies (SNMP, SMTP, database)
- Focus on business logic and edge cases
- Fast execution (<5 seconds total)

**Tools**:
- `pytest` - Test framework
- `pytest-mock` - Mocking
- `pytest-asyncio` - Async test support

**Example Test Files**:
```
backend/tests/unit/
├── test_snmp_service.py
├── test_discovery_service.py
├── test_polling_service.py
├── test_alert_service.py
├── test_email_service.py
├── test_device_service.py
└── test_cache.py
```

#### **Level 2: Integration Tests (20% of test suite)**

**Target Coverage**: ≥80% of API endpoints

**Approach**:
- Test API endpoints through HTTP requests
- Use in-memory SQLite database
- Mock authentication for business logic tests
- Test real database transactions
- Existing tests: `test_devices.py`, `test_auth.py`, `test_alerts.py`, `test_query.py`

**Tools**:
- `TestClient` (FastAPI)
- In-memory SQLite
- Fixtures for test data

#### **Level 3: End-to-End Tests (10% of test suite)**

**Target Coverage**: 100% of critical user paths

**Approach**:
- Test complete workflows through UI
- Real browser automation
- Both frontend and backend running
- Test happy paths and critical errors

**Tools**:
- `Playwright` - Browser automation
- Docker Compose for full stack

**Critical Paths**:
1. Login → View Dashboard → See Metrics
2. Trigger Discovery → View Devices → Configure Threshold
3. Alert Triggered → Email Sent → Acknowledge → Resolve

#### **Level 4: Non-Functional Tests**

**4.1 Performance Testing**
- **Tool**: Locust (Python load testing)
- **Benchmarks**:
  - API response time: <200ms (95th percentile)
  - Dashboard load: <500ms
  - Support 100 devices polling every 60s
  - Concurrent users: 10 simultaneous sessions

**4.2 Security Testing**
- **Scope**: OWASP Top 10
  - SQL Injection attempts
  - XSS payload injection
  - JWT token tampering
  - Authentication bypass
  - Rate limiting brute force
- **Tool**: Manual test cases + `pytest` security tests

**4.3 Reliability Testing**
- Email delivery SLA: ≥95% success rate
- Polling consistency: ≥99% of scheduled polls execute
- Alert notification latency: <10 seconds from threshold breach

### 2.6 Item Pass/Fail Criteria

#### **Unit Tests**
✅ **PASS Criteria**:
- All assertions pass
- No exceptions raised
- Code coverage ≥70%
- Execution time <5 seconds

❌ **FAIL Criteria**:
- Any assertion failure
- Uncaught exceptions
- Coverage drops below 70%

#### **Integration Tests**
✅ **PASS Criteria**:
- HTTP status codes match expected
- Response JSON schema valid
- Database state changes correctly
- No transaction rollbacks (unless expected)
- Execution time <30 seconds

❌ **FAIL Criteria**:
- Unexpected HTTP status codes
- Invalid response structure
- Database inconsistencies
- Authentication bypass

#### **E2E Tests**
✅ **PASS Criteria**:
- User workflow completes successfully
- UI elements visible and interactive
- Data persists correctly
- No JavaScript console errors

❌ **FAIL Criteria**:
- Workflow cannot complete
- Critical UI elements missing
- Data loss or corruption
- Application crashes

#### **Performance Tests**
✅ **PASS Criteria**:
- 95th percentile response time <200ms
- Zero timeouts under normal load
- CPU usage <80% on target hardware
- Memory usage stable (no leaks)

❌ **FAIL Criteria**:
- Response time exceeds 500ms
- Timeouts or connection errors
- Memory leaks detected
- System crashes under load

#### **Security Tests**
✅ **PASS Criteria**:
- No critical or high vulnerabilities
- Authentication cannot be bypassed
- SQL injection/XSS blocked
- Rate limiting prevents brute force

❌ **FAIL Criteria**:
- Any critical security vulnerability
- Authentication bypass successful
- Successful injection attack
- Sensitive data leaked

### 2.7 Suspension Criteria and Resumption Requirements

**Testing will be SUSPENDED if:**

1. **Critical Defects Threshold Exceeded**
   - ≥5 high-severity defects found
   - ≥2 critical security vulnerabilities
   - **Resumption**: All critical/high defects resolved or deferred

2. **Test Environment Unavailable**
   - Database corruption
   - Redis server failure
   - Network connectivity issues
   - **Resumption**: Environment restored and validated

3. **Code Quality Below Threshold**
   - Unit test coverage drops below 50%
   - >50% of integration tests failing
   - **Resumption**: Code fixes applied, coverage restored

4. **Test Data Integrity Issues**
   - Test fixtures broken
   - Database migrations failed
   - **Resumption**: Test data regenerated and validated

5. **Blocking Dependencies**
   - Critical third-party library bug
   - External API unavailable (e.g., SMTP server)
   - **Resumption**: Workaround implemented or dependency updated

**Resumption Process**:
1. Issue resolution documented in GitHub Issues
2. Regression tests executed to verify fix
3. Test Lead approves resumption
4. Testing continues from suspended point

### 2.8 Test Deliverables

| Deliverable | Format | Location | Frequency |
|-------------|--------|----------|-----------|
| **Test Plan** | Markdown | `/docs/testing/TEST_PLAN.md` | Once (this document) |
| **Test Cases** | Markdown | `/docs/testing/TEST_CASES.md` | Once, updated as needed |
| **Test Code** | Python/TypeScript | `/backend/tests/`, `/frontend/__tests__/` | Continuous |
| **Coverage Report** | HTML | `/backend/htmlcov/index.html` | Per test run |
| **Test Execution Log** | Terminal output | CI/CD artifacts | Per test run |
| **Defect Reports** | GitHub Issues | Repository Issues tab | As found |
| **Test Summary Report** | Markdown | `/docs/testing/TEST_SUMMARY_<version>.md` | Per release |
| **Performance Report** | HTML/JSON | `/backend/tests/performance/report.html` | Weekly |

**Artifact Retention**:
- Test code: Version controlled (Git)
- Coverage reports: Latest + last 5 runs
- Defect reports: Permanent (GitHub Issues)
- Test summary: Permanent (one per release)

### 2.9 Entry Criteria

Testing **CANNOT BEGIN** until:

✅ **Development Complete**
- All features implemented
- Code reviewed and merged
- No open P0/P1 development tasks

✅ **Documentation Ready**
- API documentation updated (`/docs` endpoint)
- README reflects current features
- Database schema documented

✅ **Environment Configured**
- Test database initialized (in-memory SQLite)
- Redis available (or cache disabled)
- Mock SNMP devices configured (if needed)

✅ **Test Artifacts Ready**
- Test plan approved (this document)
- Test cases documented
- Test data fixtures prepared

✅ **Dependencies Installed**
- `backend/requirements.txt` installed
- `frontend/package.json` dependencies installed
- Test libraries available (`pytest`, `@testing-library/react`)

### 2.10 Exit Criteria

Testing is **COMPLETE** when:

✅ **Execution Complete**
- 100% of planned test cases executed
- All critical paths tested
- All high-risk features validated

✅ **Quality Thresholds Met**
- ≥90% overall test pass rate
- Unit test coverage ≥70%
- Integration test coverage ≥80%
- E2E critical paths: 100% pass

✅ **Defects Resolved**
- Zero critical defects open
- Zero high-severity defects open
- All medium defects either fixed or accepted
- Low severity defects documented for future release

✅ **Performance Validated**
- All performance benchmarks met
- No memory leaks detected
- Load testing passed (100 devices)

✅ **Security Validated**
- Zero critical/high security vulnerabilities
- Authentication and authorization verified
- OWASP Top 10 checks passed

✅ **Documentation Complete**
- Test Summary Report generated
- Known issues documented
- User acceptance sign-off obtained

---

## 3. Test Management

### 3.1 Planned Tasks and Activities

| Phase | Tasks | Duration | Dependencies | Owner |
|-------|-------|----------|--------------|-------|
| **Phase 1: Documentation** | Create test plan, test cases, procedures | Week 1 | None | Test Lead |
| **Phase 2: Unit Tests** | Write service layer unit tests | Week 2-3 | Phase 1 | Backend Tester |
| **Phase 3: Frontend Tests** | Component + E2E tests | Week 3-4 | Phase 1 | Frontend Tester |
| **Phase 4: CI/CD** | GitHub Actions setup | Week 4 | Phase 2-3 | DevOps |
| **Phase 5: Non-Functional** | Performance, security, reliability | Week 5 | Phase 2-4 | QA Engineer |
| **Phase 6: Reporting** | Metrics dashboard, summary reports | Week 6 | All phases | Test Lead |

**Milestone Schedule**:
- ✅ **M1: Test Plan Approved** - End of Week 1
- ⏳ **M2: Unit Tests Complete (70% coverage)** - End of Week 3
- ⏳ **M3: Frontend Tests Complete** - End of Week 4
- ⏳ **M4: CI/CD Operational** - End of Week 4
- ⏳ **M5: All Tests Passing** - End of Week 5
- ⏳ **M6: Test Summary Report** - End of Week 6

### 3.2 Environment & Infrastructure

#### **Development Environment**
- **Purpose**: Individual developer testing
- **Database**: SQLite in-memory (`:memory:`)
- **Backend**: `http://localhost:8000`
- **Frontend**: `http://localhost:3000`
- **Redis**: Optional (or disabled via `CACHE_ENABLED=false`)

#### **CI/CD Environment**
- **Platform**: GitHub Actions (Ubuntu latest)
- **Database**: SQLite in-memory
- **Services**: Redis (Docker container)
- **Isolation**: Fresh environment per test run

#### **Test Data**
- **Fixtures**: `/backend/tests/conftest.py`
- **Mock SNMP**: `snmpsim` tool (if needed for integration)
- **Sample Devices**: 5 devices with various states

#### **Special Hardware Requirements**
- None (all tests use mocks and simulators)

#### **Network Requirements**
- No external network access required
- Discovery tests use local IP ranges (127.0.0.1, 192.168.1.0/24 mocked)

### 3.3 Responsibility and Authority

| Role | Responsibilities | Authority | Current Owner |
|------|-----------------|-----------|---------------|
| **Test Lead** | - Approve test plan<br>- Coordinate testing phases<br>- Final sign-off | - Suspend testing<br>- Approve deferrals<br>- Release authorization | TBD |
| **Backend Tester** | - Write unit tests (services)<br>- Maintain integration tests<br>- Code review | - Approve backend test PRs<br>- Set coverage thresholds | TBD |
| **Frontend Tester** | - Write component tests<br>- Create E2E tests<br>- UI validation | - Approve frontend test PRs<br>- Define critical paths | TBD |
| **QA Engineer** | - Execute manual tests<br>- Performance testing<br>- Security testing | - Raise defects<br>- Validate fixes | TBD |
| **DevOps Engineer** | - CI/CD pipeline setup<br>- Test environment maintenance | - Modify workflows<br>- Grant access | TBD |
| **Developer** | - Fix defects<br>- Support test creation<br>- Code coverage | - Challenge test requirements<br>- Propose deferrals | Development Team |

### 3.4 Resources and Allocation

#### **Human Resources**
- **Test Lead**: 0.5 FTE (20 hours/week)
- **Backend Tester**: 1.0 FTE (40 hours/week for 3 weeks)
- **Frontend Tester**: 1.0 FTE (40 hours/week for 2 weeks)
- **QA Engineer**: 0.5 FTE (20 hours/week for 2 weeks)

#### **Infrastructure**
- GitHub Actions minutes: ~500 minutes/month (free tier sufficient)
- Local development machines: 2 (existing)
- No cloud resources required

#### **Tools & Licenses**
- All tools are open source (pytest, Playwright, Locust)
- No additional licenses needed

### 3.5 Training

| Training Need | Target Audience | Duration | Format |
|--------------|----------------|----------|--------|
| **pytest Framework** | Backend Tester | 4 hours | Online tutorial + hands-on |
| **Playwright E2E** | Frontend Tester | 4 hours | Official docs + examples |
| **SNMP Protocol Basics** | All testers | 2 hours | Internal presentation |
| **System Architecture** | All testers | 2 hours | Code walkthrough |
| **Locust Load Testing** | QA Engineer | 2 hours | Official tutorial |

**Training Materials**:
- pytest: https://docs.pytest.org/
- Playwright: https://playwright.dev/docs/intro
- SNMP: Internal presentation (RFC 1157 summary)

### 3.6 Schedules, Estimates and Costs

#### **Timeline**
```
Week 1: [▓▓▓▓▓▓▓] Documentation & Planning
Week 2: [▓▓▓▓▓▓▓] Unit Tests (Backend Services)
Week 3: [▓▓▓▓▓▓▓] Unit Tests Complete + Frontend Start
Week 4: [▓▓▓▓▓▓▓] Frontend Tests + CI/CD Setup
Week 5: [▓▓▓▓▓▓▓] Non-Functional Testing
Week 6: [▓▓▓▓▓▓▓] Final Validation + Reporting
```

#### **Effort Estimates**
| Phase | Backend | Frontend | QA | Total |
|-------|---------|----------|-----|-------|
| Documentation | 8h | 4h | 4h | 16h |
| Unit Tests | 60h | - | 10h | 70h |
| Frontend Tests | - | 50h | 10h | 60h |
| CI/CD Setup | 8h | 8h | - | 16h |
| Non-Functional | 10h | 10h | 30h | 50h |
| Reporting | 4h | 2h | 10h | 16h |
| **Total** | **90h** | **74h** | **64h** | **228h** |

#### **Cost Estimate**
- **Labor**: $228 hours × $75/hour = $17,100 (assumed blended rate)
- **Infrastructure**: $0 (using free tiers)
- **Tools**: $0 (open source)
- **Total**: **$17,100**

### 3.7 Risk and Contingency

| Risk | Probability | Impact | Mitigation | Contingency |
|------|------------|--------|------------|-------------|
| **SNMP devices unavailable for testing** | Medium | High | Use `snmpsim` to simulate devices | Mock all SNMP interactions |
| **Flaky tests (timing issues)** | High | Medium | Use pytest-rerunfailures, add waits | Quarantine flaky tests, fix later |
| **Frontend test complexity** | Medium | Medium | Start with critical paths only | Reduce E2E coverage to 25% |
| **Performance benchmarks not met** | Low | High | Profile early, optimize queries | Defer optimization to v1.1 |
| **Redis unavailable in CI** | Low | Low | Use Docker service in GitHub Actions | Disable cache in tests |
| **Test environment setup issues** | Medium | Medium | Document setup in README | Provide setup script |
| **Team availability** | Medium | High | Cross-train testers | Extend timeline by 1 week |
| **Third-party library bugs** | Low | High | Pin versions in requirements.txt | Workaround or downgrade version |

---

## 4. General

### 4.1 Metrics

**Metrics to Track:**

| Metric | Target | Measurement | Frequency |
|--------|--------|-------------|-----------|
| **Test Coverage** | ≥70% backend, ≥70% frontend | pytest-cov, istanbul | Per test run |
| **Test Pass Rate** | ≥90% | (Passed / Total) × 100 | Per test run |
| **Defect Density** | <1.0 per KLOC | Defects / Lines of Code | Weekly |
| **Test Execution Time** | <2 minutes (unit + integration) | CI/CD pipeline duration | Per run |
| **Flaky Test Rate** | <5% | (Flaky / Total) × 100 | Weekly |
| **Defects Found** | Tracked | Count by severity | Daily |
| **Defect Resolution Time** | <3 days (critical), <7 days (high) | Time to close | Per defect |
| **Code Review Coverage** | 100% | PRs reviewed before merge | Per PR |

**Reporting**:
- Daily: Test execution results (CI/CD)
- Weekly: Coverage trends, defect summary
- Monthly: Quality metrics dashboard
- Per Release: Comprehensive test summary report

### 4.2 Glossary

| Term | Definition |
|------|------------|
| **SNMP** | Simple Network Management Protocol - Protocol for collecting and organizing information about managed devices on IP networks |
| **OID** | Object Identifier - Unique identifier for SNMP data points (e.g., `1.3.6.1.2.1.1.3.0` for uptime) |
| **Polling** | Scheduled collection of device metrics via SNMP queries |
| **Discovery** | Automated network scanning to detect SNMP-enabled devices |
| **Alert State** | Current status of an alert: `clear`, `triggered`, `acknowledged` |
| **JWT** | JSON Web Token - Token-based authentication mechanism |
| **Threshold** | Configurable limit for metrics (e.g., CPU > 80% triggers alert) |
| **Community String** | SNMP authentication credential (e.g., "public") |
| **Fixture** | Reusable test data setup in pytest |
| **Mock** | Simulated object replacing real dependency in tests |
| **E2E** | End-to-End testing through complete user workflows |
| **CI/CD** | Continuous Integration/Continuous Deployment automation |
| **Coverage** | Percentage of code lines executed during tests |
| **Flaky Test** | Test that intermittently passes/fails without code changes |
| **SLA** | Service Level Agreement - Performance commitment (e.g., 95% email delivery) |

### 4.3 Incident Classification

**Severity Levels:**

| Severity | Definition | Examples | Response Time | Resolution Target |
|----------|-----------|----------|---------------|------------------|
| **Critical** | System unusable, data loss, security breach | - Authentication bypass<br>- Database corruption<br>- SQL injection successful | Immediate | 24 hours |
| **High** | Major functionality broken, no workaround | - SNMP polling stopped<br>- Alerts not triggering<br>- Dashboard not loading | 4 hours | 3 days |
| **Medium** | Functionality impaired, workaround exists | - Threshold update fails<br>- Email delivery 80% success<br>- Chart rendering slow | 1 day | 7 days |
| **Low** | Minor issue, cosmetic, enhancement | - UI alignment off<br>- Typo in error message<br>- Log verbosity | 3 days | Next release |

**Priority Levels:**

| Priority | Definition | Criteria |
|----------|-----------|----------|
| **P0** | Must fix before release | Critical/High severity + affects critical path |
| **P1** | Should fix before release | High/Medium severity + affects common use case |
| **P2** | Fix in next release | Medium/Low severity or rare occurrence |
| **P3** | Fix when convenient | Low severity, cosmetic, enhancement request |

**Defect Workflow**:
1. **Found**: Tester discovers defect
2. **Reported**: GitHub Issue created with template
3. **Triaged**: Severity/Priority assigned by Test Lead
4. **Assigned**: Developer assigned
5. **Fixed**: Code merged
6. **Verified**: Tester validates fix
7. **Closed**: Issue closed with resolution notes

---

## Appendix A: Test Execution Checklist

```
Pre-Testing Checklist:
☐ Test environment configured
☐ Dependencies installed
☐ Test data loaded
☐ Documentation reviewed

During Testing:
☐ Execute tests in order (unit → integration → E2E)
☐ Log all defects immediately
☐ Update coverage reports
☐ Communicate blockers to team

Post-Testing:
☐ Generate coverage report
☐ Analyze failed tests
☐ Update test summary
☐ Archive artifacts
☐ Conduct retrospective
```

---

## Appendix B: Sign-off

**Test Plan Approval:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Test Lead | _____________ | _____________ | ________ |
| Development Lead | _____________ | _____________ | ________ |
| Product Owner | _____________ | _____________ | ________ |

**Test Completion Sign-off:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Test Lead | _____________ | _____________ | ________ |
| QA Manager | _____________ | _____________ | ________ |
| Release Manager | _____________ | _____________ | ________ |

---

**Document End**
