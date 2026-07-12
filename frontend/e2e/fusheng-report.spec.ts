import { test, expect } from '@playwright/test'
import {
  fillMinimalProfile,
  gotoApp,
  seedLoggedInProfileWithRemoteCase,
} from './helpers/profile'
import {
  setupChartApiMocks,
  setupSnapshotApiMocks,
  setupLoggedInApiMocks,
  mockBaziPayload,
} from './helpers/mockChartApi'

test.describe('报告与新功能', () => {
  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
  })

  test('报告卷首首屏仅封面、建档口径可展开', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'report')
    await expect(page.getByTestId('report-cover-hero')).toBeVisible({ timeout: 15_000 })
    const meta = page.getByTestId('report-preface-meta')
    await expect(meta).toBeVisible()
    await expect(meta).not.toHaveAttribute('open', '')
    await expect(meta.locator('.fs-kpi-strip').first()).not.toBeVisible()
    await meta.locator('summary').click()
    await expect(meta).toHaveAttribute('open', '')
    await expect(meta.locator('.fs-kpi-strip').first()).toBeVisible()
  })

  test('报告默认连续阅读且含六卷卷目', async ({ page }) => {
    await fillMinimalProfile(page)
    await page.getByTestId('profile-report').click()
    await expect(page).toHaveURL(/\/static\/app\/report/)

    const toggle = page.getByTestId('report-continuous-toggle')
    await expect(toggle).toHaveText('连续阅读')
    await expect(page.locator('.report-page--continuous')).toBeVisible()

    await expect(page.getByTestId('report-vol5-chapter')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByRole('heading', { name: '卷五·事之理' })).toBeVisible()
    await expect(page.getByRole('heading', { name: '卷一·命之根' })).toBeVisible()
    await expect(page.getByText('四维分析')).toHaveCount(0)
    await expect(page.getByTestId('report-cross-iztro')).toBeVisible()
    await expect(page.getByTestId('report-cross-iztro')).toContainText('ZW03')
  })

  test('报告互证章展示 ZIP09 八字双轨表', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'report')
    const dualTrack = page.locator('#report-volume-vol2').getByTestId('report-bazi-dual-track')
    await expect(dualTrack).toBeVisible({ timeout: 15_000 })
    await expect(dualTrack.locator('tbody tr')).toHaveCount(1)
    await expect(dualTrack).toContainText('ZIP09')
  })

  test('报告互证章展示 ZW03 iztro 双轨表', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'report')
    const iztroDual = page.getByTestId('report-iztro-dual-track')
    await expect(iztroDual).toBeVisible({ timeout: 15_000 })
    await expect(iztroDual.locator('tbody tr')).toHaveCount(2)
    await expect(iztroDual).toContainText('癸丑')
  })

  test('报告 explain 接入卷五推断默认折叠', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'report')
    const vol5 = page.getByTestId('report-vol5-chapter')
    await expect(vol5).toBeVisible({ timeout: 15_000 })
    await expect(vol5.getByText('事业宜深耕专业')).not.toBeVisible()
    const vol1 = page.locator('#report-volume-vol1')
    await expect(vol1.getByText('典籍依据')).toBeVisible()
    await expect(vol1.getByText('正官格：月令本气透出')).toBeVisible()
  })

  test('报告卷二互证 warn 横幅可见', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'report')
    const vol2 = page.locator('#report-volume-vol2')
    await expect(vol2.getByTestId('trust-degraded-banner')).toBeVisible({ timeout: 15_000 })
    await expect(vol2).toContainText('日柱')
  })

  test('报告可切换单章阅读', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'report')
    await page.getByTestId('report-continuous-toggle').click()
    await expect(page.getByTestId('report-continuous-toggle')).toHaveText('单章阅读')
    await page.getByTestId('report-continuous-toggle').click()
    await expect(page.getByTestId('report-continuous-toggle')).toHaveText('连续阅读')
  })

  test('报告卷六含 AI 解读折叠面板', async ({ page }) => {
    await fillMinimalProfile(page)
    await setupChartApiMocks(page)
    await gotoApp(page, 'report')
    await expect(page.getByText('正在生成报告…')).toHaveCount(0, { timeout: 20_000 })
    await expect(page.locator('#report-volume-vol6 details.ai-panel summary')).toContainText('AI 解读')
    await expect(page.getByTestId('report-notes')).toBeVisible()
  })

  test('报告首屏 chart waterfall ≤4 请求（R082）', async ({ page }) => {
    const chartUrls = [
      '/api/v1/fusheng/archive-bundle',
      '/api/v1/bazi/explain/batch',
      '/api/v1/ziwei/explain/batch',
    ]
    const seen = new Set<string>()

    page.on('request', (req) => {
      const hit = chartUrls.find((path) => req.url().includes(path))
      if (hit) seen.add(hit)
    })

    const bundleDone = page.waitForResponse(
      (res) => res.url().includes('/api/v1/fusheng/archive-bundle') && res.ok(),
      { timeout: 20_000 },
    )
    const baziExplainDone = page.waitForResponse(
      (res) => res.url().includes('/api/v1/bazi/explain/batch') && res.ok(),
      { timeout: 20_000 },
    )
    const ziweiExplainDone = page.waitForResponse(
      (res) => res.url().includes('/api/v1/ziwei/explain/batch') && res.ok(),
      { timeout: 20_000 },
    )

    await setupChartApiMocks(page)
    await setupLoggedInApiMocks(page)
    await seedLoggedInProfileWithRemoteCase(page)
    await gotoApp(page, 'report')

    await expect(page.getByText('正在生成报告…')).toHaveCount(0, { timeout: 20_000 })
    await expect(page.getByTestId('report-vol5-chapter')).toBeVisible({ timeout: 15_000 })
    await bundleDone
    await baziExplainDone
    await ziweiExplainDone

    expect(seen.size).toBeLessThanOrEqual(4)
    expect(seen.has('/api/v1/fusheng/archive-bundle')).toBe(true)
    expect(seen.has('/api/v1/bazi/explain/batch')).toBe(true)
    expect(seen.has('/api/v1/ziwei/explain/batch')).toBe(true)
  })

  test('点击 report-youbi-hour-btn 切换档案右弼为 hour', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'report')
    const vol2 = page.locator('#report-volume-vol2')
    await vol2.scrollIntoViewIfNeeded()
    const youbiBtn = page.getByTestId('report-youbi-hour-btn')
    await expect(youbiBtn).toBeVisible({ timeout: 15_000 })
    await youbiBtn.click()
    await gotoApp(page, 'profile')
    await expect(page.getByTestId('profile-ziwei-youbi')).toHaveValue('hour')
  })
})

test.describe('快照恢复', () => {
  test.describe.configure({ mode: 'serial' })

  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
    await setupLoggedInApiMocks(page)
    await setupSnapshotApiMocks(page)
    await seedLoggedInProfileWithRemoteCase(page)
  })

  test('档案页可恢复快照并跳转报告', async ({ page }) => {
    test.setTimeout(60_000)
    const snapshotsReady = page.waitForResponse(
      (res) => /\/api\/v1\/cases\/[^/]+\/snapshots/.test(res.url())
        && res.request().method() === 'GET'
        && res.status() === 200,
      { timeout: 20_000 },
    )
    await gotoApp(page, 'profile')
    await expect(page).toHaveURL(/\/profile/)
    await expect(page.getByTestId('profile-save')).toBeVisible({ timeout: 20_000 })
    await snapshotsReady
    await expect(page.locator('[data-snapshots-ready="true"]')).toBeAttached({ timeout: 20_000 })

    await page.getByTestId('profile-tab-cloud').click()
    await expect(page.getByTestId('profile-cloud-tab')).toBeVisible({ timeout: 15_000 })

    const restoreBtn = page.getByTestId('profile-snapshot-restore').first()
    await expect(restoreBtn).toBeVisible({ timeout: 20_000 })
    const snapshotDetailReady = page.waitForResponse(
      (res) => /\/api\/v1\/snapshots\/snap-e2e-001/.test(res.url()) && res.status() === 200,
      { timeout: 20_000 },
    )
    await restoreBtn.click()
    await snapshotDetailReady

    await expect(page).toHaveURL(/\/static\/app\/report/, { timeout: 15_000 })
    await expect(page.getByTestId('report-snapshot-note')).toContainText('已从云端快照恢复排盘数据', { timeout: 15_000 })
    await expect(page.locator('.analysis-panel__lead', { hasText: mockBaziPayload.personality.day_stem_trait }).first()).toBeVisible({ timeout: 15_000 })
  })
})
