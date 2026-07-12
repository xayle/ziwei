#!/usr/bin/env node
/**
 * Compare one birth against iztro (stdout JSON).
 * Usage: echo '{"year":1990,"month":5,"day":15,"hour":8,"minute":30,"gender":"男"}' | node scripts/iztro_compare_birth.mjs
 */
import { readFileSync } from 'node:fs'
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

function loadCalibration(birth) {
  try {
    const data = JSON.parse(readFileSync(GT_PATH, 'utf-8'))
    for (const c of data.cases || []) {
      const b = c.birth
      if (
        b.year === birth.year && b.month === birth.month && b.day === birth.day
        && b.hour === birth.hour && (b.minute ?? 0) === (birth.minute ?? 0)
        && b.gender === birth.gender && c.iztro_calibration
      ) {
        return c.iztro_calibration
      }
    }
  } catch {
    /* ignore */
  }
  return null
}

function iztroMain(astrolabe) {
  const main = {}
  const lp = astrolabe.palace('命宫')
  const lifePalaceGz = `${lp?.heavenlyStem ?? ''}${lp?.earthlyBranch ?? ''}`
  for (let i = 0; i < 12; i++) {
    const p = astrolabe.palace(i)
    for (const s of p.majorStars || []) {
      if (MAIN_STARS.includes(s.name)) main[s.name] = p.earthlyBranch
    }
  }
  return { main, lifePalaceGz }
}

function countMainMatches(engineMain, iztroMainMap) {
  let n = 0
  for (const star of MAIN_STARS) {
    if (engineMain[star] && engineMain[star] === iztroMainMap[star]) n += 1
  }
  return n
}

function yearDivideLabel(v) {
  return v === 'normal' ? '正月初一换年' : '立春换年'
}

function dayDivideLabel(v) {
  if (v === 'forward') return '子时换日（forward）'
  if (v === 'current') return '当日子时'
  return '公历次日换日（solar_next）'
}

function buildDualTrack(astro, birth, engineMain) {
  const date = `${birth.year}-${birth.month}-${birth.day}`
  const gender = birth.gender === '男' ? '男' : '女'
  const isLateZi = birth.hour >= 23 || birth.hour < 1
  const altTi = isLateZi ? 12 : hourToTimeIndex(birth.hour, birth.minute ?? 0)
  const astrolabe = astro.bySolar(date, altTi, gender, true, 'zh-CN')
  const { main, lifePalaceGz } = iztroMain(astrolabe)
  const mainMatch = countMainMatches(engineMain, main)
  return {
    label: 'iztro 对照轨',
    year_divide: 'normal',
    day_divide: 'forward',
    life_palace_gz: lifePalaceGz,
    main_match: mainMatch,
    main_total: MAIN_STARS.length,
    note: '立春前/晚子时边界：正月初一换年 + 子时换日（forward）；不覆盖引擎主盘。',
  }
}

async function main() {
  const raw = readFileSync(0, 'utf-8').trim()
  const birth = JSON.parse(raw)
  const engineMain = birth.engine_main || {}
  const engineLifeGz = birth.engine_life_palace_gz || ''
  const yearDivide = birth.year_divide || 'lichun'
  const dayDivide = birth.day_divide || 'solar_next'

  let astro
  try {
    const entry = join(IZTRO_DIR, 'node_modules', 'iztro', 'lib', 'index.js')
    ;({ astro } = await import(pathToFileURL(entry).href))
  } catch {
    process.stdout.write(JSON.stringify({ available: false, status: 'skipped' }))
    process.exit(0)
  }

  const cal = loadCalibration(birth)
  const ti = cal?.timeIndex ?? hourToTimeIndex(birth.hour, birth.minute ?? 0)
  const fixLeap = cal?.fixLeap !== false
  const date = `${birth.year}-${birth.month}-${birth.day}`
  const gender = birth.gender === '男' ? '男' : '女'
  const astrolabe = astro.bySolar(date, ti, gender, fixLeap, 'zh-CN')
  const { main, lifePalaceGz } = iztroMain(astrolabe)

  const mainMatch = countMainMatches(engineMain, main)
  const lpOk = !engineLifeGz || engineLifeGz === lifePalaceGz
  let status = 'unknown'
  if (lpOk && mainMatch === MAIN_STARS.length) status = 'main_match'
  else if (lpOk && mainMatch === 0) status = 'life_palace_only'
  else if (!lpOk) status = 'life_palace_mismatch'
  else status = `partial_main_${mainMatch}`

  let dualTrack = null
  if (status === 'life_palace_mismatch') {
    dualTrack = buildDualTrack(astro, birth, engineMain)
  }

  let advisory = null
  if (status === 'life_palace_only') {
    advisory = '与 iztro 主星未对齐：命宫一致但十四主星坐标分歧，可能为安星流派差异，请以引擎/人工复核为准。'
  } else if (status === 'life_palace_mismatch') {
    advisory = (
      `与 iztro 命宫未对齐：引擎主盘 ${engineLifeGz || '—'}（${yearDivideLabel(yearDivide)} · ${dayDivideLabel(dayDivide)}）`
      + ` vs iztro ${lifePalaceGz}。`
      + (dualTrack
        ? ` 对照轨 ${dualTrack.life_palace_gz}（正月初一 · forward）主星 ${dualTrack.main_match}/14。`
        : '')
      + ' 典型边界见 ZW03 双轨说明。'
    )
  } else if (status !== 'main_match') {
    advisory = `与 iztro 主星部分一致（${mainMatch}/14），辅星或边界口径可能存在差异。`
  }

  const out = {
    available: true,
    status,
    main_match: mainMatch,
    main_total: MAIN_STARS.length,
    life_palace_match: lpOk,
    engine_life_palace_gz: engineLifeGz || null,
    iztro_life_palace_gz: lifePalaceGz,
    time_index: ti,
    fix_leap: fixLeap,
    advisory,
    dual_track: dualTrack,
  }
  process.stdout.write(JSON.stringify(out))
}

main().catch((err) => {
  process.stderr.write(String(err))
  process.exit(1)
})
