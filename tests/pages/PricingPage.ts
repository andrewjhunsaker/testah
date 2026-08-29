import type { Locator, Page } from '@playwright/test'

export const PRICING_PATH = '/pricing'

export const PRICING_HEADING =
  'Your competitors are showing up in AI answers. Are you?'

export const PRIMARY_CTA_LABEL = 'Get Your Visibility Scoreboard'

export type FaqEntry = { question: string; answer: string }

/** The four FAQ items, in render order, with their copy of record. */
export const PRICING_FAQ: readonly FaqEntry[] = [
  {
    question: 'What do I get after purchase?',
    answer:
      'You get a complete AI Visibility Scoreboard that shows where your brand appears, how often you are mentioned, and where you can improve your rankings.',
  },
  {
    question: 'Is this a monthly subscription?',
    answer:
      'No. This is a one-time purchase for a single visibility scoreboard run. You can come back and buy another run whenever you want a fresh read.',
  },
  {
    question: 'How quickly is the visibility scoreboard delivered?',
    answer:
      'Most visibility scoreboards are delivered in minutes after checkout. Complex businesses may take a bit longer, but we keep you updated throughout the run.',
  },
  {
    question: 'Is my payment and business data secure?',
    answer:
      'Yes. Checkout is processed through secure payment providers and your data is handled with encrypted transport and strict access controls.',
  },
]

/**
 * /pricing — public sales page (no auth).
 * Selectors derived from page-maps/vizaeo/pricing/page.json and validated live.
 */
export class PricingPage {
  readonly page: Page
  readonly main: Locator
  readonly heading: Locator
  readonly primaryCta: Locator
  /** Every link on the page — the CTA is expected to be the only one. */
  readonly allLinks: Locator
  readonly faqHeading: Locator
  /** The four `<details>` items; `<details>` maps to the ARIA `group` role. */
  readonly faqItems: Locator

  constructor(page: Page) {
    this.page = page
    this.main = page.getByRole('main')
    this.heading = page.getByRole('heading', { name: PRICING_HEADING, level: 1 })
    this.primaryCta = page.getByRole('link', { name: PRIMARY_CTA_LABEL })
    this.allLinks = page.getByRole('link')
    this.faqHeading = page.getByRole('heading', { name: 'FAQ', level: 2 })
    this.faqItems = this.main.getByRole('group')
  }

  async goto(): Promise<void> {
    await this.page.goto(PRICING_PATH)
  }

  /** One FAQ item, addressed by its question text (unique on the page). */
  faqItem(question: string): Locator {
    return this.faqItems.filter({ hasText: question })
  }

  /** One FAQ item, addressed by its position in the accordion. */
  faqItemAt(index: number): Locator {
    return this.faqItems.nth(index)
  }

  /**
   * The disclosure toggle of a FAQ item. `<summary>` has no ARIA role mapping
   * (Playwright resolves it to `generic`), so there is no role locator for it
   * — an element selector scoped inside the role=group item is the narrowest
   * available handle.
   */
  summaryOf(item: Locator): Locator {
    return item.locator('summary')
  }

  /**
   * The answer body of a FAQ item — the item's only paragraph. Addressed by
   * element selector rather than `getByRole('paragraph')` on purpose: while
   * the item is collapsed the answer is outside the accessibility tree, so a
   * role locator would resolve to nothing and "is it hidden?" would be
   * vacuously true. The element selector resolves in both states, so the
   * collapsed assertion has real teeth.
   */
  answerOf(item: Locator): Locator {
    return item.locator('p')
  }

  faqSummary(question: string): Locator {
    return this.summaryOf(this.faqItem(question))
  }

  faqAnswer(question: string): Locator {
    return this.answerOf(this.faqItem(question))
  }
}
