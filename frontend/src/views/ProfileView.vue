<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useProfileStore } from '@/stores/profile'
import CityPicker from '@/components/CityPicker.vue'

const profile = useProfileStore()

// 本地表单状态（编辑时不直接修改 store，点保存才写入）
const birthDt   = ref(profile.birthDt)
const lon       = ref<number | undefined>(profile.lon)
const tz        = ref(profile.tz)
const gender    = ref<'male' | 'female' | ''>(profile.gender)
const mode      = ref<'dual' | 'single'>(profile.mode)
const solarTime = ref(profile.solarTime)
const surname   = ref(profile.surname)
const savedCity  = ref(profile.cityName)   // 传给 CityPicker 的初始城市

// 城市选择回调（接收 city-change 事件，更新 lon + 城市名）
const cityName = ref(profile.cityName)
const province = ref(profile.province)

function onCityChange(e: { cityName: string; province: string; lon: number }) {
  lon.value      = e.lon
  cityName.value = e.cityName
  province.value = e.province
}

const saved    = ref(false)
const saveErr  = ref('')

function doSave() {
  if (!birthDt.value) {
    saveErr.value = '请填写出生时间'
    return
  }
  if (lon.value === undefined) {
    saveErr.value = '请选择出生城市（用于经度计算）'
    return
  }
  saveErr.value = ''
  profile.setProfile({
    birthDt:   birthDt.value,
    lon:       lon.value,
    cityName:  cityName.value,
    province:  province.value,
    tz:        tz.value,
    gender:    gender.value,
    mode:      mode.value,
    solarTime: solarTime.value,
    surname:   surname.value,
  })
  saved.value = true
  setTimeout(() => { saved.value = false }, 2500)
}

function doReset() {
  birthDt.value   = '1990-01-15T08:30'
  lon.value       = 116.41
  cityName.value  = '北京'
  province.value  = '北京市'
  savedCity.value = '北京'
  tz.value        = 'Asia/Shanghai'
  gender.value    = 'male'
  mode.value      = 'dual'
  solarTime.value = false
  surname.value   = ''
}

onMounted(() => {
  // 确保表单与 store 同步（store 可能已从 localStorage 恢复）
  birthDt.value   = profile.birthDt
  lon.value       = profile.lon
  cityName.value  = profile.cityName
  province.value  = profile.province
  savedCity.value = profile.cityName
  tz.value        = profile.tz
  gender.value    = profile.gender
  mode.value      = profile.mode
  solarTime.value = profile.solarTime
  surname.value   = profile.surname
})
</script>

<template>
  <div class="wrap profile-view">
    <h1 class="page-title">个人信息</h1>
    <p class="page-desc">
      填写一次，八字、紫微、姓名等所有模块自动预填，无需重复输入。
    </p>

    <section class="card form-card">
      <div class="form-grid">
        <!-- 出生时间 -->
        <div class="form-row">
          <label>出生时间</label>
          <input type="datetime-local" v-model="birthDt" />
        </div>

        <!-- 出生城市（使用 CityPicker） -->
        <div class="form-row">
          <CityPicker
            v-model="lon"
            :initial-city="savedCity"
            @city-change="onCityChange"
          />
        </div>

        <!-- 时区 -->
        <div class="form-row">
          <label>时区</label>
          <select v-model="tz">
            <option value="Asia/Shanghai">Asia/Shanghai（东八区）</option>
            <option value="Asia/Tokyo">Asia/Tokyo（东九区）</option>
            <option value="UTC">UTC</option>
          </select>
        </div>

        <!-- 性别 -->
        <div class="form-row">
          <label>性别</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="male" />男</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="female" />女</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="" />不指定</label>
        </div>

        <!-- 计算模式 -->
        <div class="form-row">
          <label>计算模式</label>
          <label class="radio-opt"><input type="radio" v-model="mode" value="dual" />双历（节气校正）</label>
          <label class="radio-opt"><input type="radio" v-model="mode" value="single" />单历</label>
        </div>

        <!-- 真太阳时 -->
        <div class="form-row">
          <label>真太阳时</label>
          <label class="check-opt">
            <input type="checkbox" v-model="solarTime" />
            启用真太阳时修正
          </label>
        </div>

        <!-- 姓氏 -->
        <div class="form-row">
          <label>姓氏（选填）</label>
          <input v-model="surname" placeholder="如：张" maxlength="3" style="width:120px" />
          <span class="hint">用于姓名学联动</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <button class="btn-primary" @click="doSave">
          {{ saved ? '✓ 已保存' : '保存个人信息' }}
        </button>
        <button class="btn-sec" @click="doReset">重置为默认</button>
        <span v-if="saveErr" class="error-msg">{{ saveErr }}</span>
      </div>
    </section>

    <!-- 使用说明 -->
    <section class="card tips-card">
      <h2 class="card-title">使用说明</h2>
      <ul class="tips-list">
        <li>保存后，<b>八字排盘</b>、<b>紫微斗数</b>、<b>姓名学</b>等模块将自动预填本信息</li>
        <li>各模块仍可临时修改表单，不会覆盖此处保存的数据</li>
        <li>如需分析其他人，请在对应模块单独修改，或返回此页更新信息</li>
        <li>数据保存在本地浏览器，不上传服务器</li>
      </ul>
    </section>
  </div>
</template>

<style src="./ProfileView.css" scoped />
