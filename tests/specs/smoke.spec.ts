import { test, expect } from '@playwright/test'

// Bootstrap scaffold spec — exempt from POM/traceability per RULES.md
// "Bootstrap exception". Replace with real smoke checks for your target
// once targets.yaml points at it.

test('@smoke target base URL responds with a titled page', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/.+/)
})
