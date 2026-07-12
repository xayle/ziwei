/**
 * R079 · 从实机 SPA 截取三页对照图（供 DS 与 docs/design/targets/*.png 并排）
 * 前置：cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
 * 用法：node scripts/capture-live-targets.mjs
 */
import { chromium } from '../frontend/node_modules/playwright/index.mjs'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const outDir = path.join(root, 'docs/reports/live-targets-latest')
const base = process.env.FUSHENG_APP_URL || 'http://127.0.0.1:5173/static/app/'

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

const shots = [
  { path: 'new/bazi', out: 'live-bazi.png', testId: 'bazi-layer-structure' },
  { path: 'new/ziwei', out: 'live-ziwei.png', testId: 'ziwei-layer-plate' },
  { path: 'report', out: 'live-report-toc.png', testId: 'report-vol5-chapter' },
]

fs.mkdirSync(outDir, { recursive: true })

const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1120, height: 800 } })
const page = await context.newPage()

await page.addInitScript((data) => {
  const profileId = 'capture-live-profile'
  const now = new Date().toISOString()
  localStorage.setItem('profile_active_id_v1', profileId)
  localStorage.setItem('profile_records_v1', JSON.stringify([
    { id: profileId, label: '截图档案', createdAt: now, updatedAt: now, data },
  ]))
  localStorage.setItem('profile_v1', JSON.stringify(data))
}, profileData)

for (const { path: appPath, out, testId } of shots) {
  await page.goto(base + appPath.replace(/^\//, ''), { waitUntil: 'networkidle', timeout: 60_000 })
  await page.getByTestId(testId).waitFor({ state: 'visible', timeout: 30_000 })
  await page.waitForTimeout(500)
  await page.screenshot({ path: path.join(outDir, out), fullPage: false })
  console.log('wrote', out)
}

await browser.close()
console.log('Done →', outDir)
