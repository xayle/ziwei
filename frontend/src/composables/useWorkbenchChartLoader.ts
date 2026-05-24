import { ref, type Ref } from 'vue'
import type { CaseOut } from '@/api/report'
import { computeFullBazi, computeZiwei } from '@/api/report'
import { getJieqi, type JieqiItemOut } from '@/api/bazi'
import type { ZiweiResponse } from '@/api/ziwei'
import { getWesternChart } from '@/api/western'
import { getCities, type CityModel } from '@/api/static-data'
import type { WorkbenchBaziLike } from './workbenchTypes'

type UseWorkbenchChartLoaderReturn = {
  localBazi: Ref<WorkbenchBaziLike | null>
  localZiwei: Ref<ZiweiResponse | null>
  baziLoading: Ref<boolean>
  ziweiLoading: Ref<boolean>
  baziError: Ref<string | null>
  ziweiError: Ref<string | null>
  loadBaziForCase: (currentCase: CaseOut) => Promise<void>
  loadZiweiForCase: (currentCase: CaseOut) => Promise<void>
}

function normalizeLocalIso(value: string | null | undefined): string {
  if (!value) return ''
  const trimmed = value.trim().replace(/\s+/, 'T')
  if (!trimmed) return ''
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(trimmed)) return `${trimmed}:00`
  return trimmed
}

function parseBirthLocal(currentCase: CaseOut): { year: number; month: number; day: number; hour: number; minute: number } | null {
  const normalized = normalizeLocalIso(currentCase.birth_dt_local)
  if (normalized && normalized.includes('T')) {
    const [datePart, timePart] = normalized.split('T')
    const [year, month, day] = datePart.split('-').map(Number)
    const [hour, minute] = (timePart ?? '').split(':').map(Number)
    if ([year, month, day, hour, minute].every(value => Number.isFinite(value))) {
      return { year, month, day, hour, minute }
    }
  }

  const raw = (currentCase.birth_dt_local ?? '').trim()
  const matched = raw.match(/(\d{4})-(\d{1,2})-(\d{1,2})(?:\D+(\d{1,2}):(\d{1,2}))?/)
  if (!matched) return null

  const year = Number(matched[1])
  const month = Number(matched[2])
  const day = Number(matched[3])
  const hour = Number(matched[4] ?? '12')
  const minute = Number(matched[5] ?? '0')
  if ([year, month, day, hour, minute].some(value => !Number.isFinite(value))) return null
  return { year, month, day, hour, minute }
}

function toZiweiGender(gender: string | null | undefined): '男' | '女' {
  return gender === 'female' ? '女' : '男'
}

function summarizeLongitudes(values: Record<string, number>, keys: string[]): string {
  return keys
    .filter(key => typeof values?.[key] === 'number')
    .map(key => `${key} ${values[key].toFixed(1)}°`)
    .join('，')
}

function getMoonPhaseText(sunLongitude: number, moonLongitude: number): string {
  const delta = ((moonLongitude - sunLongitude) % 360 + 360) % 360
  if (delta < 22.5 || delta >= 337.5) return '新月'
  if (delta < 67.5) return '娥眉月'
  if (delta < 112.5) return '上弦月'
  if (delta < 157.5) return '盈凸月'
  if (delta < 202.5) return '满月'
  if (delta < 247.5) return '亏凸月'
  if (delta < 292.5) return '下弦月'
  return '残月'
}

export function useWorkbenchChartLoader(currentYear: number): UseWorkbenchChartLoaderReturn {
  const localBazi = ref<WorkbenchBaziLike | null>(null)
  const localZiwei = ref<ZiweiResponse | null>(null)
  const baziLoading = ref(false)
  const ziweiLoading = ref(false)
  const baziError = ref<string | null>(null)
  const ziweiError = ref<string | null>(null)

  const jieqiByCaseId = ref<Record<string, JieqiItemOut[] | null>>({})
  const lunarByCaseId = ref<Record<string, { date: string; text: string } | null>>({})
  const westernAuxByCaseId = ref<Record<string, any | null | undefined>>({})

  let cachedCities: CityModel[] | null = null

  async function ensureCityGeoForCase(currentCase: CaseOut): Promise<void> {
    if (Number.isFinite(currentCase.lon) && currentCase.lon > 0) return
    if (!currentCase.city) return
    try {
      if (!cachedCities) cachedCities = await getCities()
      const city = cachedCities.find(item => item.name === currentCase.city)
      if (!city) return
      currentCase.lon = Number(city.lng)
    } catch (_error) {
    }
  }

  async function ensureJieqiForCase(currentCase: CaseOut): Promise<void> {
    if (jieqiByCaseId.value[currentCase.id] !== undefined) return
    try {
      const year = Number(currentCase.birth_dt_local?.slice(0, 4))
      if (!year || Number.isNaN(year)) {
        jieqiByCaseId.value = { ...jieqiByCaseId.value, [currentCase.id]: null }
        return
      }
      const rsp = await getJieqi(year)
      jieqiByCaseId.value = { ...jieqiByCaseId.value, [currentCase.id]: rsp.items ?? null }
    } catch (_error) {
      jieqiByCaseId.value = { ...jieqiByCaseId.value, [currentCase.id]: null }
    }
  }

  async function ensureLunarForCase(currentCase: CaseOut): Promise<void> {
    if (lunarByCaseId.value[currentCase.id] !== undefined) return
    try {
      const parsed = parseBirthLocal(currentCase)
      if (!parsed) {
        lunarByCaseId.value = { ...lunarByCaseId.value, [currentCase.id]: null }
        return
      }
      const date = new Date(parsed.year, parsed.month - 1, parsed.day, parsed.hour, parsed.minute)
      const text = new Intl.DateTimeFormat('zh-CN-u-ca-chinese', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      }).format(date)
      lunarByCaseId.value = {
        ...lunarByCaseId.value,
        [currentCase.id]: { date: `${parsed.year}-${parsed.month}-${parsed.day}`, text },
      }
    } catch (_error) {
      lunarByCaseId.value = { ...lunarByCaseId.value, [currentCase.id]: null }
    }
  }

  async function ensureWesternAuxForCase(currentCase: CaseOut): Promise<void> {
    if (westernAuxByCaseId.value[currentCase.id] !== undefined) return
    try {
      const parsed = parseBirthLocal(currentCase)
      if (!parsed) throw new Error('invalid birth_dt_local')
      const dt = `${parsed.year.toString().padStart(4, '0')}-${String(parsed.month).padStart(2, '0')}-${String(parsed.day).padStart(2, '0')}T${String(parsed.hour).padStart(2, '0')}:${String(parsed.minute).padStart(2, '0')}:00`
      const west = await getWesternChart({
        dt,
        lat: 31.2304,
        lon: currentCase.lon,
        tz: currentCase.tz,
      })

      const cnByEn: Record<string, string> = {
        Sun: '太阳', Moon: '月亮', Mercury: '水星', Venus: '金星', Mars: '火星',
        Jupiter: '木星', Saturn: '土星', Uranus: '天王星', Neptune: '海王星', Pluto: '冥王星',
        Earth: '地球',
      }

      const topPlanets = (west.planets ?? [])
        .slice(0, 5)
        .map(item => `${item.name_cn} ${item.sign_cn}${item.degree_str}`)
        .join('；')

      const sun = (west.planets ?? []).find(item => item.name_en === 'Sun')
      const moon = (west.planets ?? []).find(item => item.name_en === 'Moon')
      const ascMcSummary = `ASC ${west.ascendant?.sign_cn ?? '—'} ｜ MC ${west.midheaven?.sign_cn ?? '—'}`

      const aspectSummary = (west.aspects ?? [])
        .sort((a, b) => a.orb - b.orb)
        .slice(0, 3)
        .map(item => `${cnByEn[item.planet1] ?? item.planet1}-${cnByEn[item.planet2] ?? item.planet2} ${item.aspect_cn}(${item.orb.toFixed(1)}°)`)
        .join('；')

      const geoSummary = summarizeLongitudes(west.geocentric_longitudes, ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars'])
      const helioSummary = summarizeLongitudes(west.heliocentric_longitudes, ['Earth', 'Mercury', 'Venus', 'Mars'])

      westernAuxByCaseId.value = {
        ...westernAuxByCaseId.value,
        [currentCase.id]: {
          julianDay: west.julian_day,
          moonPhase: sun && moon ? getMoonPhaseText(sun.longitude, moon.longitude) : '待接入（无法读取日月黄经）',
          planetSummary: topPlanets || '—',
          ascMcSummary,
          coordinateSummary: `地心黄经：${geoSummary} ｜ 日心黄经：${helioSummary}`,
          aspectSummary: aspectSummary || '—',
        },
      }
    } catch (_error) {
      westernAuxByCaseId.value = { ...westernAuxByCaseId.value, [currentCase.id]: null }
    }
  }

  async function loadBaziForCase(currentCase: CaseOut) {
    baziLoading.value = true
    baziError.value = null
    localBazi.value = null
    try {
      await ensureCityGeoForCase(currentCase)
      const parsed = parseBirthLocal(currentCase)
      if (!parsed) throw new Error('出生时间格式无效')
      const y = String(parsed.year).padStart(4, '0')
      const m = String(parsed.month).padStart(2, '0')
      const d = String(parsed.day).padStart(2, '0')
      const hh = String(parsed.hour).padStart(2, '0')
      const mm = String(parsed.minute).padStart(2, '0')
      const dt = `${y}-${m}-${d}T${hh}:${mm}:00`
      const years = Array.from({ length: 16 }, (_, index) => currentYear - 5 + index)
      localBazi.value = await computeFullBazi({
        dt,
        lon: currentCase.lon,
        tz: currentCase.tz,
        mode: 'dual',
        solar_time_enabled: currentCase.solar_time_enabled,
        liunian_years: years,
      })
    } catch (error: unknown) {
      console.error('[WB] loadBaziForCase 捕获异常:', error)
      baziError.value = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? '八字计算失败'
      return
    } finally {
      baziLoading.value = false
    }
    await Promise.all([
      ensureJieqiForCase(currentCase),
      ensureLunarForCase(currentCase),
      ensureWesternAuxForCase(currentCase),
    ])
  }

  async function loadZiweiForCase(currentCase: CaseOut) {
    ziweiLoading.value = true
    ziweiError.value = null
    localZiwei.value = null
    try {
      await ensureCityGeoForCase(currentCase)
      const parsed = parseBirthLocal(currentCase)
      if (!parsed) throw new Error('出生时间格式无效')
      localZiwei.value = await computeZiwei({
        ...parsed,
        gender: toZiweiGender(currentCase.gender),
        liunian_year: currentYear,
        longitude: currentCase.lon,
        template_version: 'standard',
      })
    } catch (error: unknown) {
      ziweiError.value = (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail
        ?? (error as { message?: string }).message
        ?? '紫微计算失败'
    } finally {
      ziweiLoading.value = false
    }
  }

  return {
    localBazi,
    localZiwei,
    baziLoading,
    ziweiLoading,
    baziError,
    ziweiError,
    loadBaziForCase,
    loadZiweiForCase,
  }
}
