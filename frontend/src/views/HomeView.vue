<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import CityPicker from '@/components/CityPicker.vue'

const router  = useRouter()
const profile = useProfileStore()

// ── 表单字段 ──────────────────────────────────────────────────
const name     = ref(profile.surname  || '')
const birthDt  = ref(profile.birthDt  || '1990-07-17T12:25')
const gender   = ref<'male' | 'female'>(
  (profile.gender === 'male' || profile.gender === 'female') ? profile.gender : 'female',
)
const cityName = ref(profile.cityName || '南京')
const province = ref(profile.province || '江苏省')
const lon      = ref<number | undefined>(profile.lon)
const initCity = ref(profile.cityName || '南京')

function onCityChange(e: { cityName: string; province: string; lon: number }) {
  lon.value      = e.lon
  cityName.value = e.cityName
  province.value = e.province
  initCity.value = e.cityName
}

// ── 服务定义 ──────────────────────────────────────────────────
type ServiceKey = 'bazi' | 'ziwei' | 'name' | 'compat'

const services: { key: ServiceKey; tabChar: string; label: string; route: string }[] = [
  { key: 'bazi',   tabChar: '八', label: '四柱八字', route: '/bazi'   },
  { key: 'ziwei',  tabChar: '紫', label: '紫微斗数', route: '/ziwei'  },
  { key: 'name',   tabChar: '名', label: '姓名分析', route: '/name'   },
  { key: 'compat', tabChar: '合', label: '合婚分析', route: '/compat' },
]

const activeService = ref<ServiceKey>('bazi')

// ── 开始分析 ──────────────────────────────────────────────────
function startAnalysis() {
  profile.setProfile({
    surname:  name.value,
    birthDt:  birthDt.value,
    gender:   gender.value,
    cityName: cityName.value,
    province: province.value,
    lon:      lon.value,
  })
  router.push(services.find(s => s.key === activeService.value)!.route)
}

onMounted(() => {
  name.value     = profile.surname  || ''
  birthDt.value  = profile.birthDt  || '1990-07-17T12:25'
  gender.value   = (profile.gender === 'male' || profile.gender === 'female') ? profile.gender : 'female'
  cityName.value = profile.cityName || '南京'
  province.value = profile.province || '江苏省'
  lon.value      = profile.lon
  initCity.value = profile.cityName || '南京'
})
</script>

<template>
  <div class="home-page">
    <div class="form-center">
      <div class="quick-form">

        <!-- 行1：姓名 + 性别 -->
        <div class="qf-row qf-row-2">
          <label class="qf-group">
            <span class="qf-label">姓名</span>
            <input v-model="name" type="text" class="qf-input" placeholder="请输入姓名（选填）" />
          </label>
          <label class="qf-group qf-gender">
            <span class="qf-label">性别</span>
            <div class="gender-toggle">
              <button class="gender-btn" :class="{ active: gender === 'male' }"   @click.prevent="gender = 'male'">男</button>
              <button class="gender-btn" :class="{ active: gender === 'female' }" @click.prevent="gender = 'female'">女</button>
            </div>
          </label>
        </div>

        <!-- 行2：出生时间 + 出生城市 -->
        <div class="qf-row qf-row-2">
          <label class="qf-group">
            <span class="qf-label">出生时间</span>
            <input v-model="birthDt" type="datetime-local" class="qf-input" />
          </label>
          <label class="qf-group qf-city">
            <span class="qf-label">出生城市</span>
            <CityPicker v-model="lon" :initial-city="initCity" @city-change="onCityChange" />
          </label>
        </div>

        <!-- 服务 Tabs -->
        <div class="service-tabs">
          <button
            v-for="s in services"
            :key="s.key"
            class="svc-tab"
            :class="{ active: activeService === s.key }"
            @click="activeService = s.key"
          >
            <span class="svc-tab-icon">{{ s.tabChar }}</span>
            <span>{{ s.label }}</span>
          </button>
        </div>

        <button class="btn-start" @click="startAnalysis">
          开始分析 <span class="btn-arrow">→</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style src="./HomeView.css" scoped />
