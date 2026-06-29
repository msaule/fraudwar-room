import { defineConfig } from '@playwright/test'

const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: {
    timeout: 10_000
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    env: {
      NEXT_PUBLIC_API_BASE_URL: ''
    },
    reuseExistingServer: !process.env.CI,
    timeout: 120_000
  },
  use: {
    baseURL: 'http://localhost:3000',
    browserName: 'chromium',
    launchOptions: executablePath ? { executablePath } : undefined,
    trace: 'retain-on-failure'
  }
})
