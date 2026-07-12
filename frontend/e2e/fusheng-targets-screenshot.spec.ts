import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'
import { setupChartApiMocks } from './helpers/mockChartApi'

const targetsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../docs/design/targets')
const liveDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../docs/reports/live-targets-latest')

test.describe('设计 targets 截图门禁（R087 / R079）', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1120, height: 800 })
    await setupChartApiMocks(page)
    await fillMinimalProfile(page)
    fs.mkdirSync(liveDir, { recursive: true })
  })

  test('冻结 baseline PNG 存在', () => {
    for (const file of ['bazi.png', 'ziwei.png', 'report-toc.png']) {
      expect(fs.existsSync(path.join(targetsDir, file))).toBe(true)
    }
  })

  test('八字页布局 smoke + 截图', async ({ page }) => {
    await gotoApp(page, 'new/bazi')
    await expect(page.getByTestId('bazi-layer-structure')).toBeVisible({ timeout: 15_000 })
    const shot = await page.screenshot({ fullPage: false })
    expect(shot.byteLength).toBeGreaterThan(10_000)
    fs.writeFileSync(path.join(liveDir, 'live-bazi.png'), shot)
  })

  test('紫微页布局 smoke + 截图', async ({ page }) => {
    await gotoApp(page, 'new/ziwei')
    await expect(page.getByTestId('ziwei-layer-plate')).toBeVisible({ timeout: 15_000 })
    const shot = await page.screenshot({ fullPage: false })
    expect(shot.byteLength).toBeGreaterThan(10_000)
    fs.writeFileSync(path.join(liveDir, 'live-ziwei.png'), shot)
  })

  test('报告卷目布局 smoke + 截图', async ({ page }) => {
    await gotoApp(page, 'report')
    await expect(page.getByTestId('report-vol5-chapter')).toBeVisible({ timeout: 15_000 })
    const shot = await page.screenshot({ fullPage: false })
    expect(shot.byteLength).toBeGreaterThan(10_000)
    fs.writeFileSync(path.join(liveDir, 'live-report-toc.png'), shot)
  })
})
