# Test Procedures
**SNMP Network Monitoring System**

---

## Document Information

| Field | Details |
|-------|---------|
| **Document Name** | Test Procedures - SNMP Monitoring System |
| **Reference Number** | TP-PROC-001 |
| **Version** | 1.0.0 |
| **Last Updated** | 2025-12-02 |
| **Related Documents** | [Test Plan](TEST_PLAN.md), [Test Cases](TEST_CASES.md) |

---

## Table of Contents

1. [Test Environment Setup](#1-test-environment-setup)
2. [Running Tests](#2-running-tests)
3. [Test Execution Workflows](#3-test-execution-workflows)
4. [Troubleshooting](#4-troubleshooting)
5. [Reporting](#5-reporting)

---

## 1. Test Environment Setup

### 1.1 Prerequisites

Before running tests, ensure the following are installed:

```bash
# Check Python version
python3 --version  # Should be 3.12+

# Check Node.js version
node --version    # Should be 18+

# Check Git
git --version
```

### 1.2 Backend Test Environment Setup

**Step-by-step procedure:**

```bash
# 1. Navigate to project root
cd /path/to/SNMP-Monitoring

# 2. Navigate to backend directory
cd backend

# 3. Create virtual environment (if not exists)
python3 -m venv venv

# 4. Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# 5. Install dependencies including test libraries
pip install -r requirements.txt

# 6. Verify pytest installation
pytest --version

# 7. Verify test discovery
pytest --collect-only

# Expected output: Should list all test files and test functions
```

### 1.3 Frontend Test Environment Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install --legacy-peer-deps

# 3. Verify test libraries installed
npm list @testing-library/react @testing-library/jest-dom

# 4. Verify Playwright (if E2E tests exist)
npx playwright --version
```

### 1.4 Test Database Setup

**Note**: Tests use in-memory SQLite automatically. No manual setup required.

**Verification**:
```python
# In backend directory
python -c "from app.core.database import Base; print('Database models OK')"
```

---

## 2. Running Tests

### 2.1 Quick Test Execution

#### Run All Tests (Recommended)

```bash
# From project root
make test

# OR from backend directory
cd backend
source venv/bin/activate
pytest
```

#### Run with Verbose Output

```bash
make test-verbose

# OR
pytest -vv
```

#### Run with Coverage Report

```bash
make test-coverage

# OR
pytest --cov=app --cov-report=html --cov-report=term
```

**Expected Output**:
```
======================== test session starts =========================
platform linux -- Python 3.12.0, pytest-7.4.0, pluggy-1.3.0
rootdir: /backend
plugins: asyncio-0.21.0, cov-4.1.0
collected 28 items

tests/integration/test_auth.py::TestAuthenticationFlow::test_login_with_valid_credentials_returns_token PASSED
tests/integration/test_devices.py::TestDeviceEndpoints::test_get_all_devices PASSED
...
======================== 28 passed in 2.45s ==========================

---------- coverage: platform linux, python 3.12.0 -----------
Name                               Stmts   Miss  Cover
------------------------------------------------------
app/api/routes.py                     45      3    93%
app/core/models.py                    67      8    88%
services/device_service.py            42      5    88%
------------------------------------------------------
TOTAL                                456     52    89%
```

### 2.2 Targeted Test Execution

#### Run Specific Test Category

```bash
# Run only device tests
make test-device
# OR
pytest -m device

# Run only authentication tests
pytest -m auth

# Run only alert tests
make test-alert
# OR
pytest -m alert

# Run only integration tests
make test-integration
# OR
pytest -m integration
```

#### Run Specific Test File

```bash
pytest tests/integration/test_auth.py
```

#### Run Specific Test Function

```bash
pytest tests/integration/test_auth.py::TestAuthenticationFlow::test_login_with_valid_credentials_returns_token
```

#### Run Tests Matching Pattern

```bash
# Run all tests with "alert" in the name
pytest -k alert

# Run all tests with "device" or "threshold"
pytest -k "device or threshold"
```

### 2.3 Frontend Tests (When Implemented)

```bash
# Run Jest component tests
cd frontend
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage

# Run E2E tests with Playwright
npx playwright test

# Run E2E in headed mode (see browser)
npx playwright test --headed
```

---

## 3. Test Execution Workflows

### 3.1 Pre-Commit Testing Workflow

**When to use**: Before committing code changes

**Procedure**:
```bash
# 1. Run all tests
make test

# 2. Check coverage
make test-coverage

# 3. Verify coverage threshold met (≥70%)
# Look for: "TOTAL ... 70%"

# 4. If tests pass, proceed with commit
git add .
git commit -m "Your commit message"

# 5. If tests fail, fix issues and repeat
```

**Success Criteria**:
- ✅ All tests pass
- ✅ Coverage ≥ 70%
- ✅ No new warnings

### 3.2 Pull Request Testing Workflow

**When to use**: Before creating or merging PR

**Procedure**:
```bash
# 1. Ensure on feature branch
git branch

# 2. Pull latest from main
git fetch origin
git merge origin/main

# 3. Resolve any conflicts

# 4. Run full test suite
make test-coverage

# 5. Run integration tests specifically
make test-integration

# 6. Check for flaky tests (run multiple times)
pytest --count=3  # Run each test 3 times

# 7. Push to remote
git push origin your-branch-name

# 8. Create PR - CI will run tests automatically
```

**Success Criteria**:
- ✅ All tests pass locally
- ✅ No merge conflicts
- ✅ CI/CD pipeline passes (green checkmark on PR)

### 3.3 Release Testing Workflow

**When to use**: Before production release

**Procedure**:
```bash
# 1. Checkout release candidate branch
git checkout release/v1.0.0

# 2. Run comprehensive test suite
make test-coverage

# 3. Run performance tests
cd backend
source venv/bin/activate
locust -f tests/performance/locustfile.py --users 100 --spawn-rate 10 --run-time 5m --headless

# 4. Run security tests
pytest tests/security/

# 5. Manual smoke testing
# - Start backend: make backend
# - Start frontend: make frontend
# - Test critical paths manually:
#   a. Login
#   b. View dashboard
#   c. Trigger discovery
#   d. Configure alert
#   e. Acknowledge alert

# 6. Generate test summary report
python scripts/generate_test_report.py > docs/testing/TEST_SUMMARY_v1.0.0.md

# 7. Review and sign-off
# - Test Lead reviews report
# - QA Manager approves
```

**Success Criteria**:
- ✅ 100% of critical path tests pass
- ✅ Zero critical/high defects open
- ✅ Performance benchmarks met
- ✅ Manual smoke tests pass
- ✅ Test summary report approved

---

## 4. Troubleshooting

### 4.1 Common Test Failures

#### Problem: `ModuleNotFoundError: No module named 'app'`

**Cause**: Python path not configured correctly

**Solution**:
```bash
# Ensure you're in backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Verify PYTHONPATH
echo $PYTHONPATH

# Run tests with Python path
PYTHONPATH=. pytest
```

---

#### Problem: `Database is locked`

**Cause**: Previous test didn't clean up properly

**Solution**:
```bash
# Kill any hung processes
pkill -f pytest

# Clear test artifacts
make clean

# Re-run tests
pytest
```

---

#### Problem: `pytest: command not found`

**Cause**: pytest not installed or venv not activated

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate

# Install pytest
pip install pytest pytest-cov pytest-asyncio

# Verify installation
pytest --version
```

---

#### Problem: Tests pass locally but fail in CI

**Cause**: Environment differences (timing, paths, dependencies)

**Solution**:
```bash
# 1. Check CI logs for specific error
# 2. Reproduce locally by simulating CI environment
docker run -it python:3.12 /bin/bash
# Inside container:
git clone <repo>
cd <repo>/backend
pip install -r requirements.txt
pytest

# 3. Fix timing issues with explicit waits
# 4. Check for hardcoded paths (use relative paths)
# 5. Pin dependency versions in requirements.txt
```

---

#### Problem: Flaky tests (intermittent failures)

**Cause**: Race conditions, timing dependencies

**Solution**:
```bash
# 1. Identify flaky test
pytest --lf  # Run last failed

# 2. Run multiple times to confirm
pytest tests/path/to/test.py --count=10

# 3. Add explicit waits in test
await asyncio.sleep(0.1)

# 4. Use pytest-rerunfailures
pytest --reruns 3 --reruns-delay 1

# 5. Quarantine flaky test
@pytest.mark.skip(reason="Flaky - needs investigation")
```

---

### 4.2 Coverage Issues

#### Problem: Coverage below 70%

**Solution**:
```bash
# 1. Generate detailed coverage report
pytest --cov=app --cov-report=html

# 2. Open report in browser
open htmlcov/index.html

# 3. Identify uncovered lines (red highlighting)

# 4. Add tests for uncovered code

# 5. Focus on critical paths first
```

---

## 5. Reporting

### 5.1 Generating Coverage Report

```bash
# HTML report (interactive)
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Terminal report (CI-friendly)
pytest --cov=app --cov-report=term-missing

# XML report (for codecov)
pytest --cov=app --cov-report=xml
```

### 5.2 Test Summary Report

**Manual procedure** (until automated):

1. Run full test suite with coverage
```bash
pytest --cov=app --cov-report=term > test_results.txt
```

2. Count test results
```bash
grep "passed" test_results.txt
grep "failed" test_results.txt
```

3. Extract coverage percentage
```bash
grep "TOTAL" test_results.txt
```

4. Fill template in `/docs/testing/TEST_SUMMARY_TEMPLATE.md`

5. Save as `/docs/testing/TEST_SUMMARY_<version>.md`

---

### 5.3 Defect Reporting

**When to create a defect report**:
- Test fails due to code issue (not test issue)
- Expected behavior not met
- Security vulnerability found
- Performance below benchmark

**Procedure**:
1. Navigate to GitHub Issues
2. Click "New Issue"
3. Use template from `DEFECT_TEMPLATE.md`
4. Assign severity/priority labels
5. Assign to appropriate developer
6. Link to failed test case

**Example**:
```markdown
**Title**: [BUG] Alert not triggered when CPU exceeds threshold

**Severity**: High
**Priority**: P0
**Component**: Alert Service
**Test Case**: TC-ALERT-001

**Description**:
Alert state does not transition from `clear` to `triggered` when CPU utilization exceeds configured threshold.

**Steps to Reproduce**:
1. Set device CPU threshold to 80%
2. Simulate CPU at 85%
3. Run alert check logic

**Expected**: Alert state = `triggered`
**Actual**: Alert state = `clear`

**Environment**:
- Python 3.12
- pytest 7.4.0
- Test database: SQLite in-memory

**Logs**:
[Attach relevant logs]
```

---

## 6. Best Practices

### 6.1 Test Execution

✅ **DO**:
- Run tests before every commit
- Run full suite before creating PR
- Check coverage trends weekly
- Fix failing tests immediately
- Isolate flaky tests

❌ **DON'T**:
- Skip tests to "save time"
- Commit with failing tests
- Ignore coverage drops
- Leave flaky tests unaddressed
- Run tests in production environment

### 6.2 Test Maintenance

✅ **DO**:
- Update tests when requirements change
- Refactor tests with code
- Remove obsolete tests
- Document test intentions
- Keep test data realistic

❌ **DON'T**:
- Leave broken tests disabled indefinitely
- Duplicate test logic
- Use production data in tests
- Hardcode test values
- Test implementation details (test behavior)

---

**Document End**
