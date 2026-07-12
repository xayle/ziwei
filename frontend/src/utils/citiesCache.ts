import { getCities, type CityRecord } from '@/api/staticData'

export type CityOption = {
  name: string
  province: string
  lng: number
}

const MIN_CITIES = 300

let cached: CityOption[] | null = null
let loading: Promise<CityOption[]> | null = null

export class CitiesLoadError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'CitiesLoadError'
  }
}

function mapCity(record: CityRecord): CityOption {
  return {
    name: record.name,
    province: record.province,
    lng: record.lng,
  }
}

export async function loadCityOptions(): Promise<CityOption[]> {
  if (cached) return cached
  if (loading) return loading

  loading = getCities()
    .then((records) => {
      if (records.length < MIN_CITIES) {
        throw new CitiesLoadError(
          `城市数据不完整（${records.length} 条，需 ≥${MIN_CITIES}）。请确认后端已启动：python -m uvicorn app.main:app --port 8000`,
        )
      }
      cached = records.map(mapCity)
      return cached
    })
    .catch((err: unknown) => {
      cached = null
      if (err instanceof CitiesLoadError) throw err
      throw new CitiesLoadError(
        '城市列表加载失败。请确认后端 API 已启动（http://127.0.0.1:8000），勿使用离线 4 城兜底。',
      )
    })
    .finally(() => {
      loading = null
    })

  return loading
}

export function resetCityCacheForTests() {
  cached = null
  loading = null
}
