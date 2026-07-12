import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'
import { setupChartApiMocks } from './helpers/mockChartApi'

test.describe('浮生主路径', () => {
  test.beforeEach(async ({ page }) => {
    await setupChartApiMocks(page)
  })

  test('档案补全后可进入八字页', async ({ page }) => {
    await fillMinimalProfile(page)
    await page.getByTestId('profile-bazi').click()

    await expect(page).toHaveURL(/\/static\/app\/new\/bazi/)
    await expect(page.getByTestId('bazi-depth-toggle')).toBeVisible({ timeout: 15_000 })
  })

  test('八字结构档显示卷二块', async ({ page }) => {
    await fillMinimalProfile(page)
    await page.getByTestId('profile-bazi').click()
    await page.getByTestId('bazi-depth-toggle').getByRole('button', { name: '结构' }).click()
    await expect(page.getByTestId('bazi-vol2-block')).toBeVisible({ timeout: 15_000 })
  })

  test('档案未齐时八字路由被拦截', async ({ page }) => {
    await page.addInitScript(() => localStorage.clear())
    await gotoApp(page, 'new/bazi')
    await expect(page).toHaveURL(/\/static\/app\/profile/)
    await expect(page).toHaveURL(/reason=archive/)
  })

  test('可新建本地档案', async ({ page }) => {
    await gotoApp(page, 'profile')
    await page.getByTestId('profile-new').click()
    await expect(page.getByText('已新建空白档案')).toBeVisible()
  })

  test('农历模式显示农历录入标签', async ({ page }) => {
    await gotoApp(page, 'profile')
    await page.getByTestId('profile-calendar-mode').selectOption('lunar')
    await expect(page.getByText('农历年月日与时辰')).toBeVisible()
  })

  test('档案未齐时紫微路由被拦截', async ({ page }) => {
    await page.addInitScript(() => localStorage.clear())
    await gotoApp(page, 'new/ziwei')
    await expect(page).toHaveURL(/\/static\/app\/profile/)
    await expect(page).toHaveURL(/reason=archive/)
  })
})
