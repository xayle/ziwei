<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import ProfileTabNav, { type ProfileTabId } from '@/components/fusheng/ProfileTabNav.vue'
import AlgoPresetBar from '@/components/fusheng/AlgoPresetBar.vue'
import CityPicker from '@/components/CityPicker.vue'
import { useProfileStore } from '@/stores/profile'
import { useAuthStore } from '@/stores/auth'
import { normalizeBirthDateTime } from '@/utils/timeNormalization'
import { resolveLunarBirthDt } from '@/utils/resolveLunarBirthDt'
import { trackFlowEvent } from '@/utils/flowAnalytics'
import { getSnapshot } from '@/api/snapshots'
import { profileSummary, type ProfileSummaryResponse } from '@/api/relation'
import { parseFushengSnapshotOutput } from '@/utils/parseFushengSnapshot'
import { useFushengReportStore } from '@/stores/fushengReport'
import {
  getMissingProfileFields,
  getProfileCompleteness,
  getProfileFieldLabel,
  getTimeConfidence,
} from '@/utils/profileMetrics'
import { isArchiveReady, canAnalyzeName, isDemoSeedProfile } from '@/utils/profileReadiness'
import '@/assets/fusheng-page.css'

const router = useRouter()
const route = useRoute()
const profile = useProfileStore()
const auth = useAuthStore()
const saving = ref(false)
const lunarNote = ref('')
const syncNote = ref('')
const importingCaseId = ref<string | null>(null)
const restoringSnapshotId = ref<string | null>(null)
const snapshotRestoreNote = ref('')
const engineSummary = ref<ProfileSummaryResponse | null>(null)
const engineSummaryLoading = ref(false)
const editorTab = ref<ProfileTabId>('basic')
const coverCompact = ref(false)
const archiveSpreadBody = ref<HTMLElement | null>(null)

function updateCoverCompact() {
  const scrollTop = archiveSpreadBody.value?.scrollTop ?? 0
  coverCompact.value = scrollTop > 48
}

function scrollArchiveBodyToTop() {
  archiveSpreadBody.value?.scrollTo({ top: 0, behavior: 'smooth' })
  coverCompact.value = false
}

watch(editorTab, () => {
  scrollArchiveBodyToTop()
})

onMounted(() => {
  if (auth.isLoggedIn) {
    void profile.pullRemoteCases()
    if (profile.activeProfile?.remoteCaseId) {
      void profile.pullRemoteSnapshots()
      void loadEngineSummary()
    }
  }
  updateCoverCompact()
})

const profileTabs = [
  { id: 'basic' as const, label: '基础档案', testId: 'profile-tab-basic' },
  { id: 'bazi' as const, label: '八字口径', testId: 'profile-tab-bazi' },
  { id: 'ziwei' as const, label: '紫微口径', testId: 'profile-tab-ziwei' },
  { id: 'cloud' as const, label: '云端', testId: 'profile-tab-cloud' },
]

const ziweiAlgoPresets = [
  {
    id: 'iztro-youbi-hour',
    label: '对齐 iztro（hour 右弼）',
    hint: '辅煞与 iztro 生时安星对齐；不表示主星错误。',
  },
  {
    id: 'product-youbi-month',
    label: '产品默认（month 右弼）',
    hint: '恢复全书默认右弼口径。',
  },
]

const ziweiFieldTips: Record<string, string> = {
  calendarMode: '公历/农历录入方式；农历模式需配合闰月标记，影响紫微 leap_month_method。',
  isLeapMonth: '闰月标记：same=视为本月，mid=月中分界（默认）。',
  yearDivide: '立春换年与八字节气年一致；正月初一换年对齐 iztro（ZW03 边界用例）。',
  dayDivide: '换日口径影响晚子时排盘；forward 对齐 iztro dayDivide。',
  lateZishi: '23:00–00:00 是否视为次日（与 day_divide 联动）。',
  solarTime: '启用真太阳时后按出生地经度修正时刻，影响紫微安星。',
  ziweiBrightnessMethod: '星曜亮度表：standard（斗数全书）/ zhongzhou / mod1 / mod2。',
  ziweiYoubiMethod: '右弼默认 month（戌起正月逆数）；hour 可切至时辰口径对齐 iztro 辅煞（见 PRODUCT.md）。',
  sihuaMethod: '生年四化表：quanshu（全书默认）/ zhongzhou（中州变体）。',
  liunianSihuaMethod: '流年四化来源：year_stem（流年天干）/ life_palace_stem（流年命宫宫干）。',
  kuiyueMethod: '天魁天钺安法；standard 为六辛逢虎马默认。',
  tianmaMethod: '天马安法：year（年支）/ month（月支）。',
  templateVersion: '紫微 API 响应模板：standard / pro / simple。',
}

async function loadEngineSummary() {
  const caseId = profile.activeProfile?.remoteCaseId
  if (!auth.isLoggedIn || !caseId) {
    engineSummary.value = null
    return
  }
  engineSummaryLoading.value = true
  try {
    engineSummary.value = await profileSummary(caseId)
  } catch {
    engineSummary.value = null
  } finally {
    engineSummaryLoading.value = false
  }
}

watch(
  () => profile.activeProfile?.remoteCaseId,
  () => { void loadEngineSummary() },
)

function birthDtForDisplay(calendarMode: string, lunarBirthDt?: string, birthDt?: string) {
  if (calendarMode === 'lunar') return lunarBirthDt || birthDt || ''
  return birthDt || ''
}

function syncFormFromStore() {
  form.surname = profile.surname || ''
  form.givenName = profile.givenName || ''
  form.gender = profile.gender || ''
  form.calendarMode = profile.calendarMode || 'gregorian'
  form.birthDt = birthDtForDisplay(form.calendarMode, profile.lunarBirthDt, profile.birthDt)
  form.cityName = profile.cityName || ''
  form.province = profile.province || ''
  form.lon = profile.lon ?? undefined
  form.tz = profile.tz || 'Asia/Shanghai'
  form.solarTime = profile.solarTime ?? false
  form.isLeapMonth = profile.isLeapMonth ?? false
  form.yearDivide = profile.yearDivide ?? 'lichun'
  form.dayDivide = profile.dayDivide ?? 'solar_next'
  form.lateZishi = profile.lateZishi ?? true
  form.ziDayRule = profile.ziDayRule ?? 'sxtwl'
  form.ziweiBrightnessMethod = profile.ziweiBrightnessMethod ?? 'standard'
  form.ziweiYoubiMethod = profile.ziweiYoubiMethod ?? 'month'
  form.sihuaMethod = profile.sihuaMethod ?? 'quanshu'
  form.liunianSihuaMethod = profile.liunianSihuaMethod ?? 'year_stem'
  form.kuiyueMethod = profile.kuiyueMethod ?? 'standard'
  form.tianmaMethod = profile.tianmaMethod ?? 'year'
  form.templateVersion = profile.templateVersion ?? 'standard'
  form.birthTimePrecision = profile.birthTimePrecision || 'exact'
  form.unknownTimeFallback = profile.unknownTimeFallback || 'midday'
  form.focusTopic = profile.focusTopic || ''
  form.currentCityName = profile.currentCityName || ''
  form.currentProvince = profile.currentProvince || ''
  form.currentLon = profile.currentLon ?? undefined
  form.currentTz = profile.currentTz || 'Asia/Shanghai'
  form.cityTier = profile.cityTier || ''
  form.industry = profile.industry || ''
}

function persistFormToStore() {
  profile.setProfile(profileSnapshot.value)
}

function switchToProfile(profileId: string) {
  if (profileId === profile.activeProfileId) return
  persistFormToStore()
  profile.switchProfile(profileId)
  syncFormFromStore()
}

function createBlankProfile() {
  persistFormToStore()
  profile.createNewBlankProfile()
  syncFormFromStore()
  syncNote.value = '已新建空白档案'
}

function duplicateProfileById(profileId: string) {
  persistFormToStore()
  profile.duplicateProfile(profileId)
  syncFormFromStore()
  syncNote.value = '已创建档案副本'
}

function deleteProfile(profileId: string) {
  if (profile.profileCount <= 1) return
  profile.removeProfile(profileId)
  syncFormFromStore()
  syncNote.value = '已删除档案'
}

function importCloudCase(caseId: string) {
  const target = profile.remoteCases.find((item) => item.id === caseId)
  if (!target) return
  importingCaseId.value = caseId
  persistFormToStore()
  profile.importRemoteCase(target)
  syncFormFromStore()
  syncNote.value = `已导入云端档案 ${target.name}`
  importingCaseId.value = null
}

async function refreshCloudCases() {
  const res = await profile.pullRemoteCases()
  if (!res.ok && res.error) {
    syncNote.value = res.error
  }
}

async function refreshSnapshots() {
  const res = await profile.pullRemoteSnapshots()
  if (!res.ok && res.error && !res.skipped) {
    syncNote.value = res.error
  }
}

async function restoreSnapshot(snapId: string) {
  restoringSnapshotId.value = snapId
  snapshotRestoreNote.value = ''
  try {
    const snap = await getSnapshot(snapId)
    const output = parseFushengSnapshotOutput(snap)
    if (!output) {
      snapshotRestoreNote.value = '该快照无可用排盘数据。'
      return
    }
    const reportStore = useFushengReportStore()
    reportStore.restoreFromSnapshot(output)
    if (canAnalyzeName(profile.asProfileData())) {
      void reportStore.loadNameAnalysis()
    }
    trackFlowEvent('snapshot_restore', profile.activeProfileId)
    router.push('/report')
  } catch {
    snapshotRestoreNote.value = '恢复快照失败，请稍后重试。'
  } finally {
    restoringSnapshotId.value = null
  }
}

const form = reactive({
  surname: profile.surname || '',
  givenName: profile.givenName || '',
  gender: profile.gender || '',
  birthDt: birthDtForDisplay(profile.calendarMode || 'gregorian', profile.lunarBirthDt, profile.birthDt),
  cityName: profile.cityName || '',
  province: profile.province || '',
  lon: profile.lon ?? undefined,
  tz: profile.tz || 'Asia/Shanghai',
  solarTime: profile.solarTime ?? false,
  calendarMode: profile.calendarMode || 'gregorian',
  isLeapMonth: profile.isLeapMonth ?? false,
  yearDivide: (profile.yearDivide ?? 'lichun') as 'lichun' | 'normal',
  dayDivide: (profile.dayDivide ?? 'solar_next') as 'solar_next' | 'forward' | 'current',
  lateZishi: profile.lateZishi ?? true,
  ziDayRule: (profile.ziDayRule ?? 'sxtwl') as 'sxtwl' | 'early_zi_prev_day' | 'early_zi_same_day',
  ziweiBrightnessMethod: (profile.ziweiBrightnessMethod ?? 'standard') as 'standard' | 'zhongzhou' | 'mod1' | 'mod2',
  ziweiYoubiMethod: (profile.ziweiYoubiMethod ?? 'month') as 'month' | 'hour',
  sihuaMethod: (profile.sihuaMethod ?? 'quanshu') as 'quanshu' | 'zhongzhou',
  liunianSihuaMethod: (profile.liunianSihuaMethod ?? 'year_stem') as 'year_stem' | 'life_palace_stem',
  kuiyueMethod: (profile.kuiyueMethod ?? 'standard') as 'standard' | 'gengxin_mahu' | 'gengxin_huima' | 'liuxin_mahu',
  tianmaMethod: (profile.tianmaMethod ?? 'year') as 'year' | 'month',
  templateVersion: (profile.templateVersion ?? 'standard') as 'standard' | 'pro' | 'simple',
  birthTimePrecision: profile.birthTimePrecision || 'exact',
  unknownTimeFallback: profile.unknownTimeFallback || 'midday',
  focusTopic: profile.focusTopic || '',
  currentCityName: profile.currentCityName || '',
  currentProvince: profile.currentProvince || '',
  currentLon: profile.currentLon ?? undefined,
  currentTz: profile.currentTz || 'Asia/Shanghai',
  cityTier: (profile.cityTier || '') as '' | '一线' | '新一线' | '其余',
  industry: (profile.industry || '') as '' | '金融IT' | '教育公务' | '其余',
})

watch(() => profile.activeProfileId, () => {
  syncFormFromStore()
})

const profileSnapshot = computed(() => ({
  surname: form.surname,
  givenName: form.givenName,
  gender: form.gender as 'male' | 'female' | '',
  birthDt: form.birthDt,
  cityName: form.cityName,
  province: form.province,
  lon: form.lon,
  tz: form.tz,
  solarTime: form.solarTime,
  calendarMode: form.calendarMode as 'gregorian' | 'lunar',
  isLeapMonth: form.isLeapMonth,
  yearDivide: form.yearDivide,
  dayDivide: form.dayDivide,
  lateZishi: form.lateZishi,
  ziDayRule: form.ziDayRule,
  ziweiBrightnessMethod: form.ziweiBrightnessMethod,
  ziweiYoubiMethod: form.ziweiYoubiMethod,
  sihuaMethod: form.sihuaMethod,
  liunianSihuaMethod: form.liunianSihuaMethod,
  kuiyueMethod: form.kuiyueMethod,
  tianmaMethod: form.tianmaMethod,
  templateVersion: form.templateVersion,
  birthTimePrecision: form.birthTimePrecision as 'exact' | 'hour' | 'approximate' | 'unknown',
  unknownTimeFallback: form.unknownTimeFallback as 'midday' | 'noon' | 'start_of_hour',
  focusTopic: form.focusTopic,
  currentCityName: form.currentCityName,
  currentProvince: form.currentProvince,
  currentLon: form.currentLon,
  currentTz: form.currentTz,
  cityTier: form.cityTier as '' | '一线' | '新一线' | '其余',
  industry: form.industry as '' | '金融IT' | '教育公务' | '其余',
  mode: 'dual' as const,
}))

const completeness = computed(() => getProfileCompleteness(profileSnapshot.value))
const missingFields = computed(() => getMissingProfileFields(profileSnapshot.value))
const timeConfidence = computed(() => getTimeConfidence(profileSnapshot.value))

const engineSummaryItems = computed(() => {
  const s = engineSummary.value
  if (!s) return [] as Array<{ label: string; value: string }>
  const items: Array<{ label: string; value: string }> = []
  const pillars = s.pillars_primary
  if (pillars?.day) items.push({ label: '日柱', value: pillars.day })
  if (s.geju_one_liner) items.push({ label: '格局', value: s.geju_one_liner })
  if (s.strength_tier) items.push({ label: '强弱', value: s.strength_tier })
  if (s.ziwei_ming_one_liner) items.push({ label: '紫微命宫', value: s.ziwei_ming_one_liner })
  if (s.current_dayun) items.push({ label: '当前大运', value: s.current_dayun })
  if (s.liunian_2026_tag) items.push({ label: '2026', value: s.liunian_2026_tag })
  return items
})

const profileCoverName = computed(() => {
  const fullName = [form.surname, form.givenName].filter(Boolean).join('')
  if (fullName) return fullName
  const label = profile.activeProfile?.label?.trim()
  if (label) {
    return label.replace(/\s·\s\d{4}\/\d{2}\/\d{2}$/, '').trim() || label
  }
  return '未命名档案'
})

const profileCoverTitle = computed(() => {
  const name = profileCoverName.value
  const date = form.birthDt?.trim().slice(0, 10).replace(/-/g, '/')
  return date ? `${name} · ${date}` : name
})

const profileCoverMeta = computed(() => {
  const parts: string[] = []
  if (form.birthDt?.trim()) {
    parts.push(form.birthDt.replace('T', ' ').slice(0, 16))
  } else {
    parts.push('出生时间未填')
  }
  parts.push(form.cityName?.trim() || '出生地未填')
  parts.push(`完整 ${completeness.value}%`)
  parts.push(
    `时辰 ${'★'.repeat(timeConfidence.value.stars)}${'☆'.repeat(3 - timeConfidence.value.stars)}`,
  )
  if (missingFields.value.length) {
    parts.push(`待补 ${missingFields.value.length} 项`)
  } else {
    parts.push('已齐')
  }
  parts.push(profile.saved ? '已存' : '未存')
  const engineBits = engineSummaryItems.value.slice(0, 2).map((item) => `${item.label} ${item.value}`)
  if (engineBits.length) parts.push(engineBits.join(' · '))
  return parts.join(' · ')
})

const canOpenChart = computed(() => isArchiveReady(profileSnapshot.value))

const showDemoSeedWarn = computed(() => isDemoSeedProfile(profileSnapshot.value))

const zw03AlgoNote = computed(() => {
  if (form.yearDivide === 'lichun' && form.dayDivide === 'solar_next' && form.lateZishi) {
    return '当前为引擎 canonical（立春换年 + 公历晚子进次日），与 iztro 默认可能在 ZW03 边界命宫不一致。'
  }
  if (form.yearDivide === 'normal' && form.dayDivide === 'forward') {
    return '当前参数接近 iztro 对照轨（正月初一 + forward）；主产品口径仍建议用立春换年。'
  }
  return ''
})

const birthTimeMeta = computed(() => normalizeBirthDateTime({
  birthDt: form.birthDt || '1990-01-15T08:30',
  precision: form.birthTimePrecision,
  unknownTimeFallback: form.unknownTimeFallback,
}))

function onBirthCityChange(info: { cityName: string; province: string; lon: number }) {
  form.cityName = info.cityName
  form.province = info.province
  form.lon = info.lon
}

function onCurrentCityChange(info: { cityName: string; province: string; lon: number }) {
  form.currentCityName = info.cityName
  form.currentProvince = info.province
  form.currentLon = info.lon
}

function redirectTargetAfterArchive(): string | null {
  const raw = route.query.redirect
  if (typeof raw !== 'string' || !raw.startsWith('/')) return null
  return raw
}

function maybeRedirectAfterArchiveReady() {
  const target = redirectTargetAfterArchive()
  if (!target || !isArchiveReady(profileSnapshot.value)) return false
  router.replace(target)
  return true
}

async function saveProfile() {
  saving.value = true
  lunarNote.value = ''
  syncNote.value = ''
  try {
    let snapshot = profileSnapshot.value
    if (form.calendarMode === 'lunar') {
      const lunarInput = form.birthDt
      const resolved = await resolveLunarBirthDt({ ...snapshot, birthDt: lunarInput, lunarBirthDt: lunarInput })
      snapshot = { ...snapshot, birthDt: resolved.birthDt, lunarBirthDt: lunarInput }
      if (resolved.lunarLabel) {
        lunarNote.value = `${resolved.lunarLabel} → 公历 ${resolved.birthDt.replace('T', ' ')}`
      }
      if (resolved.warning) {
        lunarNote.value = [lunarNote.value, resolved.warning].filter(Boolean).join(' · ')
      }
    } else {
      snapshot = { ...snapshot, lunarBirthDt: '' }
    }
    profile.setProfile(snapshot)
    profile.refreshActiveProfileLabel()
    trackFlowEvent('profile_save', profile.activeProfileId)

    const sync = await profile.syncRemoteCase()
    if (sync.ok) {
      syncNote.value = `已同步云端案例 ${sync.caseId}`
      void profile.pullRemoteSnapshots()
    } else if (sync.skipped) {
      syncNote.value = sync.error || ''
    } else {
      syncNote.value = sync.error || '云端同步失败，本地档案已保存。'
    }
    maybeRedirectAfterArchiveReady()
  } finally {
    saving.value = false
  }
}

async function goReport() {
  await saveProfile()
  router.push('/report')
}

async function goBazi() {
  await saveProfile()
  router.push('/new/bazi')
}

function applyZiweiAlgoPreset(presetId: string) {
  if (presetId === 'iztro-youbi-hour') {
    form.ziweiYoubiMethod = 'hour'
  } else if (presetId === 'product-youbi-month') {
    form.ziweiYoubiMethod = 'month'
  } else {
    return
  }
  persistFormToStore()
  useFushengReportStore().invalidate()
  syncNote.value = presetId === 'iztro-youbi-hour'
    ? '已切换右弼为 hour，排盘缓存已失效。'
    : '已恢复右弼 month 默认口径，排盘缓存已失效。'
}
</script>

<template>
  <main class="archive-page">
    <p v-if="$route.query.reason === 'archive'" class="fs-advisory fs-advisory--cinnabar profile-alert">
      请先补全档案必填项：{{ missingFields.filter(f => ['birthDt','gender','cityName','lon'].includes(f)).map(getProfileFieldLabel).join('、') || '出生时间、性别、出生地、经度' }}。
      <button
        v-if="redirectTargetAfterArchive() && isArchiveReady(profileSnapshot)"
        type="button"
        class="profile-alert__action"
        @click="maybeRedirectAfterArchiveReady()"
      >
        档案已齐，继续前往
      </button>
    </p>
    <p v-if="profile.storageLoadError" class="fs-advisory fs-advisory--cinnabar profile-alert" data-testid="profile-storage-reset">
      {{ profile.storageLoadError }}
    </p>
    <p
      v-if="showDemoSeedWarn"
      class="fs-advisory fs-advisory--cinnabar profile-alert"
      data-testid="profile-demo-seed-warn"
    >
      当前仍接近出厂演示生辰（北京 · 1990-01-15）。可继续排盘，但正式成书请改为真实档案。
    </p>
    <p v-if="zw03AlgoNote" class="fs-hint profile-note" data-testid="profile-zw03-algo-note">{{ zw03AlgoNote }}</p>
    <p v-if="lunarNote" class="profile-note profile-note--lunar">{{ lunarNote }}</p>
    <p v-if="syncNote" class="profile-note">{{ syncNote }}</p>

    <section class="archive-spread" aria-label="档案册页">
      <div class="archive-spread__frame">
        <header class="archive-cover" :class="{ 'archive-cover--compact': coverCompact }">
          <div class="archive-cover__head">
            <p class="archive-cover__eyebrow">档案 · 命书封面</p>
            <h1 class="archive-cover__title">{{ profileCoverTitle }}</h1>
            <p class="archive-cover__meta" data-testid="profile-cover-meta">{{ profileCoverMeta }}</p>
          </div>
          <div class="archive-cover__actions">
            <button
              class="fs-btn fs-btn--primary"
              data-testid="profile-report"
              :disabled="!canOpenChart"
              @click="goReport"
            >
              生成报告
            </button>
            <button
              class="fs-btn fs-btn--ghost"
              data-testid="profile-save"
              :disabled="saving"
              @click="saveProfile"
            >
              {{ saving ? '保存中…' : '保存档案' }}
            </button>
          </div>
          <div class="archive-cover__links">
            <button
              type="button"
              class="archive-cover__link"
              data-testid="profile-bazi"
              :disabled="!canOpenChart"
              @click="goBazi"
            >
              查看八字
            </button>
            <button
              type="button"
              class="archive-cover__link"
              data-testid="profile-relation"
              :disabled="!isArchiveReady(profileSnapshot)"
              @click="router.push('/relation/new?type=couple')"
            >
              关系合盘
            </button>
          </div>
        </header>

        <div
          ref="archiveSpreadBody"
          class="archive-spread__body"
          @scroll.passive="updateCoverCompact"
        >
        <div class="archive-grid">
          <div class="archive-editor">
            <ProfileTabNav
              :tabs="profileTabs"
              :active="editorTab"
              @change="(id) => { editorTab = id }"
            />

            <div v-show="editorTab === 'basic'" class="archive-section">
              <h2 class="archive-section__title">基础信息</h2>
              <div class="archive-field-grid">
            <label class="archive-field"><span class="archive-field__label">姓氏</span><input v-model="form.surname" type="text" placeholder="可选" data-testid="profile-surname" /></label>
            <label class="archive-field"><span class="archive-field__label">名字</span><input v-model="form.givenName" type="text" placeholder="姓名分析需填写" data-testid="profile-given-name" /></label>
            <label class="archive-field">
              <span class="archive-field__label">性别</span>
              <select v-model="form.gender" data-testid="profile-gender">
                <option value="">不指定</option>
                <option value="male">男</option>
                <option value="female">女</option>
              </select>
            </label>
            <label class="archive-field archive-field--wide">
              <span class="archive-field__label">出生时间（{{ form.calendarMode === 'lunar' ? '农历年月日与时辰' : '公历' }}）</span>
              <input v-model="form.birthDt" type="datetime-local" data-testid="profile-birth-dt" />
            </label>
            <label class="archive-field">
              <span class="archive-field__label">时辰精度</span>
              <select v-model="form.birthTimePrecision">
                <option value="exact">精确到分</option>
                <option value="hour">只知时辰</option>
                <option value="approximate">大约</option>
                <option value="unknown">未知</option>
              </select>
            </label>
            <label v-if="form.birthTimePrecision === 'unknown'" class="archive-field">
              <span class="archive-field__label">未知时辰兜底</span>
              <select v-model="form.unknownTimeFallback">
                <option value="midday">日中 12:30</option>
                <option value="noon">正午 12:00</option>
                <option value="start_of_hour">当日零点 00:00</option>
              </select>
            </label>
            <label class="archive-field">
              <span class="archive-field__label">历法</span>
              <select v-model="form.calendarMode" data-testid="profile-calendar-mode">
                <option value="gregorian">公历</option>
                <option value="lunar">农历</option>
              </select>
            </label>
            <label class="archive-field">
              <span class="archive-field__label">闰月</span>
              <select v-model="form.isLeapMonth">
                <option :value="false">否</option>
                <option :value="true">是</option>
              </select>
            </label>
            <label class="archive-field archive-field--wide"><span class="archive-field__label">关注重点</span><input v-model="form.focusTopic" type="text" placeholder="事业 / 婚恋 / 健康…" /></label>
              </div>
            </div>

            <div v-show="editorTab === 'bazi'" class="archive-section" data-testid="profile-bazi-tab">
              <h2 class="archive-section__title">八字口径</h2>
              <p class="archive-field__hint archive-field--wide">影响四柱、子时换日与真太阳时；修改后排盘缓存会自动失效。</p>
              <div class="archive-field-grid">
                <label class="archive-field">
                  <span class="archive-field__label">子时换日（八字）</span>
                  <select v-model="form.ziDayRule" data-testid="profile-zi-day-rule">
                    <option value="sxtwl">库默认（sxtwl）</option>
                    <option value="early_zi_prev_day">早子算前一日</option>
                    <option value="early_zi_same_day">早子仍算当日</option>
                  </select>
                </label>
                <label class="archive-field">
                  <span class="archive-field__label">真太阳时</span>
                  <select v-model="form.solarTime" data-testid="profile-solar-time-bazi">
                    <option :value="false">关闭</option>
                    <option :value="true">开启</option>
                  </select>
                </label>
              </div>
            </div>

            <div v-show="editorTab === 'ziwei'" class="archive-section" data-testid="profile-ziwei-tab">
              <h2 class="archive-section__title">紫微口径</h2>
              <p class="archive-field__hint archive-field--wide">
                以下 8 项直接影响紫微排盘与 iztro 互证；修改后报告缓存会自动失效。
              </p>
              <div class="archive-field-grid">
            <label class="archive-field" :title="ziweiFieldTips.calendarMode">
              <span class="archive-field__label">历法 <abbr class="field-tip" :title="ziweiFieldTips.calendarMode">?</abbr></span>
              <select v-model="form.calendarMode" data-testid="profile-calendar-mode-ziwei">
                <option value="gregorian">公历</option>
                <option value="lunar">农历</option>
              </select>
            </label>
            <label class="archive-field" :title="ziweiFieldTips.isLeapMonth">
              <span class="archive-field__label">闰月 <abbr class="field-tip" :title="ziweiFieldTips.isLeapMonth">?</abbr></span>
              <select v-model="form.isLeapMonth">
                <option :value="false">否</option>
                <option :value="true">是</option>
              </select>
            </label>
            <label class="archive-field" :title="ziweiFieldTips.yearDivide">
              <span class="archive-field__label">年界（紫微） <abbr class="field-tip" :title="ziweiFieldTips.yearDivide">?</abbr></span>
              <select v-model="form.yearDivide" data-testid="profile-year-divide">
                <option value="lichun">立春换年</option>
                <option value="normal">正月初一换年</option>
              </select>
            </label>
            <label class="archive-field" :title="ziweiFieldTips.dayDivide">
              <span class="archive-field__label">换日（紫微） <abbr class="field-tip" :title="ziweiFieldTips.dayDivide">?</abbr></span>
              <select v-model="form.dayDivide" data-testid="profile-day-divide">
                <option value="solar_next">公历次日换日</option>
                <option value="forward">子时换日（iztro）</option>
                <option value="current">当日子时</option>
              </select>
            </label>
            <label class="archive-field" :title="ziweiFieldTips.lateZishi">
              <span class="archive-field__label">晚子时 <abbr class="field-tip" :title="ziweiFieldTips.lateZishi">?</abbr></span>
              <select v-model="form.lateZishi">
                <option :value="true">23:00–00:00 视为次日</option>
                <option :value="false">仍算当日</option>
              </select>
            </label>
            <label class="archive-field" :title="ziweiFieldTips.ziweiBrightnessMethod">
              <span class="archive-field__label">亮度口径 <abbr class="field-tip" :title="ziweiFieldTips.ziweiBrightnessMethod">?</abbr></span>
              <select v-model="form.ziweiBrightnessMethod" data-testid="profile-ziwei-brightness">
                <option value="standard">standard</option>
                <option value="zhongzhou">zhongzhou</option>
                <option value="mod1">mod1</option>
                <option value="mod2">mod2</option>
              </select>
            </label>
            <label class="archive-field" :title="ziweiFieldTips.ziweiYoubiMethod">
              <span class="archive-field__label">右弼口径 <abbr class="field-tip" :title="ziweiFieldTips.ziweiYoubiMethod">?</abbr></span>
              <select v-model="form.ziweiYoubiMethod" data-testid="profile-ziwei-youbi">
                <option value="month">month（默认）</option>
                <option value="hour">hour（对齐 iztro 可选）</option>
              </select>
            </label>
            <label class="archive-field" :title="ziweiFieldTips.sihuaMethod">
              <span class="archive-field__label">四化口径 <abbr class="field-tip" :title="ziweiFieldTips.sihuaMethod">?</abbr></span>
              <select v-model="form.sihuaMethod" data-testid="profile-sihua-method">
                <option value="quanshu">quanshu（全书）</option>
                <option value="zhongzhou">zhongzhou</option>
              </select>
            </label>
            <label class="archive-field" :title="ziweiFieldTips.liunianSihuaMethod">
              <span class="archive-field__label">流年四化 <abbr class="field-tip" :title="ziweiFieldTips.liunianSihuaMethod">?</abbr></span>
              <select v-model="form.liunianSihuaMethod" data-testid="profile-liunian-sihua-method">
                <option value="year_stem">year_stem</option>
                <option value="life_palace_stem">life_palace_stem</option>
              </select>
            </label>
            <label class="archive-field" :title="ziweiFieldTips.kuiyueMethod">
              <span class="archive-field__label">魁钺安法 <abbr class="field-tip" :title="ziweiFieldTips.kuiyueMethod">?</abbr></span>
              <select v-model="form.kuiyueMethod" data-testid="profile-kuiyue-method">
                <option value="standard">standard</option>
                <option value="gengxin_mahu">gengxin_mahu</option>
                <option value="gengxin_huima">gengxin_huima</option>
                <option value="liuxin_mahu">liuxin_mahu</option>
              </select>
            </label>
            <label class="archive-field" :title="ziweiFieldTips.tianmaMethod">
              <span class="archive-field__label">天马安法 <abbr class="field-tip" :title="ziweiFieldTips.tianmaMethod">?</abbr></span>
              <select v-model="form.tianmaMethod" data-testid="profile-tianma-method">
                <option value="year">year</option>
                <option value="month">month</option>
              </select>
            </label>
            <label class="archive-field" :title="ziweiFieldTips.templateVersion">
              <span class="archive-field__label">模板版本 <abbr class="field-tip" :title="ziweiFieldTips.templateVersion">?</abbr></span>
              <select v-model="form.templateVersion" data-testid="profile-template-version">
                <option value="standard">standard</option>
                <option value="pro">pro</option>
                <option value="simple">simple</option>
              </select>
            </label>
            <p class="archive-field__hint archive-field--wide">
              右弼 <code>month</code> 为产品默认；<code>hour</code> 仅在与 iztro 辅煞对齐时使用，不表示主星错误。
            </p>
            <AlgoPresetBar :presets="ziweiAlgoPresets" @apply="applyZiweiAlgoPreset" />
              </div>
            </div>

            <div
              v-show="editorTab === 'cloud'"
              class="archive-section"
              data-testid="profile-cloud-tab"
              :data-snapshots-ready="profile.remoteSnapshots.length > 0 && !profile.loadingRemoteSnapshots ? 'true' : undefined"
            >
              <div class="archive-aside__head">
                <h2 class="archive-section__title">云端档案</h2>
                <button
                  v-if="auth.isLoggedIn"
                  type="button"
                  class="archive-cover__link"
                  :disabled="profile.loadingRemoteCases"
                  @click="refreshCloudCases"
                >
                  {{ profile.loadingRemoteCases ? '拉取中…' : '刷新' }}
                </button>
              </div>
              <p v-if="!auth.isLoggedIn" class="archive-field__hint">
                <RouterLink to="/login">登录</RouterLink> 后可从云端拉取案例列表并导入。
              </p>
              <p v-else-if="profile.remoteCasesError" class="cloud-error">{{ profile.remoteCasesError }}</p>
              <p v-else-if="profile.loadingRemoteCases" class="archive-field__hint">正在拉取云端档案…</p>
              <p v-else-if="!profile.remoteCases.length" class="archive-field__hint">暂无云端案例，保存档案后将自动同步。</p>
              <ul v-else class="archive-register">
                <li v-for="item in profile.remoteCases" :key="item.id">
                  <div class="archive-register__row">
                    <div class="archive-register__label">
                      <strong>{{ item.name }}</strong>
                      <span>{{ item.birth_dt_local?.replace('T', ' ').slice(0, 16) || '—' }}</span>
                    </div>
                    <div class="archive-register__actions">
                      <button
                        type="button"
                        class="archive-register__mini"
                        :disabled="importingCaseId === item.id"
                        @click="importCloudCase(item.id)"
                      >
                        {{ importingCaseId === item.id ? '导入中…' : '导入' }}
                      </button>
                    </div>
                  </div>
                </li>
              </ul>

              <template v-if="auth.isLoggedIn && profile.activeProfile?.remoteCaseId">
                <div class="archive-aside__head" style="margin-top: var(--sp-5);">
                  <h2 class="archive-section__title">报告快照</h2>
                  <button
                    type="button"
                    class="archive-cover__link"
                    :disabled="profile.loadingRemoteSnapshots"
                    data-testid="profile-snapshots-refresh"
                    @click="refreshSnapshots"
                  >
                    {{ profile.loadingRemoteSnapshots ? '拉取中…' : '刷新' }}
                  </button>
                </div>
                <p v-if="profile.remoteSnapshotsError" class="cloud-error">{{ profile.remoteSnapshotsError }}</p>
                <p v-if="profile.loadingRemoteSnapshots && !profile.remoteSnapshots.length" class="archive-field__hint">正在拉取快照…</p>
                <p v-else-if="!profile.remoteSnapshots.length" class="archive-field__hint">生成报告后将自动存档快照。</p>
                <p v-if="snapshotRestoreNote" class="cloud-error">{{ snapshotRestoreNote }}</p>
                <ul v-if="profile.remoteSnapshots.length" class="archive-register">
                  <li v-for="snap in profile.remoteSnapshots.slice(0, 8)" :key="snap.id">
                    <div class="archive-register__row">
                      <div class="archive-register__label">
                        <strong>{{ snap.kind || 'snapshot' }}</strong>
                        <span>{{ snap.created_at.replace('T', ' ').slice(0, 16) }}</span>
                      </div>
                      <div class="archive-register__actions">
                        <button
                          type="button"
                          class="archive-register__mini"
                          :disabled="restoringSnapshotId === snap.id"
                          data-testid="profile-snapshot-restore"
                          @click="restoreSnapshot(snap.id)"
                        >
                          {{ restoringSnapshotId === snap.id ? '恢复中…' : '恢复' }}
                        </button>
                      </div>
                    </div>
                  </li>
                </ul>
              </template>
            </div>

            <div class="archive-section">
              <h2 class="archive-section__title">出生地与现居地</h2>
              <div class="archive-field-grid">
                <div class="archive-field archive-field--wide">
                  <span class="archive-field__label">出生地</span>
                  <div class="archive-field__boxed city-picker-row">
                    <CityPicker
                      v-model="form.lon"
                      :initial-city="form.cityName"
                      data-testid="profile-birth-city"
                      @city-change="onBirthCityChange"
                    />
                  </div>
                </div>
                <label class="archive-field"><span class="archive-field__label">时区</span><input v-model="form.tz" type="text" /></label>
                <label class="archive-field">
                  <span class="archive-field__label">城市层级</span>
                  <select v-model="form.cityTier" data-testid="profile-city-tier">
                    <option value="">未指定（默认其余）</option>
                    <option value="一线">一线</option>
                    <option value="新一线">新一线</option>
                    <option value="其余">其余</option>
                  </select>
                </label>
                <label class="archive-field">
                  <span class="archive-field__label">行业</span>
                  <select v-model="form.industry" data-testid="profile-industry">
                    <option value="">未指定（默认其余）</option>
                    <option value="金融IT">金融 IT</option>
                    <option value="教育公务">教育公务</option>
                    <option value="其余">其余</option>
                  </select>
                </label>
                <p class="archive-field__hint archive-field--wide">城市层级与行业用于八字财富/大运提示估算，选填。</p>
                <div class="archive-field archive-field--wide">
                  <span class="archive-field__label">现居地（选填）</span>
                  <div class="archive-field__boxed city-picker-row">
                    <CityPicker
                      v-model="form.currentLon"
                      optional
                      :initial-city="form.currentCityName"
                      @city-change="onCurrentCityChange"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <aside class="archive-aside">
            <div class="archive-aside__block">
              <div class="archive-aside__head">
                <h2 class="archive-aside__title">本地档案</h2>
                <button type="button" class="archive-cover__link" data-testid="profile-new" @click="createBlankProfile">
                  新建
                </button>
              </div>
              <ul class="archive-register">
                <li v-for="item in profile.profiles" :key="item.id">
                  <div
                    class="archive-register__row"
                    :class="{ 'is-active': item.id === profile.activeProfileId }"
                  >
                    <button type="button" class="archive-register__label" @click="switchToProfile(item.id)">
                      <strong>{{ item.label }}</strong>
                      <span>{{ item.updatedAt.slice(0, 10) }}</span>
                    </button>
                    <div class="archive-register__actions">
                      <button type="button" class="archive-register__mini" title="复制" @click="duplicateProfileById(item.id)">副本</button>
                      <button
                        v-if="profile.profileCount > 1"
                        type="button"
                        class="archive-register__mini"
                        title="删除"
                        @click="deleteProfile(item.id)"
                      >
                        删
                      </button>
                    </div>
                  </div>
                </li>
              </ul>
            </div>

            <div class="archive-aside__block">
              <h2 class="archive-aside__title">档案摘要</h2>
              <dl class="archive-meta-list meta-list--brief">
                <div><dt>姓名</dt><dd>{{ form.surname }}{{ form.givenName }}</dd></div>
                <div><dt>出生</dt><dd>{{ form.birthDt ? form.birthDt.replace('T', ' ').slice(0, 16) : '未填写' }}</dd></div>
                <div><dt>性别</dt><dd>{{ form.gender === 'male' ? '男' : form.gender === 'female' ? '女' : '未填' }}</dd></div>
                <div><dt>出生地</dt><dd>{{ form.cityName || '未填写' }}{{ form.lon !== undefined ? ` · ${form.lon.toFixed(2)}°E` : '' }}</dd></div>
                <div v-if="form.focusTopic"><dt>关注</dt><dd>{{ form.focusTopic }}</dd></div>
              </dl>
              <details class="archive-advanced profile-advanced-meta">
                <summary>高级口径（可选）</summary>
                <dl class="archive-meta-list">
                  <div><dt>保存状态</dt><dd>{{ profile.saved ? '已保存' : '未保存' }}</dd></div>
                  <div><dt>云端案例</dt><dd>{{ profile.activeProfile?.remoteCaseId || (auth.isLoggedIn ? '未同步' : '需登录') }}</dd></div>
                  <div v-if="form.calendarMode === 'lunar' && profile.birthDt"><dt>排盘公历</dt><dd>{{ profile.birthDt.replace('T', ' ').slice(0, 16) }}</dd></div>
                  <div v-if="form.cityTier"><dt>城市层级</dt><dd>{{ form.cityTier }}</dd></div>
                  <div v-if="form.industry"><dt>行业</dt><dd>{{ form.industry }}</dd></div>
                  <div><dt>夏令时</dt><dd>{{ birthTimeMeta.dstLabel }}</dd></div>
                  <div><dt>年界</dt><dd>{{ form.yearDivide === 'normal' ? '正月初一' : '立春' }}</dd></div>
                  <div><dt>换日</dt><dd>{{ form.dayDivide === 'forward' ? '子时换日' : form.dayDivide === 'current' ? '当日子时' : '公历次日' }}</dd></div>
                  <div><dt>子时规则</dt><dd>{{ form.ziDayRule === 'early_zi_prev_day' ? '早子算前一日' : form.ziDayRule === 'early_zi_same_day' ? '早子仍算当日' : '库默认' }}</dd></div>
                  <div><dt>亮度</dt><dd>{{ form.ziweiBrightnessMethod }}</dd></div>
                  <div><dt>右弼</dt><dd>{{ form.ziweiYoubiMethod === 'hour' ? 'hour（iztro）' : 'month（默认）' }}</dd></div>
                  <div><dt>四化</dt><dd>{{ form.sihuaMethod }}</dd></div>
                  <div><dt>流年四化</dt><dd>{{ form.liunianSihuaMethod }}</dd></div>
                  <div><dt>模板</dt><dd>{{ form.templateVersion }}</dd></div>
                </dl>
              </details>
            </div>

            <div v-if="missingFields.length" class="archive-aside__block">
              <div class="archive-footnote">
                <strong>待补全字段</strong>
                <ul>
                  <li v-for="field in missingFields" :key="field">{{ getProfileFieldLabel(field) }}</li>
                </ul>
              </div>
            </div>
          </aside>
        </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.profile-alert__action {
  margin-left: 8px;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--brand-cinnabar);
  background: var(--surface);
  color: var(--brand-cinnabar);
  font-size: 12px;
  cursor: pointer;
}

.profile-note {
  margin: 0;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--brand-gold-lt);
  border: 1px solid rgba(184, 137, 77, 0.25);
  color: var(--brand-gold-dark);
  font-size: 12px;
  line-height: 1.6;
}

.profile-note--lunar {
  background: var(--surface);
  border-color: var(--border-md);
  border-left: 3px solid var(--brand-gold);
  color: var(--brand-mist);
}

.field-tip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-left: 4px;
  border-radius: 50%;
  background: var(--border);
  color: var(--brand-mist);
  font-size: 11px;
  font-weight: 800;
  text-decoration: none;
  cursor: help;
}

.cloud-error {
  margin: 0;
  font-size: 12px;
  color: var(--brand-cinnabar);
}

.city-picker-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
</style>
