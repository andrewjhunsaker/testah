import type { Locator, Page } from '@playwright/test'

/** Article card as rendered by the /help index grid. */
export type HelpCard = {
  emoji: string
  title: string
  description: string
  href: string
  /** The `h1` of the article the card links to. */
  articleHeading: string
}

/** The nine cards of the /help grid, in render order. */
export const HELP_CARDS: readonly HelpCard[] = [
  {
    emoji: '🚀',
    title: 'Getting Started',
    description: 'Set up your business and run your first AI visibility analysis.',
    href: '/help/getting-started',
    articleHeading: 'Getting Started',
  },
  {
    emoji: '💡',
    title: 'What is Vizaeo?',
    description: 'Understand AI visibility and why it matters for your business.',
    href: '/help/what-is-vizaeo',
    articleHeading: 'What is Vizaeo?',
  },
  {
    emoji: '🧠',
    title: 'How AI Visibility Works',
    description: 'The theory behind AI recommendations, scoring, and Share of Voice.',
    href: '/help/how-ai-visibility-works',
    articleHeading: 'How AI Visibility Works',
  },
  {
    emoji: '📊',
    title: 'Understanding Your Results',
    description: 'Learn what your Score, Gaps, Fix, and Watch tabs mean.',
    href: '/help/understanding-results',
    articleHeading: 'Understanding Your Results',
  },
  {
    emoji: '📏',
    title: 'The 11 Visibility Metrics',
    description: 'What each metric measures and how to improve it.',
    href: '/help/metrics',
    articleHeading: 'The 11 Visibility Metrics',
  },
  {
    emoji: '🤖',
    title: 'The Five AI Platforms',
    description: 'ChatGPT, Claude, Gemini, Grok, Perplexity — and how they differ.',
    href: '/help/platforms',
    articleHeading: 'The Five AI Platforms',
  },
  {
    emoji: '⚙️',
    title: 'Account & Settings',
    description: 'Themes, API keys, billing, privacy, and accessibility.',
    href: '/help/account',
    articleHeading: 'Account & Settings',
  },
  {
    emoji: '❓',
    title: 'FAQ',
    description: 'Common questions about AI visibility, pricing, and features.',
    href: '/help/faq',
    // The FAQ article's own heading differs from its card title.
    articleHeading: 'Frequently Asked Questions',
  },
  {
    emoji: '💬',
    title: 'Contact Support',
    description: 'Submit a ticket and track your support requests.',
    href: '/help/support',
    articleHeading: 'Contact Support',
  },
]

/** Every `/help/*` article route the sidebar links to (the index itself excluded). */
export const HELP_ARTICLE_PATHS: readonly string[] = [
  '/help/getting-started',
  '/help/what-is-vizaeo',
  '/help/how-ai-visibility-works',
  '/help/understanding-results',
  '/help/deep-reports',
  '/help/metrics',
  '/help/platforms',
  '/help/account',
  '/help/faq',
  '/help/support',
]

/** The `/help` index itself plus every article — the sidebar's eleven links. */
export const HELP_SIDEBAR_LINK_COUNT = 1 + HELP_ARTICLE_PATHS.length

export const HELP_INDEX_PATH = '/help'

/**
 * /help — Help Center index (public, no auth).
 * Selectors derived from page-maps/vizaeo/help/page.json and validated live.
 */
export class HelpPage {
  readonly page: Page
  /** Main content region — holds the heading, subtitle and the card grid only. */
  readonly main: Locator
  readonly heading: Locator
  readonly subtitle: Locator
  /** Every card in the grid: `main` contains no links other than the cards. */
  readonly cards: Locator
  readonly sidebar: Locator
  readonly sidebarNav: Locator
  readonly sidebarLinks: Locator

  constructor(page: Page) {
    this.page = page
    this.main = page.getByRole('main')
    this.heading = page.getByRole('heading', { name: 'Help Center', level: 1 })
    // The subtitle is the only <p> in `main` — the card descriptions are divs.
    this.subtitle = this.main.getByRole('paragraph')
    this.cards = this.main.getByRole('link')
    this.sidebar = page.getByRole('complementary')
    this.sidebarNav = this.sidebar.getByRole('navigation')
    this.sidebarLinks = this.sidebarNav.getByRole('link')
  }

  async goto(): Promise<void> {
    await this.page.goto(HELP_INDEX_PATH)
  }

  /**
   * One article card, addressed by its title. Card accessible names are
   * "<emoji> <title> <description>", and every title is unique within the
   * grid, so a substring name match resolves to exactly one card.
   */
  card(title: string): Locator {
    return this.main.getByRole('link', { name: title })
  }

  /** One sidebar link, addressed by its accessible name. */
  sidebarLink(name: string): Locator {
    return this.sidebarNav.getByRole('link', { name })
  }
}
