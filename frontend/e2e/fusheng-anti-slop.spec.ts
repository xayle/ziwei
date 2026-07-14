import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'
import { setupChartApiMocks } from './helpers/mockChartApi'
import { LIFE_VOLUME_LABELS } from '../src/types/life-volume'

/**
 * R071 / R079 / R103 — 防丑五问 structural proxies (not visual DS sign-off).
 * Q1–Q4 automatable; Q5 requires DS screenshot blind test.
 */
test.describe('防丑五问结构代理', () => {
  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
  })

  test('八字速览：盘面主角、无深读块', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/bazi')
    await expect(page.getByTestId('bazi-layer-structure')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('bazi-vol2-block')).toHaveCount(0)
    await expect(page.getByTestId('bazi-layer-explain')).toHaveCount(0)
    await expect(page.locator('.page-head, [data-testid="page-head"]')).toHaveCount(0)
  })

  test('紫微速览：方盘主角、信任层不在首屏', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei')
    await expect(page.getByTestId('ziwei-layer-plate')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('ziwei-layer-trust')).toHaveCount(0)
    await expect(page.getByTestId('ziwei-palace-structured')).toHaveCount(0)
    await expect(page.locator('.page-head, [data-testid="page-head"]')).toHaveCount(0)
  })

  test('紫微速览：方盘面积大于校勘脚注', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei')
    const plate = page.getByTestId('ziwei-layer-plate')
    await expect(plate).toBeVisible({ timeout: 15_000 })
    const plateBox = await plate.boundingBox()
    expect(plateBox).not.toBeNull()
    const trust = page.getByTestId('ziwei-trust-overview')
    if (await trust.count()) {
      const trustBox = await trust.boundingBox()
      if (trustBox) {
        expect(plateBox!.width * plateBox!.height).toBeGreaterThan(trustBox.width * trustBox.height)
      }
    }
    await expect(page.locator('.fz-cell').first()).toBeVisible()
  })

  test('Q5 代理：遮标题仍可识别品牌与方盘', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'new/ziwei')
    await expect(page.getByTestId('ziwei-layer-plate')).toBeVisible({ timeout: 15_000 })
    await page.addStyleTag({
      content: '.fs-page h1, .fs-page h2, .ziwei-hero h2, .brand-copy { visibility: hidden !important; }',
    })
    await expect(page.locator('img.brand-logo[alt="浮生"]')).toBeVisible()
    expect(await page.locator('.fz-cell').count()).toBeGreaterThanOrEqual(8)
  })

  test('报告卷目：六卷名与 skin 一致、无旧章', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'report')
    await expect(page.getByTestId('report-vol5-chapter')).toBeVisible({ timeout: 15_000 })
    for (const label of [
      LIFE_VOLUME_LABELS.vol1,
      LIFE_VOLUME_LABELS.vol2,
      LIFE_VOLUME_LABELS.vol5,
      LIFE_VOLUME_LABELS.colophon,
    ]) {
      await expect(page.locator('.report-body').getByRole('heading', { name: label })).toBeVisible()
    }
    await expect(page.getByText('四维分析')).toHaveCount(0)
    await expect(page.getByRole('complementary', { name: '读法导览' }).getByRole('heading', { name: '读法导览' })).toBeVisible({ timeout: 15_000 })
  })
})
