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
          `城市数据不完整（${records.length} 条）。请确认服务已启动后刷新页面。`,
        )
      }
      cached = records.map(mapCity)
      return cached
    })
    .catch((err: unknown) => {
      cached = null
      if (err instanceof CitiesLoadError) throw err
      throw new CitiesLoadError(
        '城市列表暂时无法加载，请确认服务已启动后刷新页面。',
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
