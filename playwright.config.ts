import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/specs',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 1,
  reporter: [
    ['html', { outputFolder: 'reports/html', open: 'never' }],
    ['json', { outputFile: 'reports/last-run.json' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.TESTAH_BASE_URL ?? 'https://practicesoftwaretesting.com',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
