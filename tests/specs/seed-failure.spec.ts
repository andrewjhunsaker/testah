import { test, expect } from '@playwright/test'

// @seed-failure — deliberate failure to exercise the triage path during loop
// validation (docs/plans/2026-08-28-testah-v1.md Task 13). DELETE after the
// validation review. Exempt from POM/traceability as validation scaffolding.
test('@seed-failure heading that does not exist', async ({ page }) => {
  await page.goto('/')
  await expect(
    page.getByRole('heading', { name: 'Testah Seed Failure Heading' })
  ).toBeVisible({ timeout: 3000 })
})
