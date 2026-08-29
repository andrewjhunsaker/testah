// implements: requirements/vizaeo/help/anonymous-access.md
import { test, expect } from '@playwright/test'
import { HELP_ARTICLE_PATHS, HELP_INDEX_PATH, HelpPage } from '../pages/HelpPage'
import { HelpArticlePage } from '../pages/HelpArticlePage'

// No storageState is configured for this project, so every test here runs as a
// genuinely anonymous visitor. The control test below proves that claim rather
// than assuming it.

test.describe('/help — anonymous access', () => {
  // Scenario 1
  test('@smoke the Help Center index is public', async ({ page, baseURL }) => {
    const help = new HelpPage(page)
    // The HTTP status of a navigation is only observable on its Response; the
    // URL and heading assertions below are the web-first half of the check.
    const response = await page.goto(HELP_INDEX_PATH)
    expect(response?.status(), `GET ${HELP_INDEX_PATH}`).toBe(200)

    await expect(page).toHaveURL(new URL(HELP_INDEX_PATH, baseURL).toString())
    await expect(help.heading).toBeVisible()
  })

  // Scenario 2
  for (const path of HELP_ARTICLE_PATHS) {
    test(`article ${path} is public`, async ({ page, baseURL }) => {
      const article = new HelpArticlePage(page)
      const status = await article.goto(path)
      expect(status, `GET ${path}`).toBe(200)

      // Not redirected to /login: the browser is still on the requested path.
      await expect(page).toHaveURL(new URL(path, baseURL).toString())
      await expect(article.heading).toBeVisible()
      await expect(article.heading).not.toHaveText('')
    })
  }

  // Scenario 3 — control
  test('the same anonymous session is still gated on /dashboard', async ({
    page,
  }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login\?redirect_url=%2Fdashboard/)
  })
})
