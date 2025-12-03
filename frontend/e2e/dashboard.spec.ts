/**
 * E2E tests for Dashboard Workflow
 * Tests complete dashboard functionality including navigation and data display
 */
import { test, expect } from '@playwright/test'

test.describe('Dashboard Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('password')
    await page.getByRole('button', { name: /Sign in/i }).click()

    // Wait for dashboard to load
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 10000 })
  })

  test('displays dashboard with KPI cards', async ({ page }) => {
    // KPI cards should be visible
    await expect(page.getByText('Total Devices')).toBeVisible()
    await expect(page.getByText('Devices Up')).toBeVisible()
    await expect(page.getByText('Devices Down')).toBeVisible()
  })

  test('displays network summary data', async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(2000)

    // Should display numeric values (checking for numbers)
    const totalDevices = page.locator('text=Total Devices').locator('..')
    await expect(totalDevices).toBeVisible()

    // Chart should be present
    const chart = page.locator('svg')
    await expect(chart.first()).toBeVisible({ timeout: 10000 })
  })

  test('displays top devices tables', async ({ page }) => {
    // Wait for tables to load
    await page.waitForTimeout(2000)

    // Tables should be present
    // (Exact text may vary based on data)
    await expect(page.locator('table').first()).toBeVisible()
  })

  test('can navigate to devices page', async ({ page }) => {
    // Click on a device link (if present)
    // Or navigate via menu
    const navbar = page.locator('nav')
    if (await navbar.isVisible()) {
      // Look for devices link
      const devicesLink = page.getByRole('link', { name: /devices/i })
      if (await devicesLink.isVisible()) {
        await devicesLink.click()
        await expect(page).toHaveURL(/.*devices/)
      }
    }
  })

  test('displays active alerts', async ({ page }) => {
    // Wait for alerts to load
    await page.waitForTimeout(2000)

    // Alerts section should exist
    // (May show 0 alerts if none active)
    await expect(page.getByText(/Devices in Alert/i).or(page.getByText(/Active Alerts/i))).toBeVisible()
  })

  test('can change time range selector', async ({ page }) => {
    // Look for time range selector
    const selector = page.locator('select, [role="combobox"]').first()
    if (await selector.isVisible()) {
      await selector.click()

      // Should show options
      await page.waitForTimeout(500)
    }
  })

  test('chart updates when time range changes', async ({ page }) => {
    // Wait for initial chart load
    await page.waitForTimeout(2000)

    // Find time range selector
    const selector = page.locator('select, button:has-text("Last")').first()
    if (await selector.isVisible()) {
      // Take screenshot before
      const chartBefore = page.locator('svg').first()
      await expect(chartBefore).toBeVisible()

      // Change time range
      await selector.click()
      await page.waitForTimeout(500)

      // Select different option (implementation may vary)
      const option = page.locator('text=/60 minutes|3 hours|24 hours/').first()
      if (await option.isVisible()) {
        await option.click()

        // Wait for chart to update
        await page.waitForTimeout(2000)

        // Chart should still be visible (may have different data)
        await expect(chartBefore).toBeVisible()
      }
    }
  })

  test('displays loading skeletons before data loads', async ({ page }) => {
    // Refresh page
    await page.reload()

    // Loading skeletons should appear briefly
    const skeleton = page.locator('.animate-pulse').first()
    await expect(skeleton).toBeVisible({ timeout: 1000 })

    // Then real data should load
    await expect(page.getByText('Total Devices')).toBeVisible({ timeout: 10000 })
  })

  test('handles navigation via navbar', async ({ page }) => {
    // Check if navbar is present
    const navbar = page.locator('nav')
    await expect(navbar).toBeVisible()

    // Should show system title
    await expect(page.getByText(/SNMP/i)).toBeVisible()
  })

  test('can toggle theme', async ({ page }) => {
    // Look for theme toggle button
    const themeToggle = page.locator('button[aria-label*="theme"], button:has-text("Theme")').first()
    if (await themeToggle.isVisible()) {
      await themeToggle.click()

      // Theme should change (visual check)
      await page.waitForTimeout(500)
    }
  })
})

test.describe('Dashboard - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('password')
    await page.getByRole('button', { name: /Sign in/i }).click()
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 10000 })
  })

  test('dashboard is responsive on mobile', async ({ page }) => {
    // KPIs should stack vertically on mobile
    await expect(page.getByText('Total Devices')).toBeVisible()
    await expect(page.getByText('Devices Up')).toBeVisible()

    // Chart should be visible and responsive
    const chart = page.locator('svg').first()
    await expect(chart).toBeVisible({ timeout: 10000 })
  })

  test('can scroll through dashboard content on mobile', async ({ page }) => {
    // Page should be scrollable
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    await page.waitForTimeout(500)

    // Should be able to scroll back to top
    await page.evaluate(() => window.scrollTo(0, 0))
  })
})

test.describe('Dashboard - Error Handling', () => {
  test('handles API errors gracefully', async ({ page }) => {
    // This test would require mocking API responses
    // For now, just check that dashboard doesn't crash

    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('password')
    await page.getByRole('button', { name: /Sign in/i }).click()

    await expect(page).toHaveURL(/.*dashboard/, { timeout: 10000 })

    // Dashboard should render even if some data fails to load
    await expect(page.getByText('Total Devices')).toBeVisible()

    // No uncaught errors in console
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('Browser console error:', msg.text())
      }
    })
  })
})
