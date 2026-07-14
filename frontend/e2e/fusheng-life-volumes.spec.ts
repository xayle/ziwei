import { test, expect } from '@playwright/test'
import { gotoApp, seedLoggedInProfileWithRemoteCase } from './helpers/profile'
import {
  setupChartApiMocks,
  setupLoggedInApiMocks,
  mockLifeVolumesPayload,
} from './helpers/mockChartApi'
import { LIFE_VOLUME_LABELS } from '../src/types/life-volume'

test.describe('life/volumes 可选权威路径', () => {
  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
    await setupLoggedInApiMocks(page)
    await seedLoggedInProfileWithRemoteCase(page)
    await page.route('**/api/v1/cases/*/snapshots', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      })
    })
    await page.route('**/api/v1/life/volumes/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockLifeVolumesPayload),
      })
    })
  })

  test('登录+remoteCaseId 时使用 remote 数据源且跳过 explain（T082）', async ({ page }) => {
    const explainHits: string[] = []
    page.on('request', (req) => {
      if (req.url().includes('/explain/batch')) explainHits.push(req.url())
    })
    const lifeReq = page.waitForResponse(
      (res) => res.url().includes('/api/v1/life/volumes/') && res.status() === 200,
      { timeout: 15_000 },
    )
    await gotoApp(page, 'report')
    await lifeReq
    await expect(page.getByTestId('report-vol5-chapter')).toBeVisible({ timeout: 15_000 })
    await expect(page.locator('[data-life-volume-source="remote"]')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByRole('heading', { name: LIFE_VOLUME_LABELS.vol5 })).toBeVisible()
    expect(explainHits.length).toBe(0)
    // volumes 单源：不叠 archive AnalysisPanel 典籍层
    await expect(page.locator('#report-volume-vol1').getByText('格局（引擎层）')).toHaveCount(0)
    await expect(page.locator('#report-volume-vol1').getByText('E2E volumes 正官格讲解')).toBeVisible()
  })

  test('T079 volumes flag：跳过 explain/batch，仍 remote 单源', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('fusheng-use-life-volumes-api', '1')
    })

    const explainHits: string[] = []
    page.on('request', (req) => {
      if (req.url().includes('/explain/batch')) explainHits.push(req.url())
    })

    const lifeReq = page.waitForResponse(
      (res) => res.url().includes('/api/v1/life/volumes/') && res.status() === 200,
      { timeout: 15_000 },
    )
    const bundleDone = page.waitForResponse(
      (res) => res.url().includes('/api/v1/fusheng/archive-bundle') && res.ok(),
      { timeout: 20_000 },
    )

    await gotoApp(page, 'report')
    await Promise.all([lifeReq, bundleDone])
    await expect(page.locator('[data-life-volume-source="remote"]')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByTestId('report-vol5-chapter')).toBeVisible({ timeout: 15_000 })
    expect(explainHits.length).toBe(0)
  })

  test('T083 volumes 路径六卷+跋可见', async ({ page }) => {
    await gotoApp(page, 'report')
    await expect(page.locator('[data-life-volume-source="remote"]')).toBeVisible({ timeout: 15_000 })
    for (const label of Object.values(LIFE_VOLUME_LABELS)) {
      if (label === LIFE_VOLUME_LABELS.preface) continue
      await expect(page.locator('.report-body').getByRole('heading', { name: label })).toBeVisible()
    }
    await expect(page.getByText('E2E 跋')).toBeVisible()
    await expect(page.getByTestId('reading-guide-dynamic')).toContainText('E2E volumes 读法')
  })
})
