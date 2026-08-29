// implements: requirements/vizaeo/pricing/faq-accordion.md
import { test, expect } from '@playwright/test'
import { PRICING_FAQ, PricingPage } from '../pages/PricingPage'

test.describe('/pricing — FAQ accordion', () => {
  // Scenario 1
  test('renders four questions, all collapsed on load', async ({ page }) => {
    const pricing = new PricingPage(page)
    await pricing.goto()

    await expect(pricing.faqHeading).toBeVisible()
    await expect(pricing.faqItems).toHaveCount(PRICING_FAQ.length)

    for (const [index, entry] of PRICING_FAQ.entries()) {
      // Positional, not by-question: the criterion pins the four summaries
      // "in this order", so the item at slot `index` must be THIS question.
      const item = pricing.faqItemAt(index)
      await expect(
        pricing.summaryOf(item),
        `question ${index + 1} is "${entry.question}"`,
      ).toHaveText(entry.question)
      await expect(item, `question ${index + 1} is collapsed`).toHaveJSProperty(
        'open',
        false,
      )
      await expect(
        pricing.answerOf(item),
        `answer ${index + 1} is hidden`,
      ).toBeHidden()
    }
  })

  // Scenario 2
  for (const entry of PRICING_FAQ) {
    test(`expanding "${entry.question}" reveals its answer`, async ({ page }) => {
      const pricing = new PricingPage(page)
      await pricing.goto()

      const item = pricing.faqItem(entry.question)
      const answer = pricing.faqAnswer(entry.question)
      await expect(answer).toBeHidden()

      await pricing.faqSummary(entry.question).click()

      await expect(item).toHaveJSProperty('open', true)
      await expect(answer).toBeVisible()
      // The copy of record — these are commercial claims a buyer relies on.
      await expect(answer).toHaveText(entry.answer)
    })
  }

  // Scenario 3
  test('two items can be open at the same time', async ({ page }) => {
    const pricing = new PricingPage(page)
    await pricing.goto()

    const [first, second] = PRICING_FAQ
    await pricing.faqSummary(first.question).click()
    await expect(pricing.faqItem(first.question)).toHaveJSProperty('open', true)

    await pricing.faqSummary(second.question).click()

    // Pins independent-open behavior: a redesign to single-open accordion
    // semantics must be a conscious change, not a silent one.
    await expect(pricing.faqItem(first.question)).toHaveJSProperty('open', true)
    await expect(pricing.faqItem(second.question)).toHaveJSProperty('open', true)
    await expect(pricing.faqAnswer(first.question)).toBeVisible()
    await expect(pricing.faqAnswer(second.question)).toBeVisible()
  })
})
