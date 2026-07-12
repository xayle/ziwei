import { getCities, type CityRecord } from '@/api/staticData'

export type CityOption = {
  name: string
  province: string
  lng: number
}

const FALLBACK_CITIES: CityOption[] = [
  { name: '北京', province: '北京市', lng: 116.41 },
  { name: '上海', province: '上海市', lng: 121.47 },
  { name: '广州', province: '广东省', lng: 113.26 },
  { name: '成都', province: '四川省', lng: 104.07 },
]

let cached: CityOption[] | null = null
let loading: Promise<CityOption[]> | null = null

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
      cached = records.length > 0 ? records.map(mapCity) : [...FALLBACK_CITIES]
      return cached
    })
    .catch(() => {
      cached = [...FALLBACK_CITIES]
      return cached
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
