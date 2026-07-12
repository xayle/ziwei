import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'
import { setupChartApiMocks } from './helpers/mockChartApi'

test.describe('紫微 Timeline', () => {
  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
  })

  test('选择日期后流日区更新', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei/timeline')

    await expect(page.getByTestId('timeline-date')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('timeline-liuri-section')).toBeVisible({ timeout: 15_000 })

    const before = await page.getByTestId('timeline-liuri-section').innerText()
    await page.getByTestId('timeline-date').fill('2026-06-15')
    await expect(page.getByTestId('timeline-liuri-section')).not.toHaveText(before, { timeout: 15_000 })

    await expect(page.getByTestId('ziwei-forecast-summary')).toBeVisible()
  })
})
