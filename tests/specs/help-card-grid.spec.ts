// implements: requirements/vizaeo/help/card-grid.md
import { test, expect } from '@playwright/test'
import {
  HELP_CARDS,
  HELP_SIDEBAR_LINK_COUNT,
  HelpPage,
} from '../pages/HelpPage'
import { HelpArticlePage } from '../pages/HelpArticlePage'

test.describe('/help — article card grid', () => {
  // Scenario 1
  test('@smoke renders exactly the nine article cards', async ({ page }) => {
    const help = new HelpPage(page)
    await help.goto()

    await expect(help.heading).toBeVisible()
    await expect(help.subtitle).toHaveText(
      'Everything you need to understand AI visibility and use Vizaeo effectively.',
    )

    // No more, no fewer: `main` holds the grid and nothing else linkable.
    await expect(help.cards).toHaveCount(HELP_CARDS.length)

    for (const [index, card] of HELP_CARDS.entries()) {
      const locator = help.card(card.title)
      await expect(locator, `card "${card.title}" renders`).toBeVisible()
      await expect(locator, `card "${card.title}" href`).toHaveAttribute(
        'href',
        card.href,
      )
      await expect(locator, `card "${card.title}" emoji`).toContainText(card.emoji)
      await expect(locator, `card "${card.title}" title`).toContainText(card.title)
      await expect(
        locator,
        `card "${card.title}" description`,
      ).toContainText(card.description)
      // Order matters: the grid is the reading order of the docs.
      await expect(
        help.cards.nth(index),
        `card ${index + 1} is "${card.title}"`,
      ).toHaveAttribute('href', card.href)
    }
  })

  // Scenario 2
  for (const card of HELP_CARDS) {
    test(`card "${card.title}" routes to its article`, async ({ page }) => {
      const help = new HelpPage(page)
      const article = new HelpArticlePage(page)

      // The cards are Next.js <Link>s: between first paint and hydration the
      // click handler is attached but the router is not ready, so the click is
      // swallowed and no navigation happens. Retrying the click until the
      // navigation takes is the documented Playwright answer to that race —
      // no sleep, and it still fails if the card genuinely does not route.
      //
      // The callback re-loads /help itself so that every attempt is
      // idempotent: a click that navigates somewhere WRONG must not leave the
      // next attempt hunting for the card on the wrong document (which, with
      // no actionTimeout configured, would block past the toPass budget and
      // surface as an opaque test timeout instead of the URL mismatch). The
      // bounded click timeout keeps a genuinely missing card inside the budget
      // too.
      await expect(async () => {
        await help.goto()
        await help.card(card.title).click({ timeout: 3_000 })
        await expect(page).toHaveURL(new RegExp(`${card.href}$`), {
          timeout: 2_000,
        })
      }).toPass({ timeout: 15_000 })

      await expect(article.heading).toHaveText(card.articleHeading)
    })
  }

  // Scenario 3
  test('grid and sidebar cover the same articles, minus the known Deep Reports gap', async ({
    page,
  }) => {
    const help = new HelpPage(page)
    await help.goto()

    await expect(help.sidebarLinks).toHaveCount(HELP_SIDEBAR_LINK_COUNT)
    await expect(help.sidebarLink('Help Center')).toHaveAttribute('href', '/help')
    for (const card of HELP_CARDS) {
      await expect(
        help.sidebarLink(card.title),
        `sidebar links "${card.title}"`,
      ).toHaveAttribute('href', card.href)
    }

    // The one known content/nav inconsistency, pinned deliberately: the
    // sidebar carries Competitor Deep Reports, the grid has no card for it.
    // Closing this gap (or opening a second one) must turn this red on
    // purpose — see requirements/vizaeo/help/card-grid.md, Scenario 3.
    await expect(help.sidebarLink('Competitor Deep Reports')).toHaveAttribute(
      'href',
      '/help/deep-reports',
    )
    await expect(help.card('Deep Reports')).toHaveCount(0)
  })
})
