import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'
import { setupChartApiMocks } from './helpers/mockChartApi'

/**
 * R080 / R103 #1–2 — R-01~R-05 structural proxies on three main pages.
 * Visual DS sign-off remains in R079 (Q5 blind test).
 */

async function assertNoLinearGradientInHero(page: import('@playwright/test').Page, heroTestId: string) {
  const hasGradient = await page.getByTestId(heroTestId).evaluate((el) => {
    const walk = (node: Element): boolean => {
      const style = getComputedStyle(node)
      const bg = style.backgroundImage || ''
      if (bg.includes('linear-gradient')) return true
      return Array.from(node.children).some(walk)
    }
    return walk(el)
  })
  expect(hasGradient).toBe(false)
}

async function assertHeroProseBudget(page: import('@playwright/test').Page, heroTestId: string, maxLen = 80) {
  const prose = await page.getByTestId(heroTestId).locator('p, .analysis-panel__body, [class*="interpretation"]').allTextContents()
  for (const raw of prose) {
    const text = raw.replace(/\s+/g, ' ').trim()
    if (text) expect(text.length).toBeLessThanOrEqual(maxLen)
  }
}

async function assertNoRiskDebtMarkers(page: import('@playwright/test').Page) {
  await expect(page.locator('.page-head, [data-testid="page-head"]')).toHaveCount(0)
  await expect(page.getByText('四维分析')).toHaveCount(0)
  await expect(page.getByText('ChapterStub')).toHaveCount(0)
}

test.describe('R-01~R-05 三页首屏复查', () => {
  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
  })

  test('八字结构档：R-01/02/04/05 无红灯', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/bazi')
    await expect(page.getByTestId('bazi-layer-structure')).toBeVisible({ timeout: 15_000 })
    await assertNoRiskDebtMarkers(page)
    await assertNoLinearGradientInHero(page, 'bazi-layer-structure')
    await assertHeroProseBudget(page, 'bazi-layer-structure')
    await expect(page.getByTestId('bazi-vol2-block')).toHaveCount(0)
    await expect(page.getByTestId('bazi-layer-explain')).toHaveCount(0)
    const heroHeadings = await page.getByTestId('bazi-layer-structure').locator('h1, h2').count()
    expect(heroHeadings).toBeLessThanOrEqual(1)
  })

  test('紫微速览：R-01/02/04/05 无红灯', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei')
    await expect(page.getByTestId('ziwei-layer-plate')).toBeVisible({ timeout: 15_000 })
    await assertNoRiskDebtMarkers(page)
    await assertNoLinearGradientInHero(page, 'ziwei-layer-plate')
    await assertHeroProseBudget(page, 'ziwei-layer-plate')
    await expect(page.getByTestId('ziwei-layer-trust')).toHaveCount(0)
    await expect(page.getByTestId('ziwei-palace-structured')).toHaveCount(0)
  })

  test('报告卷目：R-01/02/05 无红灯', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'report')
    await expect(page.getByTestId('report-vol5-chapter')).toBeVisible({ timeout: 15_000 })
    await assertNoRiskDebtMarkers(page)
    await expect(page.locator('[data-life-volume-source]')).toHaveAttribute('data-life-volume-source', /local|remote/)
    await expect(page.getByRole('complementary').getByRole('heading', { name: '读法导览' })).toBeVisible()
    await expect(page.locator('#report-volume-vol6 .ai-msg')).toHaveCount(0)
  })
})
