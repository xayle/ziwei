/**
 * profile.ts — 个人信息 Pinia Store
 * 存储一次性填写的个人基本信息，供八字/紫微/姓名等各模块自动预填
 * 数据持久化到 localStorage
 */
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export interface ProfileData {
  birthDt:   string                      // 'YYYY-MM-DDTHH:mm'
  lon:       number | undefined          // 经度（城市选择后自动填入）
  cityName:  string                      // 城市名，如 '北京'
  province:  string                      // 省份名，如 '北京市'
  tz:        string                      // 时区，如 'Asia/Shanghai'
  gender:    'male' | 'female' | ''      // 性别
  mode:      'dual' | 'single'           // 计算模式
  solarTime: boolean                     // 是否启用真太阳时
  surname:   string                      // 姓氏（选填）
}

const STORAGE_KEY = 'profile_v1'

const DEFAULT: ProfileData = {
  birthDt:   '1990-01-15T08:30',
  lon:       116.41,
  cityName:  '北京',
  province:  '北京市',
  tz:        'Asia/Shanghai',
  gender:    'male',
  mode:      'dual',
  solarTime: false,
  surname:   '',
}

export const useProfileStore = defineStore('profile', () => {
  const birthDt   = ref<string>(DEFAULT.birthDt)
  const lon       = ref<number | undefined>(DEFAULT.lon)
  const cityName  = ref<string>(DEFAULT.cityName)
  const province  = ref<string>(DEFAULT.province)
  const tz        = ref<string>(DEFAULT.tz)
  const gender    = ref<'male' | 'female' | ''>(DEFAULT.gender)
  const mode      = ref<'dual' | 'single'>(DEFAULT.mode)
  const solarTime = ref<boolean>(DEFAULT.solarTime)
  const surname   = ref<string>(DEFAULT.surname)

  /** 是否已填写基础信息（出生日期 + 城市） */
  const isFilled = computed(() => !!(birthDt.value && lon.value !== undefined))

  /** 用户是否主动保存过个人信息（区别于初始默认值） */
  const saved = ref(false)

  /** 从 localStorage 加载 */
  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return
      const data: Partial<ProfileData> = JSON.parse(raw)
      saved.value = true  // 有持久化数据，说明用户曾主动保存过
      if (data.birthDt  !== undefined) birthDt.value   = data.birthDt
      if (data.lon      !== undefined) lon.value       = data.lon
      if (data.cityName !== undefined) cityName.value  = data.cityName
      if (data.province !== undefined) province.value  = data.province
      if (data.tz       !== undefined) tz.value        = data.tz
      if (data.gender   !== undefined) gender.value    = data.gender
      if (data.mode     !== undefined) mode.value      = data.mode
      if (data.solarTime !== undefined) solarTime.value = data.solarTime
      if (data.surname  !== undefined) surname.value   = data.surname
    } catch {
      // ignore parse errors
    }
  }

  /** 保存到 localStorage */
  function save() {
    const data: ProfileData = {
      birthDt:   birthDt.value,
      lon:       lon.value,
      cityName:  cityName.value,
      province:  province.value,
      tz:        tz.value,
      gender:    gender.value,
      mode:      mode.value,
      solarTime: solarTime.value,
      surname:   surname.value,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }

  /** 批量更新并保存 */
  function setProfile(data: Partial<ProfileData>) {
    if (data.birthDt   !== undefined) birthDt.value   = data.birthDt
    if (data.lon       !== undefined) lon.value       = data.lon
    if (data.cityName  !== undefined) cityName.value  = data.cityName
    if (data.province  !== undefined) province.value  = data.province
    if (data.tz        !== undefined) tz.value        = data.tz
    if (data.gender    !== undefined) gender.value    = data.gender
    if (data.mode      !== undefined) mode.value      = data.mode
    if (data.solarTime !== undefined) solarTime.value = data.solarTime
    if (data.surname   !== undefined) surname.value   = data.surname
    saved.value = true  // 标记用户主动保存过
    save()
  }

  /** 将 birthDt 拆分为 { year, month, day, hour, minute } */
  function parseBirthDt() {
    if (!birthDt.value) return { year: 2002, month: 1, day: 1, hour: 12, minute: 0 }
    const [datePart, timePart] = birthDt.value.split('T')
    const [y, m, d] = (datePart || '').split('-').map(Number)
    const [h, min]  = (timePart  || '00:00').split(':').map(Number)
    return {
      year:   y   || 1990,
      month:  m   || 1,
      day:    d   || 1,
      hour:   h   || 0,
      minute: min || 0,
    }
  }

  // 初始化时立即从 localStorage 加载
  load()

  return {
    birthDt, lon, cityName, province, tz, gender, mode, solarTime, surname,
    isFilled, saved,
    load, save, setProfile, parseBirthDt,
  }
})
