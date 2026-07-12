#!/usr/bin/env node
/**
 * Compare c2 ziwei engine coordinates vs iztro for ZW ground truth cases.
 *
 * Usage:
 *   node scripts/verify_ziwei_iztro.mjs [--case ZW01] [--calibrate] [--write-verified]
 *   node scripts/verify_ziwei_iztro.mjs --youbi=hour   # 右弼按 hour 口径对照 iztro（辅煞 0 diff）
 *
 * Per-case `iztro_calibration` in data/ziwei_ground_truth.json overrides naive hour→timeIndex.
 * `--write-verified` only marks cases with life-palace match AND 14/14 main-star agreement.
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..')
const GT_PATH = join(ROOT, 'data', 'ziwei_ground_truth.json')
const IZTRO_DIR = join(__dirname, 'iztro')

const MAIN_STARS = [
  '紫微', '天机', '太阳', '武曲', '天同', '廉贞', '天府', '太阴',
  '贪狼', '巨门', '天相', '天梁', '七杀', '破军',
]
const EXTENDED_AUX = ['天魁', '天钺', '火星', '铃星', '文昌', '文曲', '左辅', '右弼', '擎羊', '陀罗']
const BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

/** Solar clock hour → iztro timeIndex (0=早子 … 12=晚子) */
function hourToTimeIndex(hour, minute = 0) {
  const h = hour + minute / 60
  if (h >= 23 || h < 1) return h >= 23 ? 12 : 0
  if (h < 3) return 1
  if (h < 5) return 2
  if (h < 7) return 3
  if (h < 9) return 4
  if (h < 11) return 5
  if (h < 13) return 6
  if (h < 15) return 7
  if (h < 17) return 8
  if (h < 19) return 9
  if (h < 21) return 10
  return 11
}

function parseYoubiMode(args) {
  const eq = args.find((a) => a.startsWith('--youbi='))
  if (eq) return eq.split('=')[1] || 'month'
  const idx = args.indexOf('--youbi')
  if (idx >= 0 && args[idx + 1]) return args[idx + 1]
  return 'month'
}

function shiftBranch(branch, delta) {
  const i = BRANCHES.indexOf(branch)
  if (i < 0) return branch
  return BRANCHES[(i + delta + 12) % 12]
}

/** golden 存 month 口径右弼；iztro 依生时安右弼 ≈ hour 口径（相对 month 顺移一宫） */
function auxExpectedForYoubi(auxExpected, youbiMode) {
  if (youbiMode !== 'hour' || !auxExpected['右弼']) return auxExpected
  return { ...auxExpected, 右弼: shiftBranch(auxExpected['右弼'], 1) }
}

function loadIztro() {
  const entry = join(IZTRO_DIR, 'node_modules', 'iztro', 'lib', 'index.js')
  return import(pathToFileURL(entry).href)
}

function resolveIztroParams(c) {
  const cal = c.iztro_calibration
  if (cal && typeof cal.timeIndex === 'number') {
    return {
      timeIndex: cal.timeIndex,
      fixLeap: cal.fixLeap !== false,
      source: 'calibration',
    }
  }
  const b = c.birth
  return {
    timeIndex: hourToTimeIndex(b.hour, b.minute ?? 0),
    fixLeap: true,
    source: 'hour_default',
  }
}

function iztroPositions(astrolabe) {
  const main = {}
  const aux = {}
  const lifePalace = astrolabe.palace('命宫')
  const lifePalaceGz = `${lifePalace?.heavenlyStem ?? ''}${lifePalace?.earthlyBranch ?? ''}`
  for (let i = 0; i < 12; i++) {
    const p = astrolabe.palace(i)
    const br = p.earthlyBranch
    for (const s of p.majorStars || []) {
      if (MAIN_STARS.includes(s.name)) main[s.name] = br
    }
    for (const s of p.minorStars || []) {
      if (EXTENDED_AUX.includes(s.name)) aux[s.name] = br
    }
    for (const s of p.adjectiveStars || []) {
      if (EXTENDED_AUX.includes(s.name)) aux[s.name] = br
    }
  }
  return { main, aux, lifePalaceGz }
}

function countMainMatches(expected, actual) {
  let n = 0
  for (const star of MAIN_STARS) {
    if (expected[star] && expected[star] === actual[star]) n += 1
  }
  return n
}

function diffMaps(expected, actual, label) {
  const mismatches = []
  for (const [star, br] of Object.entries(expected || {})) {
    if (actual[star] === undefined) {
      mismatches.push(`${label} ${star}: missing in iztro`)
    } else if (actual[star] !== br) {
      mismatches.push(`${label} ${star}: engine=${br} iztro=${actual[star]}`)
    }
  }
  return mismatches
}

function calibrateCase(astro, c) {
  const b = c.birth
  const date = `${b.year}-${b.month}-${b.day}`
  const gender = b.gender === '男' ? '男' : '女'
  const expLp = c.life_palace_gz
  let best = null
  for (let ti = 0; ti <= 12; ti += 1) {
    for (const fixLeap of [true, false]) {
      const astrolabe = astro.bySolar(date, ti, gender, fixLeap, 'zh-CN')
      const { main, lifePalaceGz } = iztroPositions(astrolabe)
      const lpOk = lifePalaceGz === expLp
      const mainMatch = countMainMatches(c.main_stars, main)
      const score = (lpOk ? 100 : 0) + mainMatch
      if (!best || score > best.score) {
        best = { timeIndex: ti, fixLeap, lifePalaceGz, lpOk, mainMatch, score }
      }
    }
  }
  return best
}

async function main() {
  const args = process.argv.slice(2)
  const caseFilter = args.includes('--case') ? args[args.indexOf('--case') + 1] : null
  const writeVerified = args.includes('--write-verified')
  const calibrate = args.includes('--calibrate')
  const youbiMode = parseYoubiMode(args)

  let astro
  try {
    ;({ astro } = await loadIztro())
  } catch (e) {
    console.error('SKIP: iztro not installed. Run: make verify-iztro-install')
    process.exit(2)
  }

  const data = JSON.parse(readFileSync(GT_PATH, 'utf-8'))
  const cases = (data.cases || []).filter((c) => !caseFilter || c.id === caseFilter)
  let totalMismatch = 0
  const report = []

  if (calibrate) {
    console.log('Calibrating iztro timeIndex / fixLeap per case…')
    for (const c of cases) {
      const best = calibrateCase(astro, c)
      c.iztro_calibration = {
        timeIndex: best.timeIndex,
        fixLeap: best.fixLeap,
        life_palace_match: best.lpOk,
        main_star_match: best.mainMatch,
        iztro_life_palace_gz: best.lifePalaceGz,
        calibrated_at: new Date().toISOString().slice(0, 10),
      }
      console.log(
        `${c.id}: ti=${best.timeIndex} fixLeap=${best.fixLeap} `
        + `lp=${best.lpOk ? 'OK' : 'MISS'} main=${best.mainMatch}/14`,
      )
      if (best.lpOk && best.mainMatch === MAIN_STARS.length) {
        c.iztro_status = 'main_match'
      } else if (best.lpOk && best.mainMatch === 0) {
        c.iztro_status = 'life_palace_only'
      } else if (!best.lpOk) {
        c.iztro_status = 'life_palace_mismatch'
      } else {
        c.iztro_status = `partial_main_${best.mainMatch}`
      }
    }
    writeFileSync(GT_PATH, JSON.stringify(data, null, 2), 'utf-8')
    console.log('Wrote iztro_calibration to ziwei_ground_truth.json')
  }

  if (youbiMode === 'hour') {
    console.log('youbi_mode=hour：右弼按 hour 口径（golden 顺移一宫）对照 iztro')
  }

  for (const c of cases) {
    const b = c.birth
    const date = `${b.year}-${b.month}-${b.day}`
    const gender = b.gender === '男' ? '男' : '女'
    const { timeIndex: ti, fixLeap, source } = resolveIztroParams(c)
    const astrolabe = astro.bySolar(date, ti, gender, fixLeap, 'zh-CN')
    const { main, aux, lifePalaceGz } = iztroPositions(astrolabe)
    const mainMatch = countMainMatches(c.main_stars, main)
    const lpOk = lifePalaceGz === c.life_palace_gz
    const mainDiff = diffMaps(c.main_stars, main, '主星')
    let auxExpected = { ...(c.aux_stars || {}), ...(c.extended_aux || {}) }
    auxExpected = auxExpectedForYoubi(auxExpected, youbiMode)
    const auxDiff = diffMaps(auxExpected, aux, '辅煞')
    const mismatches = [...mainDiff, ...auxDiff]
    const mainOk = mainMatch === MAIN_STARS.length
    const auxOk = auxDiff.length === 0
    const ok = mainOk && lpOk && auxOk
    if (!ok) totalMismatch += mismatches.length
    report.push({
      id: c.id,
      ok,
      lpOk,
      mainMatch,
      mainTotal: MAIN_STARS.length,
      auxOk,
      youbiMode,
      mismatches,
      timeIndex: ti,
      fixLeap,
      paramSource: source,
      iztroLifePalaceGz: lifePalaceGz,
    })
    let status = 'PASS'
    if (!mainOk || !lpOk) status = 'FAIL'
    else if (!auxOk) status = youbiMode === 'hour' ? 'PARTIAL(aux)' : 'PARTIAL(aux)'
    else if (mainOk && lpOk && auxOk) status = 'PASS'
    console.log(
      `${c.id}: ${status} main=${mainMatch}/14 lp=${lpOk ? 'OK' : `${lifePalaceGz}≠${c.life_palace_gz}`} `
      + `aux=${auxOk ? 'OK' : `${auxDiff.length} diff`} youbi=${youbiMode} `
      + `(ti=${ti} fixLeap=${fixLeap})`,
    )
    for (const m of mismatches.slice(0, 6)) console.log(`  - ${m}`)
    if (mismatches.length > 6) console.log(`  ... +${mismatches.length - 6} more`)

    if (writeVerified && mainOk && lpOk) {
      c.verified = true
      c.verification_method = 'iztro_diff'
      c.notes = `iztro ${date} ti=${ti} fixLeap=${fixLeap} 主星14/14一致`
    } else if (writeVerified && (!mainOk || !lpOk)) {
      console.log('  skip --write-verified: need 14/14 main + life palace match')
    }
  }

  if (writeVerified) {
    writeFileSync(GT_PATH, JSON.stringify(data, null, 2), 'utf-8')
    console.log('Wrote verified flags to ziwei_ground_truth.json')
  }

  const outPath = join(ROOT, 'docs', 'reports', 'ziwei-iztro-diff-latest.json')
  writeFileSync(
    outPath,
    JSON.stringify({ generated_at: new Date().toISOString(), youbi_mode: youbiMode, report }, null, 2),
  )
  console.log(`Report: ${outPath}`)
  process.exit(totalMismatch > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
