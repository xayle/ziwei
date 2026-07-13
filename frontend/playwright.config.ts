import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:5173/static/app/',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // CI 使用 playwright install 的 chromium；本地默认本机 Chrome
        ...(process.env.CI ? {} : { channel: (process.env.PW_CHANNEL as 'chrome' | undefined) || 'chrome' }),
      },
    },
  ],
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 5173',
    url: 'http://127.0.0.1:5173/static/app/',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
