<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

interface City {
  name: string
  province: string
  lng: number
}

const CITIES: City[] = [
  { name: '北京',    province: '北京市',          lng: 116.41 },
  { name: '天津',    province: '天津市',          lng: 117.19 },
  { name: '上海',    province: '上海市',          lng: 121.47 },
  { name: '重庆',    province: '重庆市',          lng: 106.55 },
  { name: '合肥',    province: '安徽省',          lng: 117.27 },
  { name: '福州',    province: '福建省',          lng: 119.30 },
  { name: '厦门',    province: '福建省',          lng: 118.09 },
  { name: '兰州',    province: '甘肃省',          lng: 103.83 },
  { name: '广州',    province: '广东省',          lng: 113.26 },
  { name: '深圳',    province: '广东省',          lng: 114.06 },
  { name: '南宁',    province: '广西壮族自治区',   lng: 108.37 },
  { name: '贵阳',    province: '贵州省',          lng: 106.63 },
  { name: '海口',    province: '海南省',          lng: 110.35 },
  { name: '石家庄',  province: '河北省',          lng: 114.50 },
  { name: '郑州',    province: '河南省',          lng: 113.65 },
  { name: '哈尔滨',  province: '黑龙江省',        lng: 126.69 },
  { name: '武汉',    province: '湖北省',          lng: 114.30 },
  { name: '长沙',    province: '湖南省',          lng: 112.98 },
  { name: '南京',    province: '江苏省',          lng: 118.77 },
  { name: '南昌',    province: '江西省',          lng: 115.93 },
  { name: '长春',    province: '吉林省',          lng: 125.33 },
  { name: '沈阳',    province: '辽宁省',          lng: 123.43 },
  { name: '大连',    province: '辽宁省',          lng: 121.60 },
  { name: '呼和浩特', province: '内蒙古自治区',   lng: 111.75 },
  { name: '银川',    province: '宁夏回族自治区',   lng: 106.27 },
  { name: '西宁',    province: '青海省',          lng: 101.78 },
  { name: '济南',    province: '山东省',          lng: 117.00 },
  { name: '青岛',    province: '山东省',          lng: 120.38 },
  { name: '太原',    province: '山西省',          lng: 112.55 },
  { name: '西安',    province: '陕西省',          lng: 108.95 },
  { name: '成都',    province: '四川省',          lng: 104.07 },
  { name: '乌鲁木齐', province: '新疆维吾尔自治区', lng: 87.62 },
  { name: '拉萨',    province: '西藏自治区',      lng:  91.11 },
  { name: '昆明',    province: '云南省',          lng: 102.73 },
  { name: '杭州',    province: '浙江省',          lng: 120.15 },
  { name: '宁波',    province: '浙江省',          lng: 121.56 },
]

const props = defineProps<{
  modelValue: number | undefined
  optional?: boolean
  initialCity?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number | undefined]
  'city-change': [info: { cityName: string; province: string; lon: number }]
}>()

const selectedProvince = ref('')
const selectedCity     = ref('')

// 省份列表：直辖市置顶，其余按汉字拼音排序
const provinces = computed<string[]>(() => {
  const fixed = ['北京市', '上海市', '天津市', '重庆市']
  const rest  = [...new Set(CITIES.map(c => c.province))]
    .filter(p => !fixed.includes(p))
    .sort((a, b) => a.localeCompare(b, 'zh'))
  return [...fixed, ...rest]
})

const citiesInProvince = computed<City[]>(() =>
  selectedProvince.value
    ? CITIES.filter(c => c.province === selectedProvince.value)
    : []
)

function onProvinceChange() {
  selectedCity.value = ''
  if (props.optional || !selectedProvince.value) {
    emit('update:modelValue', undefined)
  }
}

function onCityChange() {
  const city = CITIES.find(c => c.name === selectedCity.value)
  if (city) {
    emit('update:modelValue', city.lng)
    emit('city-change', { cityName: city.name, province: city.province, lon: city.lng })
  } else {
    emit('update:modelValue', undefined)
  }
}

function applyCity(cityLabel: string | undefined) {
  if (!cityLabel) return
  const city = CITIES.find(c => c.name === cityLabel)
  if (city) {
    selectedProvince.value = city.province
    selectedCity.value     = city.name
    emit('update:modelValue', city.lng)
  }
}

onMounted(() => applyCity(props.initialCity))

// 当 initialCity prop 变化时（父组件动态传入）同步更新
watch(() => props.initialCity, (newCity) => applyCity(newCity))
</script>

<template>
  <label>出生省份</label>
  <select v-model="selectedProvince" @change="onProvinceChange">
    <option value="">{{ optional ? '不填' : '-- 请选 --' }}</option>
    <option v-for="p in provinces" :key="p" :value="p">{{ p }}</option>
  </select>
  <label class="inner-lbl">城市</label>
  <select
    v-model="selectedCity"
    :disabled="!selectedProvince"
    @change="onCityChange"
  >
    <option value="">{{ selectedProvince ? '-- 请选 --' : '先选省份' }}</option>
    <option v-for="c in citiesInProvince" :key="c.name" :value="c.name">
      {{ c.name }}
    </option>
  </select>
  <span v-if="modelValue !== undefined" class="hint">经度 {{ modelValue.toFixed(2) }}°E</span>
  <span v-else-if="optional" class="hint">选填，用于真太阳时修正</span>
</template>

<style scoped>
select {
  padding: 7px 10px;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-md);
  background-color: var(--bg-card, #fff);
  cursor: pointer;
}
select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
select:focus {
  outline: none;
  border-color: var(--accent);
}
.inner-lbl {
  width: auto !important;
  margin-left: var(--sp-2, 4px) !important;
  font-size: var(--fs-md);
  color: var(--text-2);
  flex-shrink: 0;
}
.hint {
  color: var(--text-3);
  font-size: var(--fs-sm);
}
</style>
