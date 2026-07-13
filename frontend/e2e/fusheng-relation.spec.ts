import { test, expect } from '@playwright/test'
import { fillMinimalProfile, gotoApp } from './helpers/profile'

const MOCK_RELATION_RESPONSE = {
  schema_version: 'relation-compat@1.0',
  relation_type: 'couple',
  relation_type_label: '情侣合盘',
  person_a: {
    label: '我',
    gender: 'male',
    birth_solar: '1990-01-15T08:30:00',
    pillars_primary: {
      day: { stem: '癸', branch: '未' },
    },
  },
  person_b: {
    label: '对方',
    gender: 'female',
    birth_solar: '1992-05-20T14:00:00',
    pillars_primary: {
      day: { stem: '甲', branch: '子' },
    },
  },
  combined_score: 62.5,
  grade: '中',
  summary: 'E2E 情侣合盘：综合 62.5 分（中）。有缘相聚，宜沟通与规则并重。',
  summary_cards: [
    { id: 'c1', tone: 'support', text: '命宫六合' },
    { id: 'c2', tone: 'conflict', text: '日支丑未冲需调和' },
    { id: 'c3', tone: 'action', text: '固定每周沟通' },
  ],
  disclaimer_block: { text: '免责声明 E2E', version: '2026-07-12' },
  layers: {
    fact: { collapsed_default: false, sections: [] },
    cite: { collapsed_default: true, sections: [] },
    inference: { collapsed_default: true, sections: [] },
  },
  dimensions: [
    { id: 'day_branch', label: '日支', score: 0, max_score: 30, weight: 0.2, description: '丑未冲', layer: 'fact', engine: 'bazi' },
    { id: 'day_master', label: '日主', score: 30, max_score: 40, weight: 0.2, description: '比和', layer: 'fact', engine: 'bazi' },
  ],
  palace_cross: [
    { pair_id: 'p1', a_palace: '夫妻宫', b_palace: '命宫', relation_tag: '六合', summary: 'E2E 宫位', layer: 'fact' },
  ],
  timeline: [
    { year: 2025, label: '2025', summary: '平稳', risk_level: '低' },
    { year: 2026, label: '2026', summary: '值太岁', risk_level: '中' },
    { year: 2027, label: '2027', summary: '过渡', risk_level: '低' },
    { year: 2028, label: '2028', summary: '过渡', risk_level: '低' },
  ],
  action_items: [{ id: 'a1', text: '每周沟通', priority: 'P0' }],
  tensions: [],
  missing_fields: [],
}

test.describe('关系合盘 fusheng-relation', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/relation/full', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_RELATION_RESPONSE),
      })
    })
  })

  test('fusheng-relation-couple：情侣合盘页可提交并展示结果', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'relation/new?type=couple')
    await expect(page.getByTestId('relation-type-couple')).toHaveClass(/active/)
    await page.getByTestId('relation-partner-birth').fill('1992-05-20T14:00')
    await page.getByTestId('relation-run').click()
    await expect(page.getByTestId('relation-result')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText('E2E 情侣合盘')).toBeVisible()
    await expect(page.locator('.score-num')).toContainText('62.5')
  })

  test('fusheng-relation-friend：友人合盘类型可切换', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'relation/new?type=friend')
    await page.getByTestId('relation-type-friend').click()
    await expect(page.getByTestId('relation-type-friend')).toHaveClass(/active/)
    await page.getByTestId('relation-partner-birth').fill('1992-05-20T14:00')
    await page.getByTestId('relation-run').click()
    await expect(page.getByTestId('relation-result')).toBeVisible({ timeout: 10_000 })
  })

  test('fusheng-relation-partner：合伙合盘类型可切换', async ({ page }) => {
    await fillMinimalProfile(page)
    await gotoApp(page, 'relation/new?type=business_partner')
    await page.getByTestId('relation-type-business_partner').click()
    await page.getByTestId('relation-partner-birth').fill('1992-05-20T14:00')
    await page.getByTestId('relation-run').click()
    await expect(page.getByTestId('relation-result')).toBeVisible({ timeout: 10_000 })
  })

  test('fusheng-relation-export：结果页可导出 PDF/PNG', async ({ page }) => {
    await page.route('**/api/v1/relation/export/pdf', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        body: Buffer.from('%PDF-1.4 e2e'),
      })
    })
    await page.route('**/api/v1/relation/export/png', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'image/png',
        body: Buffer.from([0x89, 0x50, 0x4e, 0x47]),
      })
    })
    await fillMinimalProfile(page)
    await gotoApp(page, 'relation/new?type=couple')
    await page.getByTestId('relation-partner-birth').fill('1992-05-20T14:00')
    await page.getByTestId('relation-partner-lon').fill('122.117')
    await page.getByTestId('relation-run').click()
    await expect(page.getByTestId('relation-result')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByTestId('relation-export-pdf')).toBeVisible()
    await expect(page.getByTestId('relation-export-png')).toBeVisible()
    await page.getByTestId('relation-export-pdf').click()
    await page.getByTestId('relation-export-png').click()
  })
})
