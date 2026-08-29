// implements: requirements/vizaeo/pricing/primary-cta-route.md
import { test, expect } from '@playwright/test'
import { PRIMARY_CTA_LABEL, PricingPage } from '../pages/PricingPage'
import { SIGNUP_PATH, SignupPage } from '../pages/SignupPage'

test.describe('/pricing — primary CTA', () => {
  // Scenario 1
  test('@smoke the CTA renders and is the only link on the page', async ({
    page,
  }) => {
    const pricing = new PricingPage(page)
    await pricing.goto()

    await expect(pricing.heading).toBeVisible()
    await expect(pricing.primaryCta).toBeVisible()
    await expect(pricing.primaryCta).toHaveText(PRIMARY_CTA_LABEL)
    await expect(pricing.primaryCta).toHaveAttribute('href', SIGNUP_PATH)

    // Pins the signup-first flow: no header, no footer, no direct-to-checkout
    // path. A second link here is a deliberate change, not an accident.
    await expect(pricing.allLinks).toHaveCount(1)
  })

  // Scenario 2
  test('following the CTA reaches the signup page', async ({ page, baseURL }) => {
    const pricing = new PricingPage(page)
    const signup = new SignupPage(page)

    // Same Next.js hydration race as the /help cards: a click landing between
    // first paint and hydration is swallowed by the not-yet-ready router.
    // Retry the click until the navigation takes — no sleep, and it still
    // fails if the CTA genuinely does not route. The callback re-loads
    // /pricing so each attempt is idempotent: a click that navigates somewhere
    // WRONG must not leave the next attempt hunting for the CTA on the
    // destination page, which would block past the toPass budget and hide the
    // URL mismatch behind a test timeout.
    await expect(async () => {
      await pricing.goto()
      await pricing.primaryCta.click({ timeout: 3_000 })
      await expect(page).toHaveURL(new URL(SIGNUP_PATH, baseURL).toString(), {
        timeout: 2_000,
      })
    }).toPass({ timeout: 15_000 })

    // The rendered form is the observable form of "the signup page loaded".
    // Read-only: nothing is typed and nothing is submitted.
    await expect(signup.heading).toBeVisible()
    await expect(signup.emailInput).toBeVisible()
    await expect(signup.continueButton).toBeVisible()
  })
})
