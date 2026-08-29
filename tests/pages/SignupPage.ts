import type { Locator, Page } from '@playwright/test'

export const SIGNUP_PATH = '/signup'

/**
 * /signup — destination of the /pricing primary CTA. Not a designated target
 * page in targets.yaml; this POM exists only so the CTA criterion can assert
 * that the signup form actually rendered. Nothing here submits.
 */
export class SignupPage {
  readonly page: Page
  readonly heading: Locator
  readonly emailInput: Locator
  readonly continueButton: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.getByRole('heading', { name: 'Welcome to Vizaeo', level: 1 })
    this.emailInput = page.getByRole('textbox', { name: 'Email' })
    this.continueButton = page.getByRole('button', { name: 'Continue', exact: true })
  }
}
