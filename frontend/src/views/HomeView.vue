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

<style scoped>
/* ════ 页面容器 ════ */
.home-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafaf9;
  overflow-y: auto;
}

.form-center {
  width: 100%;
  max-width: 640px;
  padding: 32px 20px;
}

/* ════ 快速表单卡 ════ */
.quick-form {
  background: #fff;
  border: 1px solid #e7e5e4;
  border-radius: 22px;
  padding: 28px;
  box-shadow: 0 8px 32px rgba(28,25,23,.08);
}

/* 两列行 */
.qf-row-2 {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 14px;
  margin-bottom: 14px;
  align-items: end;
}

.qf-group { display: flex; flex-direction: column; gap: 5px; }

.qf-label {
  font-size: 11px;
  font-weight: 600;
  color: #78716c;
  letter-spacing: .06em;
  text-transform: uppercase;
}

.qf-input {
  height: 42px;
  padding: 0 12px;
  border: 1px solid #d6d3d1;
  border-radius: 11px;
  font-size: 14px;
  color: #1c1917;
  background: #fafaf9;
  outline: none;
  transition: border-color .15s;
  width: 100%;
  box-sizing: border-box;
}
.qf-input:focus { border-color: #b45309; background: #fff; }
.qf-input::placeholder { color: #a8a29e; }

/* 性别 */
.qf-gender { width: fit-content; }
.gender-toggle {
  display: flex;
  height: 42px;
  border: 1px solid #d6d3d1;
  border-radius: 11px;
  overflow: hidden;
}
.gender-btn {
  width: 48px;
  border: none;
  background: #fafaf9;
  font-size: 14px;
  font-weight: 600;
  color: #57534e;
  cursor: pointer;
  transition: all .15s;
}
.gender-btn + .gender-btn { border-left: 1px solid #e7e5e4; }
.gender-btn.active { background: #1c1917; color: #fff; }

/* 城市 */
.qf-city { width: 220px; }
.qf-city :deep(select) {
  height: 42px;
  border-radius: 11px;
  font-size: 14px;
  border-color: #d6d3d1;
  background: #fafaf9;
  padding: 0 10px;
  width: 100%;
  box-sizing: border-box;
}

/* ════ 服务 Tabs ════ */
.service-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
}

.svc-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 9px 4px;
  border: 2px solid #e7e5e4;
  border-radius: 13px;
  background: #fafaf9;
  font-size: 12px;
  font-weight: 600;
  color: #57534e;
  cursor: pointer;
  transition: all .15s;
}
.svc-tab:hover { border-color: #a8a29e; }
.svc-tab.active { border-color: #1c1917; background: #1c1917; color: #fff; }

.svc-tab-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: 14px;
  font-weight: 700;
  background: rgba(0,0,0,.05);
}
.svc-tab.active .svc-tab-icon { background: rgba(255,255,255,.15); }

/* ════ 开始按钮 ════ */
.btn-start {
  width: 100%;
  height: 50px;
  border: none;
  border-radius: 99px;
  background: #b45309;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 6px 18px rgba(180,83,9,.22);
  transition: all .15s;
}
.btn-start:hover { background: #92400e; transform: translateY(-1px); }
.btn-arrow { font-size: 18px; }

/* ════ 响应式 ════ */
@media (max-width: 560px) {
  .qf-row-2 { grid-template-columns: 1fr; }
  .qf-city { width: 100%; }
  .form-center { padding: 16px 12px; }
  .quick-form { padding: 18px; }
}
</style>