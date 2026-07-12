import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'
import { setupChartApiMocks } from './helpers/mockChartApi'

async function assertNoPageOverflow(page: import('@playwright/test').Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(2)
}

test.describe('主路径 375px 复验', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await setupChartApiMocks(page)
  })

  test('档案页无页级横滚', async ({ page }) => {
    await gotoApp(page, 'profile')
    await expect(page.getByTestId('profile-birth-dt')).toBeVisible({ timeout: 15_000 })
    await assertNoPageOverflow(page)
  })

  test('报告页无页级横滚', async ({ page }) => {
    await fillMinimalProfile(page)
    await page.getByTestId('profile-report').click()
    await expect(page.getByTestId('report-vol5-chapter')).toBeVisible({ timeout: 15_000 })
    await assertNoPageOverflow(page)
  })

  test('首页无页级横滚', async ({ page }) => {
    await gotoApp(page, '')
    await expect(page.locator('.fs-page, main').first()).toBeVisible({ timeout: 15_000 })
    await assertNoPageOverflow(page)
  })
})
