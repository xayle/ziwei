/**
 * W102-11 · ReadingGuide 接 explain reading section
 */
import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'
import { setupChartApiMocks } from './helpers/mockChartApi'

test.describe('读法导览 explain reading（W102-11）', () => {
  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
  })

  test('首页建档后展示动态读法导览', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, '')
    await expect(page.getByTestId('reading-guide-loading')).toHaveCount(0, { timeout: 15_000 })
    await expect(page.locator('[data-testid="reading-guide-dynamic"]').first()).toContainText(/先读/, { timeout: 15_000 })
  })

  test('报告页读法导览来自 explain batch', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'report')
    await expect(page.getByTestId('report-cover-hero')).toBeVisible({ timeout: 15_000 })
    const guide = page.getByRole('complementary', { name: '读法导览' })
    await expect(guide.getByTestId('reading-guide-dynamic').first()).toContainText(/先读/)
  })

  test('explain 失败时回退默认文案', async ({ page }) => {
    await page.route('**/api/v1/bazi/explain/batch', async (route) => {
      await route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"unavailable"}' })
    })
    await page.route('**/api/v1/ziwei/explain/batch', async (route) => {
      await route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"unavailable"}' })
    })
    await fillMinimalProfile(page)
    await gotoApp(page, '')
    await expect(page.getByTestId('reading-guide-fallback')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByText('六卷辑录按分层阅读；卷五推断默认折叠，卷六问书需主动展开。')).toBeVisible()
  })
})
