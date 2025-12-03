# Automated Testing Guide

**SNMP Network Monitoring System**

---

## Overview

This guide explains how to use the automated testing system with auto-updating documentation.

## Quick Start

### 1. Install Required Dependencies

```bash
cd backend
pip install pytest pytest-asyncio pytest-mock pytest-cov pytest-json-report
```

### 2. Run All Tests

```bash
# From project root
cd backend
pytest tests/ -v
```

### 3. Generate Automated Report

```bash
# Run tests and generate report
python tests/generate_test_report.py

# Or use existing test results (skip test execution)
python tests/generate_test_report.py --no-run
```

### 4. View Report

The report will be generated at:
```
docs/testing/TEST_RESULTS.md
```

---

## Test Structure

### Test Files Created

#### ✅ **backend/tests/unit/test_polling_service.py**
- **Test Cases**: TC02, TC04
- **Coverage**: SNMP polling, interval configuration
- **Tests**:
  - `test_poll_device_success_cisco` - Successful polling
  - `test_poll_device_timeout` - Unreachable device handling
  - `test_poll_device_recovery` - Device recovery after failure
  - `test_poll_device_alert_triggering` - Alert threshold detection
  - `test_poll_interfaces_success` - Interface metrics collection
  - `test_perform_full_poll_with_multiple_devices` - Concurrent polling
  - `test_calculate_interface_speed` - Speed calculation
  - `test_clear_interface_alerts` - Alert clearing
  - `test_polling_interval_update` - Config changes (TC04)

#### ✅ **backend/tests/unit/test_discovery_service.py**
- **Test Cases**: TC01
- **Coverage**: Network discovery, device detection
- **Tests**:
  - `test_network_discovery_success` - IP range scanning
  - `test_network_discovery_empty_network` - Empty network handling
  - `test_network_discovery_invalid_cidr` - Invalid CIDR handling
  - `test_network_discovery_large_subnet` - Large subnet support
  - `test_network_discovery_with_concurrency_limit` - Concurrency control
  - `test_device_deduplication_by_mac` - MAC-based deduplication
  - `test_discovery_with_partial_failures` - Partial failure handling

---

## Test Case Mapping

| Test Case ID | Description | Test File | Status |
|--------------|-------------|-----------|--------|
| **TC01** | Device Discovery | `test_discovery_service.py` | ✅ Implemented |
| **TC02** | SNMP Polling (every 30s) | `test_polling_service.py` | ✅ Implemented |
| **TC03** | Alert Triggering | `test_alerts.py` (existing) | ✅ Implemented |
| **TC04** | Polling Interval Config | `test_polling_service.py` | ✅ Implemented |
| **TC05** | Device Details View | E2E tests (partial) | ⚠️ Partial |
| **TC06** | Alert History | `test_alerts.py` (existing) | ✅ Implemented |
| **TC07** | Invalid SNMP String | `test_snmp_service.py` (existing) | ✅ Implemented |

---

## Running Specific Tests

### Run Only Unit Tests
```bash
pytest tests/unit/ -v
```

### Run Only Integration Tests
```bash
pytest tests/test_*.py -v
```

### Run Specific Test File
```bash
pytest tests/unit/test_polling_service.py -v
```

### Run Specific Test Case
```bash
pytest tests/unit/test_polling_service.py::TestPollingService::test_poll_device_success_cisco -v
```

### Run with Coverage
```bash
pytest tests/ --cov=services --cov=app --cov-report=html
# View report at: backend/htmlcov/index.html
```

---

## Automated Report Features

The `generate_test_report.py` script provides:

### ✅ **Automated Features**

1. **Test Execution**
   - Runs all pytest tests
   - Captures JSON output
   - Generates coverage data

2. **Report Generation**
   - Executive summary with pass/fail statistics
   - Test case mapping (TC01-TC07)
   - Failed test details with error messages
   - Coverage breakdown by module

3. **Documentation Updates**
   - Creates `TEST_RESULTS.md` with latest results
   - Timestamps all reports
   - Tracks test trends

4. **Coverage Analysis**
   - Line coverage percentage
   - Module-by-module breakdown
   - Top 10 covered modules

### 📊 **Report Sections**

1. **Executive Summary**
   - Total tests, passed, failed, skipped
   - Pass rate percentage
   - Test duration
   - Code coverage

2. **Test Case Mapping**
   - Groups tests by test case ID (TC01-TC07)
   - Shows individual test results
   - Execution time per test

3. **Failed Tests Details**
   - Complete error messages
   - Stack traces
   - Failure reasons

4. **Coverage Report**
   - Top 10 most-covered modules
   - Coverage percentage per file

5. **Test Case Status Summary**
   - Overall status for each test case
   - Pass/Fail/Pending/Partial indicators

---

## CI/CD Integration (Optional)

### GitHub Actions Workflow

Create `.github/workflows/test-and-report.yml`:

```yaml
name: Automated Testing

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-mock pytest-cov pytest-json-report

    - name: Run tests and generate report
      run: |
        python backend/tests/generate_test_report.py

    - name: Upload coverage report
      uses: actions/upload-artifact@v3
      with:
        name: test-report
        path: docs/testing/TEST_RESULTS.md

    - name: Comment PR with results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const report = fs.readFileSync('docs/testing/TEST_RESULTS.md', 'utf8');
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: '## 📊 Test Results\n\n' + report.substring(0, 65000)
          });
```

---

## Troubleshooting

### ModuleNotFoundError: No module named 'fastapi'

**Solution**: Install backend dependencies
```bash
cd backend
pip install -r requirements.txt
```

### pytest-json-report not found

**Solution**: Install pytest-json-report
```bash
pip install pytest-json-report
```

### Tests failing due to missing database

**Solution**: Tests use in-memory SQLite, no setup needed. Check if SQLAlchemy is installed.

### Coverage report not generated

**Solution**: Install pytest-cov
```bash
pip install pytest-cov
```

---

## Best Practices

### 1. Run Tests Before Committing
```bash
python backend/tests/generate_test_report.py
```

### 2. Check Coverage Target
- **Unit Tests**: ≥70% coverage
- **Integration Tests**: ≥80% endpoint coverage

### 3. Review Failed Tests
- Check `TEST_RESULTS.md` for detailed error messages
- Fix failing tests before merging

### 4. Update Test Cases
- When adding new features, add corresponding tests
- Follow existing test patterns in `test_*.py` files

### 5. Use Fixtures
- Leverage `conftest.py` fixtures
- Examples: `sample_device`, `test_db`, `auth_headers`

---

## Examples

### Example: Running Full Test Suite with Report

```bash
# 1. Navigate to project root
cd /home/user/SNMP-Monitoring

# 2. Activate virtual environment (if using one)
source venv/bin/activate

# 3. Run tests and generate report
python backend/tests/generate_test_report.py

# 4. View results
cat docs/testing/TEST_RESULTS.md
```

### Example: Quick Test of New Feature

```bash
# 1. Run specific test file
pytest backend/tests/unit/test_polling_service.py -v

# 2. If passes, run full suite
pytest backend/tests/ -v

# 3. Generate report
python backend/tests/generate_test_report.py
```

---

## Report Output Example

```markdown
# Test Execution Report

**Generated**: 2025-12-03 10:30:45
**Status**: ✅ PASSED

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 45 |
| **✅ Passed** | 43 (95.6%) |
| **❌ Failed** | 2 |
| **⏭️ Skipped** | 0 |
| **⏱️ Duration** | 12.34s |
| **📈 Coverage** | 73.5% |

---

## 🎯 Test Case Mapping

### TC01: Device Discovery

| Test | Status | Duration |
|------|--------|----------|
| `test_network_discovery_success` | ✅ PASSED | 0.145s |
| `test_network_discovery_empty_network` | ✅ PASSED | 0.098s |
...
```

---

## Additional Resources

- **Test Plan**: [TEST_PLAN.md](TEST_PLAN.md)
- **Test Cases**: [TEST_CASES.md](TEST_CASES.md)
- **Test Procedures**: [TEST_PROCEDURES.md](TEST_PROCEDURES.md)
- **Requirements Matrix**: [REQUIREMENTS_TRACEABILITY_MATRIX.md](REQUIREMENTS_TRACEABILITY_MATRIX.md)

---

**Last Updated**: 2025-12-03
