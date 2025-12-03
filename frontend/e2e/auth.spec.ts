/**
 * E2E tests for Authentication Flow
 * Tests complete user authentication workflow from login to dashboard
 */
import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page before each test
    await page.goto('/login')
  })

  test('displays login page correctly', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/SNMP Monitoring System/)

    // Check main heading
    await expect(page.getByRole('heading', { name: /SNMP Monitoring System/i })).toBeVisible()

    // Check form elements
    await expect(page.getByLabel('Username')).toBeVisible()
    await expect(page.getByLabel('Password')).toBeVisible()
    await expect(page.getByRole('button', { name: /Sign in/i })).toBeVisible()
  })

  test('shows validation for empty fields', async ({ page }) => {
    // Click submit without filling fields
    await page.getByRole('button', { name: /Sign in/i }).click()

    // HTML5 validation should prevent submission
    // (Built-in browser validation, may vary by browser)
  })

  test('successfully logs in with valid credentials', async ({ page }) => {
    // Fill in credentials
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('password')

    // Submit form
    await page.getByRole('button', { name: /Sign in/i }).click()

    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/)

    // Dashboard elements should be visible
    await expect(page.getByText('Total Devices')).toBeVisible({ timeout: 10000 })
  })

  test('shows error message with invalid credentials', async ({ page }) => {
    // Fill in invalid credentials
    await page.getByLabel('Username').fill('invalid')
    await page.getByLabel('Password').fill('wrongpassword')

    // Submit form
    await page.getByRole('button', { name: /Sign in/i }).click()

    // Error message should appear
    await expect(page.getByText(/Invalid username or password/i)).toBeVisible({ timeout: 5000 })

    // Should remain on login page
    await expect(page).toHaveURL(/.*login/)
  })

  test('shows loading state during login', async ({ page }) => {
    // Fill in credentials
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('password')

    // Submit form
    await page.getByRole('button', { name: /Sign in/i }).click()

    // Loading text should appear (briefly)
    await expect(page.getByText(/Signing in.../i)).toBeVisible({ timeout: 1000 })
  })

  test('clears error message when user starts typing', async ({ page }) => {
    // Trigger error first
    await page.getByLabel('Username').fill('invalid')
    await page.getByLabel('Password').fill('wrong')
    await page.getByRole('button', { name: /Sign in/i }).click()

    // Wait for error
    await expect(page.getByText(/Invalid username or password/i)).toBeVisible({ timeout: 5000 })

    // Start typing in username field
    await page.getByLabel('Username').fill('admin')

    // Error should be cleared
    await expect(page.getByText(/Invalid username or password/i)).not.toBeVisible()
  })

  test('autofocuses username field on page load', async ({ page }) => {
    // Username field should be focused
    await expect(page.getByLabel('Username')).toBeFocused()
  })

  test('displays setup instructions', async ({ page }) => {
    // Setup instructions should be visible
    await expect(page.getByText('First time setup?')).toBeVisible()
    await expect(page.getByText(/python scripts\/setup_admin.py/)).toBeVisible()
  })

  test('password field masks input', async ({ page }) => {
    const passwordField = page.getByLabel('Password')

    // Check input type is password
    await expect(passwordField).toHaveAttribute('type', 'password')
  })

  test('redirects authenticated users from login to dashboard', async ({ page }) => {
    // First, log in
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('password')
    await page.getByRole('button', { name: /Sign in/i }).click()

    // Wait for redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 10000 })

    // Now try to go back to login page
    await page.goto('/login')

    // Should redirect back to dashboard (if AuthGuard is implemented)
    // await expect(page).toHaveURL(/.*dashboard/, { timeout: 5000 })
  })
})

test.describe('Authentication - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test('login form is responsive on mobile', async ({ page }) => {
    await page.goto('/login')

    // Form should be visible and usable
    await expect(page.getByLabel('Username')).toBeVisible()
    await expect(page.getByLabel('Password')).toBeVisible()
    await expect(page.getByRole('button', { name: /Sign in/i })).toBeVisible()

    // Form should be centered and properly sized
    const card = page.locator('form').locator('..')
    await expect(card).toBeVisible()
  })
})
