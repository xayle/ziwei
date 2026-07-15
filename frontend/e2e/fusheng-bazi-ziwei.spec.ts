import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'
import { mockBaziDegradedPayload, setupChartApiMocks } from './helpers/mockChartApi'

test.describe('八字紫微页面打磨', () => {
  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
  })

  test('八字速览首屏仅盘面无 KPI', async ({ page }) => {
    await fillMinimalProfile(page)
    await page.getByTestId('profile-bazi').click()
    await expect(page.getByTestId('bazi-layer-structure')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('bazi-layer-summary')).toHaveCount(0)
    await expect(page.getByTestId('bazi-vol2-block')).toHaveCount(0)
    await expect(page.getByTestId('bazi-layer-trust')).toHaveCount(0)
  })

  test('八字速览可见结构洞察条且无规则长文主露', async ({ page }) => {
    await fillMinimalProfile(page)
    await page.getByTestId('profile-bazi').click()
    const strip = page.getByTestId('bazi-structure-insight')
    await expect(strip).toBeVisible({ timeout: 15_000 })
    await expect(strip).toContainText(/用神|格局|·/)
    await expect(page.getByTestId('bazi-layer-explain')).toHaveCount(0)
    await expect(page.getByText('规则与提示')).toHaveCount(0)
  })

  test('375px 八字页无页级横滚', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await fillMinimalProfile(page)
    await page.getByTestId('profile-bazi').click()
    await expect(page.getByTestId('bazi-depth-toggle')).toBeVisible({ timeout: 15_000 })
    const overflow = await page.evaluate(() => {
      const root = document.documentElement
      return root.scrollWidth - root.clientWidth
    })
    expect(overflow).toBeLessThanOrEqual(2)
  })

  test('桌面八字页无页级横滚', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 })
    await fillMinimalProfile(page)
    await page.getByTestId('profile-bazi').click()
    await expect(page.getByTestId('bazi-layer-structure')).toBeVisible({ timeout: 15_000 })
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    expect(overflow).toBeLessThanOrEqual(2)
  })

  test('完整档案八字速览缺失展示少于6处', async ({ page }) => {
    await fillMinimalProfile(page)
    await page.getByTestId('profile-bazi').click()
    await expect(page.getByTestId('bazi-layer-structure')).toBeVisible({ timeout: 15_000 })
    const missingInTable = await page.getByTestId('bazi-layer-structure').locator('.bazi-table').getByText('缺失').count()
    expect(missingInTable).toBeLessThan(6)
  })

  test('紫微速览首屏有方盘 Hero', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei')
    await expect(page.getByTestId('ziwei-depth-toggle')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('ziwei-layer-plate')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('ziwei-layer-trust')).toHaveCount(0)
  })

  test('紫微 degraded 横幅首屏可见', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei')
    const banner = page.getByTestId('trust-degraded-banner')
    await expect(banner).toBeVisible({ timeout: 15_000 })
    await expect(banner).toContainText('ZW03')
  })

  test('375px 紫微页无页级横滚', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei')
    await expect(page.getByTestId('ziwei-layer-plate')).toBeVisible({ timeout: 15_000 })
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    expect(overflow).toBeLessThanOrEqual(2)
  })

  test('紫微运限时间轴分节可加载', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei/timeline')
    await expect(page.getByTestId('timeline-sticky-date')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('timeline-dayun-section')).toBeVisible()
    await expect(page.getByTestId('timeline-liuri-section')).toBeVisible()
    await expect(page.getByText('卷三·运波 — 大限')).toBeVisible()
  })

  test('八字结构档显示互证提示', async ({ page }) => {
    await fillMinimalProfile(page)
    await page.getByTestId('profile-bazi').click()
    await page.waitForResponse((res) => res.url().includes('/api/v1/bazi/full') && res.status() === 200)
    await Promise.all([
      page.waitForResponse((res) => res.url().includes('/api/v1/ziwei/full') && res.status() === 200),
      page.getByRole('button', { name: '查看紫微' }).click(),
    ])
    await expect(page.getByTestId('ziwei-layer-summary')).toBeVisible({ timeout: 15_000 })
    await page.getByRole('button', { name: '查看八字' }).click()
    await expect(page.getByTestId('bazi-layer-structure')).toBeVisible({ timeout: 15_000 })
    await page.getByTestId('bazi-depth-toggle').getByRole('button', { name: '结构' }).click()
    await expect(page.getByTestId('cross-validation-hint')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('cross-validation-hint')).toContainText('日柱')
  })

  test('八字 degraded 显示缺失字段', async ({ page }) => {
    await page.route('**/api/v1/bazi/full', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBaziDegradedPayload),
      })
    })
    await fillMinimalProfile(page)
    await page.getByTestId('profile-bazi').click()
    await expect(page.getByTestId('bazi-trust-overview')).toBeVisible({ timeout: 15_000 })
    await page.getByTestId('bazi-trust-overview').locator('summary').click()
    await expect(page.getByTestId('bazi-trust-overview')).toContainText('时柱（引擎未返回）')
  })

  test('八字速览折叠校勘不含 provenance', async ({ page }) => {
    await fillMinimalProfile(page)
    await page.getByTestId('profile-bazi').click()
    await expect(page.getByTestId('bazi-trust-overview')).toBeVisible({ timeout: 15_000 })
    await page.getByTestId('bazi-trust-overview').locator('summary').click()
    await expect(page.getByTestId('bazi-trust-overview').getByTestId('provenance-section')).toHaveCount(0)
    await expect(page.getByTestId('bazi-trust-overview').getByText('切至「结构」')).toBeVisible()
  })

  test('紫微速览首屏可见 missing_fields 与 provenance', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei')
    const trust = page.getByTestId('ziwei-trust-overview')
    await expect(trust).toBeVisible({ timeout: 15_000 })
    await trust.locator('summary').click()
    await expect(trust.getByTestId('missing-fields')).toBeVisible()
    await expect(trust.getByTestId('provenance-section')).toBeVisible()
  })
})
