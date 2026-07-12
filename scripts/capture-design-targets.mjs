/**
 * T014 · 从 skin-preview.html 冻结设计门禁截图
 * 用法：node scripts/capture-design-targets.mjs
 */
import { chromium } from '../frontend/node_modules/playwright/index.mjs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const skinFile = path.join(root, 'docs/design/skin-preview.html')
const targetsDir = path.join(root, 'docs/design/targets')
const skinUrl = 'file:///' + skinFile.replace(/\\/g, '/')

const shots = [
  { hash: '#layout-bazi', out: 'bazi.png', width: 1120, height: 720 },
  { hash: '#layout-ziwei', out: 'ziwei.png', width: 1120, height: 640 },
  { hash: '#volumes', out: 'report-toc.png', width: 1120, height: 800 },
]

const browser = await chromium.launch()
const page = await browser.newPage()

for (const { hash, out, width, height } of shots) {
  await page.setViewportSize({ width, height })
  await page.goto(skinUrl + hash, { waitUntil: 'load' })
  await page.waitForTimeout(300)
  const el = await page.locator(hash.slice(1)).first()
  await el.screenshot({ path: path.join(targetsDir, out) })
  console.log('wrote', out)
}

await browser.close()
