import { defineConfig, devices } from '@playwright/test'

const testahBaseURL =
  process.env.TESTAH_BASE_URL ?? 'https://staging.vizaeo.com'

export default defineConfig({
  metadata: {
    testah: {
      baseURL: testahBaseURL,
    },
  },
  testDir: './tests/specs',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 1,
  reporter: [
    ['html', { outputFolder: 'reports/html', open: 'never' }],
    ['json', { outputFile: 'reports/last-run.json' }],
    ['list'],
  ],
  use: {
    baseURL: testahBaseURL,
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
