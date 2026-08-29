import type { Locator, Page } from '@playwright/test'

/**
 * Any `/help/<article>` page. The articles share the docs shell with the
 * `/help` index; the only thing these criteria observe on them is the
 * article's own level-1 heading, which identifies which article rendered.
 */
export class HelpArticlePage {
  readonly page: Page
  readonly heading: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.getByRole('heading', { level: 1 })
  }

  async goto(path: string): Promise<number | undefined> {
    const response = await this.page.goto(path)
    return response?.status()
  }
}
