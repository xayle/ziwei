/**
 * W102-09 · 八字页 BAZI_PAGE_EXPLAIN_SECTIONS batch
 */
import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'
import { setupChartApiMocks } from './helpers/mockChartApi'

test.describe('八字页 explain batch（W102-09）', () => {
  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
  })

  test('深读模式加载 geju/relations/reading 解读块', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/bazi')
    await expect(page.getByTestId('bazi-layer-structure')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('bazi-layer-explain')).toHaveCount(0)

    await page.getByTestId('bazi-depth-toggle').getByRole('button', { name: '深读' }).click()
    await expect(page.getByTestId('bazi-layer-explain')).toBeVisible()
    await expect(page.getByText('格局解读')).toBeVisible()
    await expect(page.getByText('正官格：月令本气透出。')).toBeVisible()
    await expect(page.getByTestId('bazi-explain-banner')).toHaveCount(0)
  })

  test('explain 失败时展示降级横幅', async ({ page }) => {
    await page.route('**/api/v1/bazi/explain/batch', async (route) => {
      await route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"unavailable"}' })
    })
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/bazi')
    await expect(page.getByTestId('bazi-layer-structure')).toBeVisible({ timeout: 15_000 })
    await page.getByTestId('bazi-depth-toggle').getByRole('button', { name: '深读' }).click()
    await expect(page.getByTestId('bazi-explain-banner')).toBeVisible()
    await expect(page.getByTestId('bazi-layer-explain')).toBeVisible()
  })
})
