import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp, seedArchiveReadyProfile } from './helpers/profile'
import { setupChartApiMocks } from './helpers/mockChartApi'

test.describe('扩展工具路由', () => {
  test('首页可进入工具箱（档案就绪）', async ({ page }) => {
    await seedArchiveReadyProfile(page)
    await gotoApp(page)
    await page.getByTestId('home-extensions').click()
    await expect(page).toHaveURL(/\/static\/app\/extensions$/)
    await expect(page.getByText('合婚、相似盘与择日为独立路由')).toBeVisible()
    await expect(page.getByRole('heading', { name: '关系合盘（统一）' })).toBeVisible()
  })

  test('档案未齐时扩展路由被拦截', async ({ page }) => {
    await page.addInitScript(() => localStorage.clear())
    await gotoApp(page, 'extensions/compat')
    await expect(page).toHaveURL(/\/static\/app\/profile/)
    await expect(page).toHaveURL(/reason=archive/)
  })

  test('工具箱可进入合婚/相似盘/择日', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'extensions')
    await page.getByRole('button', { name: '进入' }).first().click()
    await expect(page).toHaveURL(/\/static\/app\/relation\/new/)
    await expect(page.getByTestId('relation-type-grid')).toBeVisible()

    await gotoApp(page, 'extensions')
    await page.getByRole('button', { name: '进入' }).nth(1).click()
    await expect(page).toHaveURL(/\/static\/app\/extensions\/compat/)
    await expect(page.getByRole('heading', { name: '对方信息' })).toBeVisible()

    await gotoApp(page, 'extensions')
    await page.getByRole('button', { name: '进入' }).nth(2).click()
    await expect(page).toHaveURL(/\/static\/app\/extensions\/ziwei-compat/)
    await expect(page.getByRole('heading', { name: '对方信息' })).toBeVisible()

    await gotoApp(page, 'extensions')
    await page.getByRole('button', { name: '进入' }).nth(3).click()
    await expect(page).toHaveURL(/\/static\/app\/extensions\/similarity/)

    await gotoApp(page, 'extensions')
    await page.getByRole('button', { name: '进入' }).nth(4).click()
    await expect(page).toHaveURL(/\/static\/app\/extensions\/zeri/)
    await expect(page.getByTestId('zeri-purpose')).toBeVisible()
  })

  test('合婚页可提交表单（mock API）', async ({ page }) => {
    await fillMinimalProfile(page)
    await page.route('**/api/v1/bazi/compatibility', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          score: 78,
          wuxing_match: { wood: '相生' },
          branch_clash: [],
          born_year_he: ['子丑合'],
          summary: 'E2E 合婚摘要：整体匹配度良好。',
        }),
      })
    })

    await gotoApp(page, 'extensions/compat')
    await page.getByTestId('compat-partner-birth').fill('1992-05-20T14:00')
    await page.getByTestId('compat-run').click()
    await expect(page.getByText('E2E 合婚摘要')).toBeVisible({ timeout: 10_000 })
  })

  test('择日页在 mock 紫微后可出结果', async ({ page }) => {
    await fillMinimalProfile(page)
    await setupChartApiMocks(page)
    await page.route('**/api/v1/zeri/purposes', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ purposes: { marriage: '婚嫁', move: '搬家' } }),
      })
    })
    await page.route('**/api/v1/zeri/recommend**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          year: 2026,
          month: 7,
          purpose: 'marriage',
          purpose_label: '婚嫁',
          life_palace_branch: '子',
          wuxing_ju_name: '水二局',
          days: [],
          recommended: [{
            day: 8,
            ganzhi: '甲子',
            score: 88,
            level: '大吉',
            reason: 'E2E 推荐日',
          }],
        }),
      })
    })

    await gotoApp(page, 'extensions/zeri')
    await expect(page.getByText('E2E 推荐日')).toBeVisible({ timeout: 15_000 })
  })
})
