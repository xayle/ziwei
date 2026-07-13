import { expect, type Page } from '@playwright/test'

/** 在 SPA base（/static/app/）内导航 */
export async function gotoApp(page: Page, path = '') {
  const clean = path.replace(/^\//, '')
  await page.goto(clean || '.')
}

/** 填写最小可排盘档案（北京 1990-01-15 08:30 男） */
export async function fillMinimalProfile(page: Page) {
  await gotoApp(page, 'profile')

  await page.getByTestId('profile-birth-dt').fill('1990-01-15T08:30')
  await page.getByTestId('profile-gender').selectOption('male')

  const cityRow = page.locator('.city-picker-row').first()
  await cityRow.scrollIntoViewIfNeeded()
  const provinceSelect = cityRow.locator('select').first()
  await expect(provinceSelect).toBeEnabled({ timeout: 15_000 })
  await provinceSelect.selectOption('北京市')
  const citySelect = cityRow.locator('select').nth(1)
  await expect(citySelect).toBeEnabled({ timeout: 10_000 })
  await expect(citySelect.locator('option', { hasText: '北京' })).toHaveCount(1, { timeout: 10_000 })
  await citySelect.selectOption('北京')
  await expect(page.getByText(/经度\s+116\.\d+°E/).first()).toBeVisible({ timeout: 10_000 })

  await page.getByTestId('profile-save').click()
  await expect(page.getByTestId('profile-bazi')).toBeEnabled({ timeout: 15_000 })
}

export async function seedLoggedInProfileWithRemoteCase(page: Page, caseId = 'case-e2e-001') {
  const profileId = 'profile-e2e-001'
  const now = new Date().toISOString()
  const profileData = {
    birthDt: '1990-01-15T08:30',
    lon: 116.4074,
    cityName: '北京',
    province: '北京市',
    tz: 'Asia/Shanghai',
    gender: 'male',
    mode: 'dual',
    solarTime: false,
    surname: '',
    givenName: '',
    calendarMode: 'gregorian',
    isLeapMonth: false,
    yearDivide: 'lichun',
    dayDivide: 'solar_next',
    lateZishi: true,
    ziDayRule: 'sxtwl',
    birthTimePrecision: 'exact',
    unknownTimeFallback: 'midday',
    currentCityName: '',
    currentProvince: '',
    currentTz: 'Asia/Shanghai',
    focusTopic: '',
    cityTier: '',
    industry: '',
  }

  await page.addInitScript(({ profileId, caseId, now, profileData }) => {
    localStorage.clear()
    localStorage.setItem('token', 'e2e-test-token')
    localStorage.setItem('refresh_token', 'e2e-test-refresh')
    localStorage.setItem('username', 'e2e-user')
    localStorage.setItem('profile_active_id_v1', profileId)
    localStorage.setItem('profile_records_v1', JSON.stringify([
      {
        id: profileId,
        label: 'E2E 档案',
        createdAt: now,
        updatedAt: now,
        remoteCaseId: caseId,
        data: profileData,
      },
    ]))
    localStorage.setItem('profile_v1', JSON.stringify(profileData))
  }, { profileId, caseId, now, profileData })
}

export async function seedArchiveReadyProfile(page: Page) {
  const profileId = 'profile-e2e-ready'
  const now = new Date().toISOString()
  const profileData = {
    birthDt: '1990-01-15T08:30',
    lon: 116.4074,
    cityName: '北京',
    province: '北京市',
    tz: 'Asia/Shanghai',
    gender: 'male',
    mode: 'dual',
    solarTime: false,
    surname: '',
    givenName: '',
    calendarMode: 'gregorian',
    isLeapMonth: false,
    yearDivide: 'lichun',
    dayDivide: 'solar_next',
    lateZishi: true,
    ziDayRule: 'sxtwl',
    birthTimePrecision: 'exact',
    unknownTimeFallback: 'midday',
    currentCityName: '',
    currentProvince: '',
    currentTz: 'Asia/Shanghai',
    focusTopic: '',
    cityTier: '',
    industry: '',
  }

  await page.addInitScript(({ profileId, now, profileData }) => {
    localStorage.clear()
    localStorage.setItem('profile_active_id_v1', profileId)
    localStorage.setItem('profile_records_v1', JSON.stringify([
      {
        id: profileId,
        label: 'E2E 就绪档案',
        createdAt: now,
        updatedAt: now,
        data: profileData,
      },
    ]))
    localStorage.setItem('profile_v1', JSON.stringify(profileData))
  }, { profileId, now, profileData })
}
