import { test, expect } from '@playwright/test'
import { gotoApp, seedLoggedInProfileWithRemoteCase } from './helpers/profile'
import { setupChartApiMocks, setupLoggedInApiMocks } from './helpers/mockChartApi'
import { LIFE_VOLUME_LABELS } from '../src/types/life-volume'

const mockLifeVolumes = {
  schema_version: 'life-volume@1.0',
  case_id: 'case-e2e-001',
  chart_hash: 'e2e-life-hash',
  disclaimer_block: { text: 'E2E 免责声明', version: '1.0' },
  volumes: [
    { id: 'preface', title: LIFE_VOLUME_LABELS.preface, sections: [] },
    { id: 'vol1', title: LIFE_VOLUME_LABELS.vol1, sections: [] },
    { id: 'vol2', title: LIFE_VOLUME_LABELS.vol2, sections: [] },
    { id: 'vol3', title: LIFE_VOLUME_LABELS.vol3, sections: [] },
    { id: 'vol4', title: LIFE_VOLUME_LABELS.vol4, sections: [] },
    { id: 'vol5', title: LIFE_VOLUME_LABELS.vol5, sections: [] },
    { id: 'vol6', title: LIFE_VOLUME_LABELS.vol6, sections: [] },
    { id: 'colophon', title: LIFE_VOLUME_LABELS.colophon, sections: [] },
  ],
  colophon: { summary_lines: ['E2E 跋'], expandable: true },
}

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
        body: JSON.stringify(mockLifeVolumes),
      })
    })
  })

  test('登录+remoteCaseId 时使用 remote 数据源', async ({ page }) => {
    const lifeReq = page.waitForResponse(
      (res) => res.url().includes('/api/v1/life/volumes/') && res.status() === 200,
      { timeout: 15_000 },
    )
    await gotoApp(page, 'report')
    await lifeReq
    await expect(page.getByTestId('report-vol5-chapter')).toBeVisible({ timeout: 15_000 })
    await expect(page.locator('[data-life-volume-source="remote"]')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByRole('heading', { name: LIFE_VOLUME_LABELS.vol5 })).toBeVisible()
  })
})
