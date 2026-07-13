import { defineConfig, devices } from '@playwright/test'

const autopilotE2e = !!process.env.AUTOPILOT_E2E

export default defineConfig({
  testDir: './e2e',
  fullyParallel: !autopilotE2e,
  forbidOnly: !!process.env.CI,
  retries: autopilotE2e ? 1 : process.env.CI ? 1 : 0,
  workers: autopilotE2e ? 1 : process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [['list'], ['github'], ['html', { open: 'never', outputFolder: 'playwright-report' }]]
    : 'list',
  use: {
    baseURL: 'http://127.0.0.1:5173/static/app/',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // CI 使用 playwright install 的 chromium；本地与 autopilot 默认本机 Chrome
        ...(process.env.CI ? {} : { channel: (process.env.PW_CHANNEL as 'chrome' | undefined) || 'chrome' }),
      },
    },
  ],
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 5173',
    url: 'http://127.0.0.1:5173/static/app/',
    reuseExistingServer: !(process.env.CI || autopilotE2e),
    timeout: 120_000,
  },
})
