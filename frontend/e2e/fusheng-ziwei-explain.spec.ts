/**
 * W102-10 · 紫微页 ZIWEI_PAGE_EXPLAIN_SECTIONS batch
 */
import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'
import { setupChartApiMocks } from './helpers/mockChartApi'

test.describe('紫微页 explain batch（W102-10）', () => {
  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
  })

  test('深读模式加载 palaces/reading 解读块', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei')
    await expect(page.getByTestId('ziwei-layer-plate')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('ziwei-layer-explain')).toHaveCount(0)

    await page.getByTestId('ziwei-depth-toggle').getByRole('button', { name: '深读' }).click()
    await expect(page.getByTestId('ziwei-layer-explain')).toBeVisible()
    await expect(page.getByText('宫图与星曜要点')).toBeVisible()
    await expect(page.getByText('命宫 子：紫微')).toBeVisible()
    await expect(page.getByTestId('ziwei-explain-banner')).toHaveCount(0)
  })

  test('explain 失败时展示降级横幅', async ({ page }) => {
    await page.route('**/api/v1/ziwei/explain/batch', async (route) => {
      await route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"unavailable"}' })
    })
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei')
    await expect(page.getByTestId('ziwei-layer-plate')).toBeVisible({ timeout: 15_000 })
    await page.getByTestId('ziwei-depth-toggle').getByRole('button', { name: '深读' }).click()
    await expect(page.getByTestId('ziwei-explain-banner')).toBeVisible()
    await expect(page.getByTestId('ziwei-layer-explain')).toBeVisible()
  })
})
