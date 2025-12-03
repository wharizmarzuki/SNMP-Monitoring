/**
 * E2E Test Setup - Create Test Data
 *
 * This runs BEFORE E2E tests to ensure test devices exist in the database
 * Run with: npx playwright test --global-setup=./e2e/global-setup.ts
 */
import { chromium, FullConfig } from '@playwright/test'

async function globalSetup(config: FullConfig) {
  console.log('🔧 Setting up E2E test data...')

  const browser = await chromium.launch()
  const page = await browser.newPage()

  try {
    // Login as admin
    await page.goto('http://localhost:3000/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'password')
    await page.click('button[type="submit"]')

    // Wait for login to complete
    await page.waitForURL('**/dashboard', { timeout: 10000 })

    console.log('✅ Login successful')

    // Check if test device exists
    const response = await page.request.get('http://localhost:8000/device/')
    const devices = await response.json()

    console.log(`📊 Found ${devices.length} existing devices`)

    // If no devices, create test device via discovery or API
    if (devices.length === 0) {
      console.log('⚠️  No devices found - tests will be skipped')
      console.log('💡 To run full E2E tests:')
      console.log('   1. Start backend: cd backend && uvicorn main:app')
      console.log('   2. Run discovery or add test device manually')
      console.log('   3. Then run: npm run test:e2e')
    } else {
      console.log(`✅ Test devices ready: ${devices.slice(0, 3).map((d: any) => d.ip_address).join(', ')}`)
    }

  } catch (error) {
    console.error('❌ Setup failed:', error)
    console.log('\n⚠️  Make sure:')
    console.log('   1. Backend is running on http://localhost:8000')
    console.log('   2. Frontend is running on http://localhost:3000')
    console.log('   3. Admin user exists (run: python scripts/setup_admin.py)')
  } finally {
    await browser.close()
  }
}

export default globalSetup
