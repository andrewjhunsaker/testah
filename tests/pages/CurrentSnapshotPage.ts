import type { Locator, Page } from '@playwright/test'

/** The loopback-only Current Snapshot Overview. */
export class CurrentSnapshotPage {
  readonly page: Page
  readonly heading: Locator
  readonly unavailableNotice: Locator
  private versionRequests = 0

  constructor(page: Page) {
    this.page = page
    this.heading = page.getByRole('heading', {
      name: 'Current Snapshot',
      level: 1,
    })
    this.unavailableNotice = page.getByRole('alert')
    page.on('request', (request) => {
      if (request.url().endsWith('/api/version')) this.versionRequests += 1
    })
  }

  async goto(url: string): Promise<void> {
    await this.page.goto(url)
  }

  targetHeading(name: string): Locator {
    return this.page.getByRole('heading', { name, level: 3 })
  }

  targetCard(name: string): Locator {
    return this.page.getByRole('article').filter({
      has: this.targetHeading(name),
    })
  }

  count(value: number, label: string): Locator {
    // Run-count list items have no distinct accessible label, so their
    // rendered value is the narrowest operator-visible locator available.
    return this.page.getByRole('listitem').filter({ hasText: `${value} ${label}` })
  }

  evidenceState(state: string): Locator {
    // The definition's visible value is its operator-facing evidence state.
    return this.page.getByRole('definition').filter({ hasText: state })
  }

  latestRun(targetName: string, value: string): Locator {
    return this.definitionField(this.targetCard(targetName), 'Latest run', value)
  }

  repositoryBranch(value: string): Locator {
    return this.definitionField(this.repositorySection(), 'Branch', value)
  }

  repositoryCommit(value: string | RegExp): Locator {
    return this.definitionField(this.repositorySection(), 'Commit', value)
  }

  lastChecked(): Locator {
    // The last-check value is rendered as paragraph text below the page heading.
    return this.page.getByRole('paragraph').filter({ hasText: 'Last checked' })
  }

  async installClock(): Promise<void> {
    await this.page.clock.install()
  }

  async advanceTime(milliseconds: number): Promise<void> {
    await this.page.clock.fastForward(milliseconds)
    await this.page.waitForLoadState('networkidle')
  }

  versionRequestCount(): number {
    return this.versionRequests
  }

  async setVisibility(state: 'hidden' | 'visible'): Promise<void> {
    // Chromium headless keeps every tab visible. Emulate the browser-owned
    // Page Visibility state while leaving the real dashboard HTTP seam intact.
    await this.page.evaluate((visibilityState) => {
      Object.defineProperty(document, 'visibilityState', {
        configurable: true,
        get: () => visibilityState,
      })
      document.dispatchEvent(new Event('visibilitychange'))
    }, state)
  }

  private repositorySection(): Locator {
    return this.page.getByRole('region', { name: 'Repository' })
  }

  private definitionField(
    container: Locator,
    label: string,
    value: string | RegExp,
  ): Locator {
    // A definition list exposes dt/dd roles but no accessible association
    // between each pair, so the following-sibling axis is the narrowest
    // available handle after locating the visible term by role and text.
    // `term` does not take an accessible name, so a role name option cannot
    // address its visible label.
    return container
      .getByRole('term')
      .filter({ hasText: label })
      .locator('xpath=following-sibling::dd[1]')
      .filter({ hasText: value })
  }
}
