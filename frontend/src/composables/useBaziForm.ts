/**
 * useBaziForm.ts — 八字排盘表单状态管理
 *
 * 提供：
 *  - 表单字段 refs（出生时间、经度、时区、性别、模式、真太阳时、姓氏、城市）
 *  - syncFromProfile()  从个人信息 store 同步批量赋值
 *  - onCityChange()     CityPicker 城市变更处理
 *  - gotoZeri()         跳转择日页
 *  - gotoGlossary()     跳转词汇表页
 *  - profile            暴露 profileStore 实例供父层判断 saved 状态
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useNameStore } from '@/stores/name'
import { useProfileStore } from '@/stores/profile'

export function useBaziForm() {
  const router    = useRouter()
  const nameStore = useNameStore()
  const profile   = useProfileStore()

  // ── 表单字段 ──────────────────────────────────────────────────────────────
  const birthDt   = ref(profile.birthDt || '1990-01-15T08:30')
  const lon       = ref<number | undefined>(profile.lon)
  const tz        = ref(profile.tz || 'Asia/Shanghai')
  const gender    = ref<'male' | 'female' | ''>(profile.gender || 'male')
  const mode      = ref<'dual' | 'single'>(profile.mode || 'dual')
  const solarTime = ref(profile.solarTime)
  const surname   = ref(profile.surname || '')
  const initCity  = ref(profile.cityName || '北京')
  const cityName  = ref(profile.cityName || '北京')
  const province  = ref(profile.province || '北京市')
  const showForm  = ref(!profile.saved)

  // ── 操作 ─────────────────────────────────────────────────────────────────
  function syncFromProfile() {
    birthDt.value   = profile.birthDt   || '1990-01-15T08:30'
    lon.value       = profile.lon
    tz.value        = profile.tz        || 'Asia/Shanghai'
    gender.value    = profile.gender    || 'male'
    mode.value      = profile.mode      || 'dual'
    solarTime.value = profile.solarTime
    surname.value   = profile.surname   || ''
    initCity.value  = profile.cityName  || '北京'
    cityName.value  = profile.cityName  || '北京'
    province.value  = profile.province  || '北京市'
  }

  function onCityChange(e: { cityName: string; province: string; lon: number }) {
    lon.value       = e.lon
    cityName.value  = e.cityName
    province.value  = e.province
    initCity.value  = e.cityName
  }

  /** 根据用神推荐改名，跳转姓名页 */
  function gotoNameSuggest(favorList: string[]) {
    const WX_MAP: Record<string, string> = {
      '甲':'木','乙':'木','寅':'木','卯':'木',
      '丙':'火','丁':'火','巳':'火','午':'火',
      '戊':'土','己':'土','辰':'土','戌':'土','丑':'土','未':'土',
      '庚':'金','辛':'金','申':'金','酉':'金',
      '壬':'水','癸':'水','亥':'水','子':'水',
      '木':'木','火':'火','土':'土','金':'金','水':'水',
    }
    const elements = [...new Set(favorList.map(t => WX_MAP[t]).filter(Boolean))]
    nameStore.setPrefill(surname.value, elements)
    router.push('/name')
  }

  function gotoZeri() {
    router.push('/zeri')
  }

  function gotoGlossary() {
    router.push('/glossary')
  }

  return {
    // refs
    birthDt, lon, tz, gender, mode, solarTime, surname,
    initCity, cityName, province, showForm,
    // actions
    syncFromProfile,
    onCityChange,
    gotoNameSuggest,
    gotoZeri,
    gotoGlossary,
    // store（供父层检查 profile.saved）
    profile,
  }
}
