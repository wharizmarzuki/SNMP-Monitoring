# Frontend E2E Testing Guide

## 🎯 **Prerequisites**

Before running E2E tests, ensure:

### 1. Backend is Running
```bash
cd backend
uvicorn main:app --reload
# Backend should be accessible at http://localhost:8000
```

### 2. Frontend is Running
```bash
cd frontend
npm run dev
# Frontend should be accessible at http://localhost:3000
```

### 3. Admin User Exists
```bash
cd backend
python scripts/setup_admin.py
# Creates admin user with credentials: admin/password
```

### 4. Test Data Exists ⭐
**IMPORTANT**: E2E tests require at least one device in the database!

**Option A: Run Discovery**
```bash
# In frontend UI:
1. Login as admin
2. Go to Settings
3. Enter network range (e.g., 192.168.1.0/24)
4. Click "Start Discovery"
5. Wait for devices to be discovered
```

**Option B: Add Test Device Manually (API)**
```bash
# Use curl to add a test device
curl -X POST http://localhost:8000/device/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "ip_address": "192.168.1.100",
    "hostname": "test-device",
    "vendor": "Cisco",
    "mac_address": "00:11:22:33:44:55"
  }'
```

---

## 🚀 **Running Tests**

### Run All E2E Tests
```bash
cd frontend
npm run test:e2e
```

### Run with UI (Recommended for Development)
```bash
npm run test:e2e:ui
```

### Run Specific Test File
```bash
npx playwright test e2e/device-details.spec.ts
```

### Run in Headed Mode (See Browser)
```bash
npm run test:e2e:headed
```

---

## 📊 **Test Results**

### View HTML Report
```bash
# After tests complete
npx playwright show-report
# Opens: http://localhost:9323
```

### View Failed Test Screenshots
```
frontend/test-results/*/test-failed-1.png
```

### View Traces for Debugging
```bash
npx playwright show-trace test-results/*/trace.zip
```

---

## ⚠️ **Common Issues & Solutions**

### Issue 1: "No devices found" - Tests Skip
**Problem**: Device details tests (TC05) skip because no devices exist
**Solution**:
1. Run device discovery in the UI
2. Or add test devices via API (see above)
3. Verify devices exist: `curl http://localhost:8000/device/`

### Issue 2: Login Tests Timeout
**Problem**: Tests stuck on "Signing in..."
**Solution**:
1. Ensure backend is running and accessible
2. Check admin user exists: `python backend/scripts/setup_admin.py`
3. Increase timeout in test config

### Issue 3: Charts Not Rendering
**Problem**: Device charts don't appear
**Solution**:
1. Ensure devices have been polled (wait 30-60 seconds after discovery)
2. Check backend polling service is running
3. Verify metrics exist: `curl http://localhost:8000/query/device/{ip}/metrics`

### Issue 4: Tests Fail with 401/403
**Problem**: Authentication errors during tests
**Solution**:
1. Clear browser storage: `npx playwright test --project=chromium --clear-context`
2. Verify login credentials in tests match database
3. Check JWT token expiration settings

---

## 🎨 **Test Structure**

### TC05 - Device Details Tests
Located in: `frontend/e2e/device-details.spec.ts`

**17 Tests covering:**
- Navigation to device details
- Device information display
- CPU & Memory charts
- Interface metrics
- Real-time data updates
- Time range filtering
- Mobile responsiveness
- Error handling
- Alert acknowledgment

**Current Behavior:**
- Tests automatically **skip** if no devices exist (won't fail)
- Tests dynamically find first available device
- No hardcoded IP addresses (mostly fixed)

---

## 📝 **Test Data Requirements**

For full test coverage, you need:

| Test | Requirement |
|------|-------------|
| **Auth Tests** | Admin user (admin/password) |
| **Dashboard Tests** | At least 1 device |
| **Device Details (TC05)** | At least 1 device with metrics |
| **Alert Tests** | Device with triggered alert |

---

## 🔧 **Configuration**

### Playwright Config
File: `frontend/playwright.config.ts`

Key settings:
```typescript
{
  baseURL: 'http://localhost:3000',
  timeout: 30000,  // 30s per test
  retries: 1,      // Retry failed tests once
}
```

### Test Helpers
File: `frontend/e2e/helpers.ts`

Provides:
- `navigateToFirstDevice()` - Navigate to first available device
- `getFirstDeviceIP()` - Get IP of first device
- `login()` - Login helper

---

## 📈 **Expected Results**

### With Backend & Test Data
```
✅ Auth tests: 2-3 passed
✅ Dashboard tests: 5-7 passed
✅ Device Details (TC05): 15-17 passed
Total: ~25-30 passed
```

### Without Test Data
```
⏭️  Auth tests: 2-3 passed
⏭️  Dashboard tests: 2-3 passed (some skipped)
⏭️  Device Details (TC05): 0 passed (all skipped)
Total: ~5-10 passed, rest skipped
```

---

## 🎯 **Best Practices**

### 1. Run Backend First
Always start backend before running E2E tests

### 2. Use Test Data
Create dedicated test devices for E2E tests, don't use production data

### 3. Use UI Mode for Development
```bash
npm run test:e2e:ui
```
Provides visual feedback and easy debugging

### 4. Check Logs
```bash
# Backend logs
tail -f backend/logs/app.log

# Frontend console
# Check browser dev tools during test:e2e:headed
```

### 5. Clean State
```bash
# Reset test state
rm -rf frontend/test-results/
rm -rf frontend/playwright-report/
```

---

## 🚦 **CI/CD Integration**

For automated testing in CI:

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start Backend
        run: |
          cd backend
          pip install -r requirements.txt
          uvicorn main:app --host 0.0.0.0 &
          sleep 5

      - name: Setup Admin User
        run: python backend/scripts/setup_admin.py

      - name: Start Frontend
        run: |
          cd frontend
          npm install
          npm run build
          npm run start &
          sleep 5

      - name: Run E2E Tests
        run: |
          cd frontend
          npx playwright test

      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## 📞 **Troubleshooting Commands**

```bash
# Check if backend is accessible
curl http://localhost:8000/health

# Check if devices exist
curl http://localhost:8000/device/

# Check if admin user exists
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# View Playwright debug logs
DEBUG=pw:api npx playwright test

# Run single test with trace
npx playwright test e2e/device-details.spec.ts:10 --trace on
```

---

## ✅ **Quick Start Checklist**

- [ ] Backend running on :8000
- [ ] Frontend running on :3000
- [ ] Admin user created
- [ ] At least 1 device discovered
- [ ] Devices have been polled (wait 60s)
- [ ] Run `npm run test:e2e`

---

**Last Updated**: 2025-12-04
