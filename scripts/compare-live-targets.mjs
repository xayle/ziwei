/**
 * R079 · 对比实机截图与冻结 targets（尺寸 + 体积比，无像素库依赖）
 * 输入：docs/reports/live-targets-latest/live-*.png
 * 对照：docs/design/targets/{bazi,ziwei,report-toc}.png
 */
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const liveDir = path.join(root, 'docs/reports/live-targets-latest')
const frozenDir = path.join(root, 'docs/design/targets')
const reportPath = path.join(root, 'docs/reports/R079-targets-compare-latest.json')

const PAIRS = [
  { live: 'live-bazi.png', frozen: 'bazi.png' },
  { live: 'live-ziwei.png', frozen: 'ziwei.png' },
  { live: 'live-report-toc.png', frozen: 'report-toc.png' },
]

function pngMeta(filePath) {
  const buf = fs.readFileSync(filePath)
  if (buf.length < 24 || buf.toString('ascii', 1, 4) !== 'PNG') {
    throw new Error(`not a PNG: ${filePath}`)
  }
  return {
    width: buf.readUInt32BE(16),
    height: buf.readUInt32BE(20),
    bytes: buf.length,
  }
}

const results = []
let allPass = true

for (const { live, frozen } of PAIRS) {
  const livePath = path.join(liveDir, live)
  const frozenPath = path.join(frozenDir, frozen)
  const row = { live, frozen, ok: false, notes: [] }

  if (!fs.existsSync(livePath)) {
    row.notes.push(`missing live: ${livePath}`)
    allPass = false
    results.push(row)
    continue
  }
  if (!fs.existsSync(frozenPath)) {
    row.notes.push(`missing frozen: ${frozenPath}`)
    allPass = false
    results.push(row)
    continue
  }

  const L = pngMeta(livePath)
  const F = pngMeta(frozenPath)
  row.liveMeta = L
  row.frozenMeta = F

  const wRatio = L.width / F.width
  const hRatio = L.height / F.height
  if (wRatio < 0.9 || wRatio > 1.15) {
    row.notes.push(`width drift live ${L.width} vs frozen ${F.width}`)
  }
  if (L.height !== F.height) {
    row.notes.push(`height advisory: live ${L.height} vs frozen ${F.height} (viewport vs skin-preview crop)`)
  }
  const ratio = L.bytes / F.bytes
  row.sizeRatio = Number(ratio.toFixed(3))
  if (ratio < 0.35 || ratio > 2.8) {
    row.notes.push(`byte size ratio ${row.sizeRatio} outside [0.35, 2.8]`)
  }
  if (L.bytes < 8_000) {
    row.notes.push(`live screenshot too small (${L.bytes} bytes)`)
  }

  row.ok = row.notes.filter((n) => !n.startsWith('height advisory')).length === 0
  if (!row.ok) allPass = false
  results.push(row)
}

const payload = {
  generated_at: new Date().toISOString(),
  pass: allPass,
  pairs: results,
}

fs.mkdirSync(path.dirname(reportPath), { recursive: true })
fs.writeFileSync(reportPath, `${JSON.stringify(payload, null, 2)}\n`)
console.log(JSON.stringify(payload, null, 2))
process.exit(allPass ? 0 : 1)
