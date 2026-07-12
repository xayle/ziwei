/**
 * R060 · 15 分钟试读路径自动化（步骤 1–9；步骤 10 主观仍人工）
 */
import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'
import { setupChartApiMocks } from './helpers/mockChartApi'

test.describe('P1 试读路径（R060）', () => {
  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
  })

  test('建档→八字→紫微→报告→卷五折叠→跋', async ({ page }) => {
    await fillMinimalProfile(page)

    await page.evaluate(() => {
      const activeId = localStorage.getItem('profile_active_id_v1') || 'default'
      localStorage.setItem('fusheng-reading-progress', JSON.stringify({ [activeId]: 'vol5' }))
    })
    await gotoApp(page, '')
    await expect(page.getByText('续读：')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByTestId('reading-guide-resume')).toBeVisible()

    await gotoApp(page, 'new/bazi')
    await expect(page.getByTestId('bazi-layer-structure')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('bazi-layer-explain')).toHaveCount(0)

    await gotoApp(page, 'new/ziwei')
    await expect(page.getByTestId('ziwei-layer-plate')).toBeVisible({ timeout: 15_000 })

    await gotoApp(page, 'report')
    const vol5 = page.getByTestId('report-vol5-chapter')
    await expect(vol5).toBeVisible({ timeout: 15_000 })
    await expect(page.getByRole('complementary').getByRole('heading', { name: '读法导览' })).toBeVisible()
    await expect(vol5.getByText('事业宜深耕专业')).not.toBeVisible()

    const colophon = page.locator('#report-volume-colophon .colophon-footnote')
    await expect(colophon).toBeVisible()
    const summaryCount = await colophon.locator('.colophon-footnote__summary p').count()
    expect(summaryCount).toBeLessThanOrEqual(3)

    await expect(page.getByTestId('report-cross-iztro')).toBeVisible()
  })
})
