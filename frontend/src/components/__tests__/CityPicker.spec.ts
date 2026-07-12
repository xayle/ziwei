import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import CityPicker from '@/components/CityPicker.vue'
import { loadCityOptions } from '@/utils/citiesCache'

vi.mock('@/utils/citiesCache', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/utils/citiesCache')>()
  return {
    ...actual,
    loadCityOptions: vi.fn(),
  }
})

function buildMockCities() {
  const municipalities = [
    { name: '北京', province: '北京市', lng: 116.4, lat: 39.9 },
    { name: '上海', province: '上海市', lng: 121.4, lat: 31.2 },
    { name: '天津', province: '天津市', lng: 117.2, lat: 39.1 },
    { name: '重庆', province: '重庆市', lng: 106.5, lat: 29.5 },
  ]
  const provinces = [
    '广东省', '四川省', '浙江省', '江苏省', '山东省', '河南省', '湖北省', '湖南省',
    '福建省', '安徽省', '江西省', '辽宁省', '吉林省', '黑龙江省', '陕西省', '甘肃省',
    '云南省', '贵州省', '海南省', '山西省', '河北省', '广西壮族自治区', '内蒙古自治区',
    '宁夏回族自治区', '新疆维吾尔自治区', '西藏自治区', '青海省',
  ]
  const rows = [...municipalities]
  let i = 0
  while (rows.length < 337) {
    rows.push({
      name: `示例市${i + 1}`,
      province: provinces[i % provinces.length],
      lng: 100 + (i % 35),
      lat: 22 + (i % 18),
    })
    i += 1
  }
  return rows
}

describe('CityPicker provinces (A48)', () => {
  beforeEach(() => {
    vi.mocked(loadCityOptions).mockResolvedValue(buildMockCities())
  })

  it('loads at least 31 provinces from API mock', async () => {
    const wrapper = mount(CityPicker)
    await flushPromises()

    const provinceSelect = wrapper.findAll('select')[0]
    const options = provinceSelect.findAll('option')
    const labels = options.map((o) => o.text()).filter((t) => t && t !== '请选择省份')
    const unique = new Set(labels)

    expect(unique.size).toBeGreaterThanOrEqual(31)
    expect(labels).toContain('北京市')
    expect(labels).toContain('广东省')
  })
})
