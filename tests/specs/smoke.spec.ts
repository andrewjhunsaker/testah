import { test, expect } from '@playwright/test'

// Bootstrap scaffold spec — exempt from POM/traceability per RULES.md
// "Bootstrap exception". Asserts real staging behavior observed 2026-08-28.

test('@smoke unauthenticated root redirects to sign-in', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/\/login/)
  await expect(page).toHaveTitle(/sign in · vizaeo/i)
})

test('@smoke help center is publicly reachable', async ({ page }) => {
  await page.goto('/help')
  await expect(page).toHaveTitle(/vizaeo/i)
})
