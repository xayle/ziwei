#!/usr/bin/env node
/**
 * Advisory horoscope cross-check: c2 engine dayun vs iztro horoscope().
 *
 * Usage:
 *   node scripts/verify_ziwei_horoscope_iztro.mjs [--case WM01] [--query 2026-7-12]
 *   make verify-horoscope-iztro
 *
 * Non-blocking: records diffs to docs/reports/ziwei-horoscope-iztro-diff-latest.json
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { dirname, join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..')
const WENMO_PATH = join(ROOT, 'data', 'imported', 'wenmo_reference_cases.json')
const IZTRO_DIR = join(__dirname, 'iztro')
const ENGINE_SCRIPT = join(__dirname, 'ziwei_horoscope_engine.py')
const OUT_PATH = join(ROOT, 'docs', 'reports', 'ziwei-horoscope-iztro-diff-latest.json')

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

function loadIztro() {
  const entry = join(IZTRO_DIR, 'node_modules', 'iztro', 'lib', 'index.js')
  return import(pathToFileURL(entry).href)
}

function loadCases(caseFilter) {
  const data = JSON.parse(readFileSync(WENMO_PATH, 'utf-8'))
  const cases = (data.cases || []).filter((c) => !caseFilter || c.id === caseFilter)
  if (!cases.length) {
    throw new Error(`No wenmo cases found${caseFilter ? ` for ${caseFilter}` : ''}`)
  }
  return cases
}

function engineSnapshot(caseRow, queryDates) {
  const proc = spawnSync(
    process.platform === 'win32' ? 'python' : 'python3',
    [
      ENGINE_SCRIPT,
      '--case-json',
      JSON.stringify(caseRow),
      '--query-dates',
      queryDates.join(','),
    ],
    { cwd: ROOT, encoding: 'utf-8', timeout: 60_000, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } },
  )
  if (proc.status !== 0) {
    throw new Error(proc.stderr || proc.stdout || 'engine snapshot failed')
  }
  return JSON.parse(proc.stdout)
}

function defaultQueryDates(caseRow) {
  const y = caseRow.birth_year
  return [`${y + 14}-6-15`, `${y + 25}-6-29`, `${y + 33}-7-12`]
}

function compareSample(engineSample, iztroHoroscope) {
  const decadal = iztroHoroscope?.decadal
  const yearly = iztroHoroscope?.yearly
  const iztroDecadalGz = decadal ? `${decadal.heavenlyStem}${decadal.earthlyBranch}` : null
  const iztroYearlyGz = yearly ? `${yearly.heavenlyStem}${yearly.earthlyBranch}` : null
  const engineDecadalGz = engineSample.decadal_ganzhi
  const decadalMatch = iztroDecadalGz === engineDecadalGz
  return {
    query_date: engineSample.query_date,
    virtual_age: engineSample.virtual_age,
    engine_decadal_ganzhi: engineDecadalGz,
    engine_decadal_palace: engineSample.decadal_palace,
    iztro_decadal_ganzhi: iztroDecadalGz,
    iztro_yearly_ganzhi: iztroYearlyGz,
    decadal_match: decadalMatch,
    trust_level: 'advisory',
  }
}

async function main() {
  const args = process.argv.slice(2)
  const caseFilter = args.includes('--case') ? args[args.indexOf('--case') + 1] : null
  const queryOverride = args.includes('--query') ? args[args.indexOf('--query') + 1] : null

  let astro
  try {
    ;({ astro } = await loadIztro())
  } catch (e) {
    console.error('SKIP: iztro not installed. Run: make verify-iztro-install')
    process.exit(2)
  }

  const cases = loadCases(caseFilter)
  const report = []

  for (const caseRow of cases) {
    const queryDates = queryOverride ? [queryOverride] : defaultQueryDates(caseRow)
    const engine = engineSnapshot(caseRow, queryDates)
    const gender = caseRow.gender === 'female' || caseRow.gender === '女' ? '女' : '男'
    const date = `${caseRow.birth_year}-${caseRow.birth_month}-${caseRow.birth_day}`
    const ti = hourToTimeIndex(caseRow.birth_hour, caseRow.birth_minute ?? 0)
    const astrolabe = astro.bySolar(date, ti, gender, true, 'zh-CN')

    const samples = []
    let decadalMatches = 0
    for (const engineSample of engine.samples) {
      const horoscope = astrolabe.horoscope(engineSample.query_date)
      const row = compareSample(engineSample, horoscope)
      if (row.decadal_match) decadalMatches += 1
      samples.push(row)
      console.log(
        `${caseRow.id} ${row.query_date} age=${row.virtual_age} `
        + `engine=${row.engine_decadal_ganzhi} iztro=${row.iztro_decadal_ganzhi} `
        + `${row.decadal_match ? 'MATCH' : 'DIFF'}`,
      )
    }

    report.push({
      id: caseRow.id,
      trust_level: 'advisory',
      time_index: ti,
      query_dates: queryDates,
      decadal_matches: decadalMatches,
      decadal_total: samples.length,
      engine_dayun_items: engine.dayun_items,
      samples,
    })
  }

  const payload = {
    generated_at: new Date().toISOString(),
    trust_level: 'advisory',
    note: 'Decadal diffs are expected across schools; non-blocking advisory only.',
    report,
  }
  writeFileSync(OUT_PATH, JSON.stringify(payload, null, 2))
  console.log(`Report: ${OUT_PATH}`)
  // Advisory track: exit 0 even when decadal mismatches exist.
  process.exit(0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
