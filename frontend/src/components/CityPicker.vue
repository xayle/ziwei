<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { loadCityOptions, type CityOption } from '@/utils/citiesCache'

const props = defineProps<{
  modelValue?: number
  optional?: boolean
  initialCity?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number | undefined]
  'city-change': [info: { cityName: string; province: string; lon: number }]
}>()

const cities = ref<CityOption[]>([])
const citiesLoading = ref(true)
const citiesError = ref('')

const selectedProvince = ref('')
const selectedCity = ref('')

const provinces = computed<string[]>(() => {
  const fixed = ['北京市', '上海市', '天津市', '重庆市']
  const rest = [...new Set(cities.value.map((c) => c.province))]
    .filter((p) => !fixed.includes(p))
    .sort((a, b) => a.localeCompare(b, 'zh'))
  return [...fixed, ...rest]
})

const citiesInProvince = computed<CityOption[]>(() =>
  selectedProvince.value
    ? cities.value.filter((c) => c.province === selectedProvince.value)
    : [],
)

function onProvinceChange() {
  selectedCity.value = ''
  if (props.optional || !selectedProvince.value) {
    emit('update:modelValue', undefined)
  }
}

function onCityChange() {
  const city = cities.value.find((c) => c.name === selectedCity.value)
  if (city) {
    emit('update:modelValue', city.lng)
    emit('city-change', { cityName: city.name, province: city.province, lon: city.lng })
  } else {
    emit('update:modelValue', undefined)
  }
}

function applyCity(cityLabel: string | undefined) {
  if (!cityLabel || cities.value.length === 0) return
  const city = cities.value.find((c) => c.name === cityLabel)
  if (city) {
    selectedProvince.value = city.province
    selectedCity.value = city.name
    emit('update:modelValue', city.lng)
  }
}

onMounted(async () => {
  citiesLoading.value = true
  citiesError.value = ''
  try {
    cities.value = await loadCityOptions()
    applyCity(props.initialCity)
  } catch (err) {
    citiesError.value = err instanceof Error ? err.message : '城市列表加载失败，请确认后端已启动。'
  } finally {
    citiesLoading.value = false
  }
})

watch(() => props.initialCity, (newCity) => applyCity(newCity))
watch(cities, () => applyCity(props.initialCity))
</script>

<template>
  <label id="city-picker-province-label" for="city-picker-province">出生省份</label>
  <select
    id="city-picker-province"
    v-model="selectedProvince"
    :disabled="citiesLoading"
    data-testid="city-picker-province"
    @change="onProvinceChange"
  >
    <option value="">{{ optional ? '不填' : '-- 请选 --' }}</option>
    <option v-for="p in provinces" :key="p" :value="p">{{ p }}</option>
  </select>
  <label class="inner-lbl" id="city-picker-city-label" for="city-picker-city">城市</label>
  <select
    id="city-picker-city"
    v-model="selectedCity"
    :disabled="!selectedProvince || citiesLoading"
    data-testid="city-picker-city"
    @change="onCityChange"
  >
    <option value="">{{ selectedProvince ? '-- 请选 --' : '先选省份' }}</option>
    <option v-for="c in citiesInProvince" :key="c.name" :value="c.name">
      {{ c.name }}
    </option>
  </select>
  <span v-if="citiesLoading" class="hint">正在加载城市…（需后端 API，若久未响应请确认已启动 uvicorn :8000）</span>
  <span v-else-if="citiesError" class="hint hint--warn">{{ citiesError }}</span>
  <span v-else-if="modelValue !== undefined" class="hint" title="完整经度用于排盘">
    经度 {{ Number(modelValue).toFixed(4) }}°E（排盘用完整值）
  </span>
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
  outline: 2px solid transparent;
  border-color: var(--accent);
}
select:focus-visible {
  outline: 2px solid var(--accent, #8b6914);
  outline-offset: 2px;
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
.hint--warn {
  color: var(--brand-cinnabar);
}
</style>
