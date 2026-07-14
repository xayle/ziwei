import { test, expect } from '@playwright/test'
import { gotoApp } from './helpers/profile'

async function assertNoPageOverflow(page: import('@playwright/test').Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
  expect(overflow).toBeLessThanOrEqual(2)
}

test.describe('抖音落地页 LandingVolume', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
  })

  test('375px 卷首摘要可见且无页级横滚', async ({ page }) => {
    await gotoApp(page, 'landing?utm_source=douyin&utm_campaign=geju_hook&content_id=v_e2e')
    await expect(page.getByTestId('landing-volume')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('landing-cta')).toBeVisible()
    await expect(page.getByTestId('landing-disclaimer')).toBeVisible()
    await expect(page.getByTestId('snippet-hooks')).toBeVisible()
    await expect(page.getByTestId('snippet-copy-0')).toBeVisible()
    await expect(page.getByTestId('douyin-share-card')).toBeVisible()
    await expect(page.getByTestId('douyin-share-preview')).toContainText('浮生')
    await expect(page.getByText('浮生').first()).toBeVisible()
    await assertNoPageOverflow(page)
  })

  test('CTA 进入建档页并保留 utm', async ({ page }) => {
    await gotoApp(page, 'landing?utm_source=douyin&content_id=v_cta')
    await page.getByTestId('landing-cta').click()
    await expect(page).toHaveURL(/profile/)
    expect(page.url()).toContain('utm_source=douyin')
    expect(page.url()).toContain('content_id=v_cta')
  })
})
