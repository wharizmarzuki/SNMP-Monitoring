/**
 * E2E Test Helpers
 */
import { Page } from '@playwright/test'

/**
 * Get the first available device IP from the devices list
 * Returns null if no devices exist
 */
export async function getFirstDeviceIP(page: Page): Promise<string | null> {
  await page.goto('/devices')
  await page.waitForTimeout(2000)

  // Try to find device link
  const deviceLink = page.locator('a[href*="/devices/"]').first()
  const count = await deviceLink.count()

  if (count === 0) {
    return null
  }

  // Extract IP from href
  const href = await deviceLink.getAttribute('href')
  if (!href) return null

  // Extract IP address from URL (e.g., /devices/192.168.1.1)
  const match = href.match(/\/devices\/(.+)/)
  return match ? match[1] : null
}

/**
 * Navigate to first device details page
 * Returns true if successful, false if no devices
 */
export async function navigateToFirstDevice(page: Page): Promise<boolean> {
  await page.goto('/devices')
  await page.waitForTimeout(2000)

  const deviceLink = page.locator('a[href*="/devices/"]').first()

  if (await deviceLink.count() === 0) {
    return false
  }

  await deviceLink.click()
  await page.waitForTimeout(2000)

  return true
}

/**
 * Login helper
 */
export async function login(page: Page, username: string = 'admin', password: string = 'password') {
  await page.goto('/login')
  await page.getByLabel('Username').fill(username)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: /Sign in/i }).click()
  await page.waitForURL(/.*dashboard/, { timeout: 10000 })
}
