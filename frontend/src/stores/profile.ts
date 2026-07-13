/**
 * profile.ts — 个人信息 Pinia Store
 * 存储一次性填写的个人基本信息，供八字/紫微/姓名等各模块自动预填
 * 数据持久化到 localStorage
 */
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { createCase, listCases, patchCase, type CaseOut } from '@/api/cases'
import { listSnapshots, type SnapshotOut } from '@/api/snapshots'
import { useAuthStore } from '@/stores/auth'
import {
  caseOutToProfileData,
  caseOutToProfileLabel,
  profileToCasePatch,
  profileToCasePayload,
} from '@/utils/profileCaseSync'
import { isArchiveReady } from '@/utils/profileReadiness'

export interface ProfileData {
  birthDt:   string                      // 引擎用公历 'YYYY-MM-DDTHH:mm'
  /** 农历模式下用户录入的农历时刻（展示/再编辑用） */
  lunarBirthDt?: string
  lon:       number | undefined          // 经度（城市选择后自动填入）
  cityName:  string                      // 城市名，如 '北京'
  province:  string                      // 省份名，如 '北京市'
  tz:        string                      // 时区，如 'Asia/Shanghai'
  gender:    'male' | 'female' | ''      // 性别
  mode:      'dual' | 'single'           // 计算模式
  solarTime: boolean                     // 是否启用真太阳时
  surname:   string                      // 姓氏（选填）
  givenName: string                      // 名字（选填，姓名分析需与姓氏同填）
  calendarMode: 'gregorian' | 'lunar'
  isLeapMonth: boolean
  /** 紫微年界：lichun=立春换年 | normal=正月初一（对齐 iztro） */
  yearDivide: 'lichun' | 'normal'
  /** 紫微换日：solar_next=公历次日 | forward=子时换日(iztro) | current=当日子时 */
  dayDivide: 'solar_next' | 'forward' | 'current'
  /** 晚子时(23:00~00:00)是否视为次日 */
  lateZishi: boolean
  /** 八字子时换日：sxtwl=库默认 | early_zi_prev_day | early_zi_same_day */
  ziDayRule: 'sxtwl' | 'early_zi_prev_day' | 'early_zi_same_day'
  /** 紫微庙旺亮度算法 */
  ziweiBrightnessMethod: 'standard' | 'zhongzhou' | 'mod1' | 'mod2'
  /** 紫微右弼安星口径 */
  ziweiYoubiMethod: 'month' | 'hour'
  /** 生年四化表口径 */
  sihuaMethod: 'quanshu' | 'zhongzhou'
  /** 流年四化来源 */
  liunianSihuaMethod: 'year_stem' | 'life_palace_stem'
  /** 天魁天钺安法 */
  kuiyueMethod: 'standard' | 'gengxin_mahu' | 'gengxin_huima' | 'liuxin_mahu'
  /** 天马安法 */
  tianmaMethod: 'year' | 'month'
  /** 紫微响应模板 */
  templateVersion: 'standard' | 'pro' | 'simple'
  birthTimePrecision: 'exact' | 'hour' | 'approximate' | 'unknown'
  unknownTimeFallback: 'midday' | 'noon' | 'start_of_hour'
  currentCityName: string
  currentProvince: string
  currentLon: number | undefined
  currentTz: string
  focusTopic: string
  /** 城市层级（财富估算 M3.03） */
  cityTier: '一线' | '新一线' | '其余' | ''
  /** 行业（财富估算 M3.03） */
  industry: '金融IT' | '教育公务' | '其余' | ''
}

export interface ProfileRecord {
  id: string
  label: string
  createdAt: string
  updatedAt: string
  data: ProfileData
  /** 已同步到 /api/v1/cases 的远端 ID（需登录） */
  remoteCaseId?: string | null
}

const STORAGE_KEY = 'profile_v1'
const PROFILES_KEY = 'profile_records_v1'
const ACTIVE_PROFILE_KEY = 'profile_active_id_v1'

const DEFAULT: ProfileData = {
  birthDt: '',
  lunarBirthDt: '',
  lon: undefined,
  cityName: '',
  province: '',
  tz: 'Asia/Shanghai',
  gender: '',
  mode: 'dual',
  solarTime: false,
  surname: '',
  givenName: '',
  calendarMode: 'gregorian',
  isLeapMonth: false,
  yearDivide: 'lichun',
  dayDivide: 'solar_next',
  lateZishi: true,
  ziDayRule: 'sxtwl',
  ziweiBrightnessMethod: 'standard',
  ziweiYoubiMethod: 'month',
  sihuaMethod: 'quanshu',
  liunianSihuaMethod: 'year_stem',
  kuiyueMethod: 'standard',
  tianmaMethod: 'year',
  templateVersion: 'standard',
  birthTimePrecision: 'exact',
  unknownTimeFallback: 'midday',
  currentCityName: '',
  currentProvince: '',
  currentLon: undefined,
  currentTz: 'Asia/Shanghai',
  focusTopic: '',
  cityTier: '',
  industry: '',
}

function createEmptyProfileData(): ProfileData {
  return {
    birthDt: '',
    lunarBirthDt: '',
    lon: undefined,
    cityName: '',
    province: '',
    tz: 'Asia/Shanghai',
    gender: '',
    mode: 'dual',
    solarTime: false,
    surname: '',
    givenName: '',
    calendarMode: 'gregorian',
    isLeapMonth: false,
    yearDivide: 'lichun',
    dayDivide: 'solar_next',
    lateZishi: true,
  ziDayRule: 'sxtwl',
  ziweiBrightnessMethod: 'standard',
  ziweiYoubiMethod: 'month',
  sihuaMethod: 'quanshu',
  liunianSihuaMethod: 'year_stem',
  kuiyueMethod: 'standard',
  tianmaMethod: 'year',
  templateVersion: 'standard',
    birthTimePrecision: 'exact',
    unknownTimeFallback: 'midday',
    currentCityName: '',
    currentProvince: '',
    currentLon: undefined,
    currentTz: 'Asia/Shanghai',
    focusTopic: '',
    cityTier: '',
    industry: '',
  }
}

function createDefaultProfileRecord(): ProfileRecord {
  const now = new Date().toISOString()
  return {
    id: 'default',
    label: '新档案',
    createdAt: now,
    updatedAt: now,
    data: createEmptyProfileData(),
  }
}

function createProfileLabel(data: ProfileData): string {
  const fullName = [data.surname?.trim(), data.givenName?.trim()].filter(Boolean).join('')
  const base = fullName || data.cityName?.trim() || '个人档案'
  if (!data.birthDt) return base
  const date = data.birthDt.split('T')[0]?.replaceAll('-', '/')
  return date ? `${base} · ${date}` : base
}

function cloneProfileData(data: ProfileData): ProfileData {
  return { ...data }
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
  const givenName = ref<string>(DEFAULT.givenName)
  const calendarMode = ref<'gregorian' | 'lunar'>(DEFAULT.calendarMode)
  const isLeapMonth = ref<boolean>(DEFAULT.isLeapMonth)
  const yearDivide = ref<'lichun' | 'normal'>(DEFAULT.yearDivide)
  const dayDivide = ref<'solar_next' | 'forward' | 'current'>(DEFAULT.dayDivide)
  const lateZishi = ref<boolean>(DEFAULT.lateZishi)
  const ziDayRule = ref<ProfileData['ziDayRule']>(DEFAULT.ziDayRule)
  const ziweiBrightnessMethod = ref<ProfileData['ziweiBrightnessMethod']>(DEFAULT.ziweiBrightnessMethod)
  const ziweiYoubiMethod = ref<ProfileData['ziweiYoubiMethod']>(DEFAULT.ziweiYoubiMethod)
  const sihuaMethod = ref<ProfileData['sihuaMethod']>(DEFAULT.sihuaMethod)
  const liunianSihuaMethod = ref<ProfileData['liunianSihuaMethod']>(DEFAULT.liunianSihuaMethod)
  const kuiyueMethod = ref<ProfileData['kuiyueMethod']>(DEFAULT.kuiyueMethod)
  const tianmaMethod = ref<ProfileData['tianmaMethod']>(DEFAULT.tianmaMethod)
  const templateVersion = ref<ProfileData['templateVersion']>(DEFAULT.templateVersion)
  const birthTimePrecision = ref<'exact' | 'hour' | 'approximate' | 'unknown'>(DEFAULT.birthTimePrecision)
  const unknownTimeFallback = ref<'midday' | 'noon' | 'start_of_hour'>(DEFAULT.unknownTimeFallback)
  const currentCityName = ref<string>(DEFAULT.currentCityName)
  const currentProvince = ref<string>(DEFAULT.currentProvince)
  const currentLon = ref<number | undefined>(DEFAULT.currentLon)
  const currentTz = ref<string>(DEFAULT.currentTz)
  const focusTopic = ref<string>(DEFAULT.focusTopic)
  const lunarBirthDt = ref<string>(DEFAULT.lunarBirthDt ?? '')
  const cityTier = ref<ProfileData['cityTier']>(DEFAULT.cityTier)
  const industry = ref<ProfileData['industry']>(DEFAULT.industry)
  const profiles = ref<ProfileRecord[]>([createDefaultProfileRecord()])
  const activeProfileId = ref<string>('default')
  const remoteCases = ref<CaseOut[]>([])
  const loadingRemoteCases = ref(false)
  const remoteCasesError = ref('')
  const remoteSnapshots = ref<SnapshotOut[]>([])
  const loadingRemoteSnapshots = ref(false)
  const remoteSnapshotsError = ref('')

  /** 是否已填写基础信息（出生日期 + 城市 + 性别 + 经度） */
  const isFilled = computed(() => isArchiveReady(readCurrentProfileData()))

  function asProfileData(): ProfileData {
    return readCurrentProfileData()
  }

  /** 用户是否主动保存过个人信息（区别于初始默认值） */
  const saved = ref(false)

  const activeProfile = computed(() => profiles.value.find((item) => item.id === activeProfileId.value) || profiles.value[0] || null)
  const profileCount = computed(() => profiles.value.length)

  function readCurrentProfileData(): ProfileData {
    return {
      birthDt: birthDt.value,
      lunarBirthDt: lunarBirthDt.value,
      lon: lon.value,
      cityName: cityName.value,
      province: province.value,
      tz: tz.value,
      gender: gender.value,
      mode: mode.value,
      solarTime: solarTime.value,
      surname: surname.value,
      givenName: givenName.value,
      calendarMode: calendarMode.value,
      isLeapMonth: isLeapMonth.value,
      yearDivide: yearDivide.value,
      dayDivide: dayDivide.value,
      lateZishi: lateZishi.value,
      ziDayRule: ziDayRule.value,
      ziweiBrightnessMethod: ziweiBrightnessMethod.value,
      ziweiYoubiMethod: ziweiYoubiMethod.value,
      sihuaMethod: sihuaMethod.value,
      liunianSihuaMethod: liunianSihuaMethod.value,
      kuiyueMethod: kuiyueMethod.value,
      tianmaMethod: tianmaMethod.value,
      templateVersion: templateVersion.value,
      birthTimePrecision: birthTimePrecision.value,
      unknownTimeFallback: unknownTimeFallback.value,
      currentCityName: currentCityName.value,
      currentProvince: currentProvince.value,
      currentLon: currentLon.value,
      currentTz: currentTz.value,
      focusTopic: focusTopic.value,
      cityTier: cityTier.value,
      industry: industry.value,
    }
  }

  function applyProfileData(data: ProfileData) {
    birthDt.value = data.birthDt
    lunarBirthDt.value = data.lunarBirthDt ?? ''
    lon.value = data.lon
    cityName.value = data.cityName
    province.value = data.province
    tz.value = data.tz
    gender.value = data.gender
    mode.value = data.mode
    solarTime.value = data.solarTime
    surname.value = data.surname
    givenName.value = data.givenName ?? ''
    calendarMode.value = data.calendarMode
    isLeapMonth.value = data.isLeapMonth
    yearDivide.value = data.yearDivide ?? 'lichun'
    dayDivide.value = data.dayDivide ?? 'solar_next'
    lateZishi.value = data.lateZishi ?? true
    ziDayRule.value = data.ziDayRule ?? 'sxtwl'
    ziweiBrightnessMethod.value = data.ziweiBrightnessMethod ?? 'standard'
    ziweiYoubiMethod.value = data.ziweiYoubiMethod ?? 'month'
    sihuaMethod.value = data.sihuaMethod ?? 'quanshu'
    liunianSihuaMethod.value = data.liunianSihuaMethod ?? 'year_stem'
    kuiyueMethod.value = data.kuiyueMethod ?? 'standard'
    tianmaMethod.value = data.tianmaMethod ?? 'year'
    templateVersion.value = data.templateVersion ?? 'standard'
    birthTimePrecision.value = data.birthTimePrecision
    unknownTimeFallback.value = data.unknownTimeFallback
    currentCityName.value = data.currentCityName
    currentProvince.value = data.currentProvince
    currentLon.value = data.currentLon
    currentTz.value = data.currentTz
    focusTopic.value = data.focusTopic
    cityTier.value = data.cityTier ?? ''
    industry.value = data.industry ?? ''
  }

  function persistProfiles() {
    localStorage.setItem(PROFILES_KEY, JSON.stringify(profiles.value))
    localStorage.setItem(ACTIVE_PROFILE_KEY, activeProfileId.value)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(readCurrentProfileData()))
  }

  function upsertActiveProfile(data: ProfileData) {
    const now = new Date().toISOString()
    const nextLabel = createProfileLabel(data)
    const current = profiles.value.find((item) => item.id === activeProfileId.value)
    if (current) {
      current.label = nextLabel
      current.updatedAt = now
      current.data = cloneProfileData(data)
      return
    }
    const next: ProfileRecord = {
      id: activeProfileId.value,
      label: nextLabel,
      createdAt: now,
      updatedAt: now,
      data: cloneProfileData(data),
      remoteCaseId: null,
    }
    profiles.value = [next, ...profiles.value.filter((item) => item.id !== next.id)]
  }

  async function pullRemoteCases(): Promise<{ ok: boolean; error?: string }> {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) {
      remoteCases.value = []
      remoteCasesError.value = '未登录，无法拉取云端档案。'
      return { ok: false, error: remoteCasesError.value }
    }

    loadingRemoteCases.value = true
    remoteCasesError.value = ''
    try {
      const res = await listCases(50)
      remoteCases.value = res.items
      return { ok: true }
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      remoteCasesError.value = typeof detail === 'string' ? detail : '云端档案列表拉取失败。'
      return { ok: false, error: remoteCasesError.value }
    } finally {
      loadingRemoteCases.value = false
    }
  }

  function importRemoteCase(caseOut: CaseOut): string {
    const linked = profiles.value.find((item) => item.remoteCaseId === caseOut.id)
    if (linked) {
      switchProfile(linked.id)
      return linked.id
    }

    const nextId = crypto.randomUUID()
    const now = new Date().toISOString()
    const data = caseOutToProfileData(caseOut)
    const label = caseOutToProfileLabel(caseOut)
    const next: ProfileRecord = {
      id: nextId,
      label,
      createdAt: now,
      updatedAt: now,
      data,
      remoteCaseId: caseOut.id,
    }
    profiles.value = [next, ...profiles.value]
    activeProfileId.value = nextId
    applyProfileData(data)
    saved.value = true
    persistProfiles()
    return nextId
  }

  async function pullRemoteSnapshots(): Promise<{ ok: boolean; error?: string; skipped?: boolean }> {
    const auth = useAuthStore()
    const caseId = activeProfile.value?.remoteCaseId
    if (!auth.isLoggedIn || !caseId) {
      remoteSnapshots.value = []
      return { ok: false, skipped: true, error: '未登录或未同步云端案例。' }
    }

    loadingRemoteSnapshots.value = true
    remoteSnapshotsError.value = ''
    try {
      remoteSnapshots.value = await listSnapshots(caseId)
      return { ok: true }
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      remoteSnapshotsError.value = typeof detail === 'string' ? detail : '快照列表拉取失败。'
      return { ok: false, error: remoteSnapshotsError.value }
    } finally {
      loadingRemoteSnapshots.value = false
    }
  }

  async function syncRemoteCase(): Promise<{ ok: boolean; caseId?: string; error?: string; skipped?: boolean }> {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) {
      return { ok: false, skipped: true, error: '未登录，档案仅保存在本地。' }
    }
    if (!isArchiveReady(readCurrentProfileData())) {
      return { ok: false, skipped: true, error: '档案未就绪，跳过云端同步。' }
    }

    const data = readCurrentProfileData()
    const current = profiles.value.find((item) => item.id === activeProfileId.value)
    const label = current?.label || createProfileLabel(data)

    try {
      if (current?.remoteCaseId) {
        const updated = await patchCase(current.remoteCaseId, profileToCasePatch(data, label))
        current.remoteCaseId = updated.id
        persistProfiles()
        void pullRemoteSnapshots()
        return { ok: true, caseId: updated.id }
      }
      const created = await createCase(profileToCasePayload(data, label))
      if (current) {
        current.remoteCaseId = created.id
        persistProfiles()
      }
      void pullRemoteSnapshots()
      return { ok: true, caseId: created.id }
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      return {
        ok: false,
        error: typeof detail === 'string' ? detail : '云端档案同步失败。',
      }
    }
  }

  function syncActiveProfileData() {
    const data = readCurrentProfileData()
    upsertActiveProfile(data)
    saved.value = true
    persistProfiles()
  }

  /** 从 localStorage 加载 */
  function load() {
    try {
      const rawProfiles = localStorage.getItem(PROFILES_KEY)
      const rawActiveId = localStorage.getItem(ACTIVE_PROFILE_KEY)
      const legacyRaw = localStorage.getItem(STORAGE_KEY)

      let loadedProfiles: ProfileRecord[] = []
      if (rawProfiles) {
        const parsed = JSON.parse(rawProfiles) as ProfileRecord[]
        if (Array.isArray(parsed) && parsed.length > 0) {
          loadedProfiles = parsed
        }
      }

      if (loadedProfiles.length === 0 && legacyRaw) {
        const data = JSON.parse(legacyRaw) as Partial<ProfileData>
        const merged: ProfileData = { ...DEFAULT, ...data }
        loadedProfiles = [{
          ...createDefaultProfileRecord(),
          label: createProfileLabel(merged),
          data: merged,
        }]
      }

      if (loadedProfiles.length === 0) {
        profiles.value = [createDefaultProfileRecord()]
        activeProfileId.value = 'default'
        applyProfileData(DEFAULT)
        return
      }

      profiles.value = loadedProfiles.map((item) => ({
        ...item,
        data: { ...DEFAULT, ...item.data },
      }))
      activeProfileId.value = rawActiveId && profiles.value.some((item) => item.id === rawActiveId) ? rawActiveId : profiles.value[0].id
      const matched = profiles.value.find((item) => item.id === activeProfileId.value) || profiles.value[0]
      if (matched) {
        applyProfileData(matched.data)
      }
      saved.value = true
      persistProfiles()
    } catch {
      // ignore parse errors
    }
  }

  /** 保存到 localStorage */
  function save() {
    syncActiveProfileData()
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
    if (data.givenName !== undefined) givenName.value = data.givenName
    if (data.calendarMode !== undefined) calendarMode.value = data.calendarMode
    if (data.isLeapMonth !== undefined) isLeapMonth.value = data.isLeapMonth
    if (data.yearDivide !== undefined) yearDivide.value = data.yearDivide
    if (data.dayDivide !== undefined) dayDivide.value = data.dayDivide
    if (data.lateZishi !== undefined) lateZishi.value = data.lateZishi
    if (data.ziDayRule !== undefined) ziDayRule.value = data.ziDayRule
    if (data.ziweiBrightnessMethod !== undefined) ziweiBrightnessMethod.value = data.ziweiBrightnessMethod
    if (data.ziweiYoubiMethod !== undefined) ziweiYoubiMethod.value = data.ziweiYoubiMethod
    if (data.sihuaMethod !== undefined) sihuaMethod.value = data.sihuaMethod
    if (data.liunianSihuaMethod !== undefined) liunianSihuaMethod.value = data.liunianSihuaMethod
    if (data.kuiyueMethod !== undefined) kuiyueMethod.value = data.kuiyueMethod
    if (data.tianmaMethod !== undefined) tianmaMethod.value = data.tianmaMethod
    if (data.templateVersion !== undefined) templateVersion.value = data.templateVersion
    if (data.birthTimePrecision !== undefined) birthTimePrecision.value = data.birthTimePrecision
    if (data.unknownTimeFallback !== undefined) unknownTimeFallback.value = data.unknownTimeFallback
    if (data.currentCityName !== undefined) currentCityName.value = data.currentCityName
    if (data.currentProvince !== undefined) currentProvince.value = data.currentProvince
    if (data.currentLon !== undefined) currentLon.value = data.currentLon
    if (data.currentTz !== undefined) currentTz.value = data.currentTz
    if (data.focusTopic !== undefined) focusTopic.value = data.focusTopic
    if (data.lunarBirthDt !== undefined) lunarBirthDt.value = data.lunarBirthDt
    if (data.cityTier !== undefined) cityTier.value = data.cityTier
    if (data.industry !== undefined) industry.value = data.industry
    saved.value = true
    save()
    void import('./fushengReport').then(({ useFushengReportStore }) => {
      useFushengReportStore().invalidate()
    })
  }

  function saveCurrentAsNewProfile(label?: string) {
    const nextId = crypto.randomUUID()
    const now = new Date().toISOString()
    const data = readCurrentProfileData()
    const next: ProfileRecord = {
      id: nextId,
      label: label?.trim() || `${createProfileLabel(data)} 副本`,
      createdAt: now,
      updatedAt: now,
      data,
    }
    profiles.value = [next, ...profiles.value]
    activeProfileId.value = nextId
    saved.value = true
    persistProfiles()
  }

  function createNewBlankProfile(label = '新个人信息') {
    const nextId = crypto.randomUUID()
    const now = new Date().toISOString()
    const data = createEmptyProfileData()
    const next: ProfileRecord = {
      id: nextId,
      label,
      createdAt: now,
      updatedAt: now,
      data,
    }
    profiles.value = [next, ...profiles.value.filter((item) => item.id !== nextId)]
    activeProfileId.value = nextId
    applyProfileData(data)
    saved.value = false
    persistProfiles()
  }

  function duplicateProfile(profileId: string, label?: string) {
    const source = profiles.value.find((item) => item.id === profileId)
    if (!source) return
    const nextId = crypto.randomUUID()
    const now = new Date().toISOString()
    const next: ProfileRecord = {
      id: nextId,
      label: label?.trim() || `${source.label} 副本`,
      createdAt: now,
      updatedAt: now,
      data: cloneProfileData(source.data),
    }
    profiles.value = [next, ...profiles.value]
    activeProfileId.value = nextId
    applyProfileData(next.data)
    saved.value = true
    persistProfiles()
  }

  function switchProfile(profileId: string) {
    const target = profiles.value.find((item) => item.id === profileId)
    if (!target) return
    activeProfileId.value = profileId
    applyProfileData(target.data)
    saved.value = true
    persistProfiles()
    void import('./fushengReport').then(({ useFushengReportStore }) => {
      useFushengReportStore().invalidate()
    })
  }

  function removeProfile(profileId: string) {
    if (profiles.value.length <= 1) return
    const nextList = profiles.value.filter((item) => item.id !== profileId)
    profiles.value = nextList.length > 0 ? nextList : [createDefaultProfileRecord()]
    if (activeProfileId.value === profileId) {
      activeProfileId.value = profiles.value[0].id
      applyProfileData(profiles.value[0].data)
    }
    persistProfiles()
  }

  function refreshActiveProfileLabel() {
    const target = profiles.value.find((item) => item.id === activeProfileId.value)
    if (!target) return
    const data = readCurrentProfileData()
    target.label = createProfileLabel(data)
    target.updatedAt = new Date().toISOString()
    target.data = cloneProfileData(data)
    persistProfiles()
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
    birthDt, lon, cityName, province, tz, gender, mode, solarTime, surname, givenName,
    calendarMode, isLeapMonth, yearDivide, dayDivide, lateZishi, ziDayRule,
    ziweiBrightnessMethod, ziweiYoubiMethod, sihuaMethod, liunianSihuaMethod, kuiyueMethod, tianmaMethod, templateVersion,
    birthTimePrecision, unknownTimeFallback,
    currentCityName, currentProvince, currentLon, currentTz, focusTopic, lunarBirthDt, cityTier, industry,
    isFilled, saved,
    profiles, activeProfile, activeProfileId, profileCount,
    remoteCases, loadingRemoteCases, remoteCasesError,
    remoteSnapshots, loadingRemoteSnapshots, remoteSnapshotsError,
    load, save, setProfile, parseBirthDt, asProfileData,
    pullRemoteCases, pullRemoteSnapshots, importRemoteCase, syncRemoteCase,
    saveCurrentAsNewProfile, createNewBlankProfile, duplicateProfile, switchProfile, removeProfile, refreshActiveProfileLabel,
  }
})
