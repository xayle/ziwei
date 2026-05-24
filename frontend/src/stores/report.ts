/**
 * report.ts — 报告书 Pinia Store
 * 管理案例数据、各章节计算结果、参数控制状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import {
  fetchCase, fetchCaseList,
  computeFullBazi, computeZiwei, computeName,
  fetchZeriRecommend, fetchFengshuiBagua,
  type CaseOut, type BaziFullResponse, type ZeriResponse, type FengshuiResponse,
} from '@/api/report'
import type { ZiweiResponse } from '@/api/ziwei'
import type { NameAnalysisResponse } from '@/api/name'
import { genderToZh } from '@/data/ganzhi'
import { CHAPTERS, firstSectionId } from '@/data/toc'
import { lookupGlossary } from '@/components/report/glossaryData'

// ── 参数类型 ─────────────────────────────────────────────────────

export interface ChapterParamsBazi {
  mode: 'dual' | 'single'
  solar_time_enabled: boolean
  liunian_range: [number, number]   // [起始年, 结束年]
}

export interface ChapterParamsZiwei {
  gender: 'M' | 'F'
  template_version: 'standard' | 'pro' | 'simple'
  liunian_year: number
  dayun_index: number | null
}

export interface ChapterParamsName {
  name_override: string | null
  birth_year_override: number | null
}

export interface ChapterParamsZeri {
  purpose: string
  month: string                     // 'YYYY-MM'
  house_direction: string | null
}

export interface ChapterParamsFengshui {
  birth_year_override: number | null
  gender_override: '男' | '女' | null
}

export interface ChapterParams {
  bazi: ChapterParamsBazi
  ziwei: ChapterParamsZiwei
  name: ChapterParamsName
  zeri: ChapterParamsZeri
  fengshui: ChapterParamsFengshui
}

// ── 词条类型 ─────────────────────────────────────────────────────

export interface GlossaryEntry {
  term: string
  pinyin?: string
  definition: string
  category?: string
  classic_source?: string
}

// ── Store ─────────────────────────────────────────────────────────

export const useReportStore = defineStore('report', () => {
  // ─── 案例 ─────────────────────────────────────────────────────
  const caseId    = ref<string | null>(null)
  const caseData  = ref<CaseOut | null>(null)
  const caseList  = ref<CaseOut[]>([])
  const caseListError = ref<string | null>(null)
  const caseLoading = ref(false)
  const caseError = ref<string | null>(null)

  // ─── 各章节计算结果 ────────────────────────────────────────────
  const baziData     = ref<BaziFullResponse | null>(null)
  const ziweiData    = ref<ZiweiResponse | null>(null)
  const nameData     = ref<NameAnalysisResponse | null>(null)
  const zeriData     = ref<ZeriResponse | null>(null)
  const fengshuiData = ref<FengshuiResponse | null>(null)

  // ─── 加载/错误状态 ─────────────────────────────────────────────
  const loadingMap = ref<Record<string, boolean>>({
    case: false, bazi: false, ziwei: false, name: false, zeri: false, fengshui: false,
  })
  const errorMap = ref<Record<string, string | null>>({
    case: null, bazi: null, ziwei: null, name: null, zeri: null, fengshui: null,
  })
  const cacheTimestamps = ref<Record<string, number>>({})
  const CACHE_TTL = 30 * 60 * 1000   // 30 分钟

  // ─── 导航状态 ──────────────────────────────────────────────────
  const activeChapter = ref(1)
  const activeSection = ref<string | null>('1-1')

  // ─── 参数控制 ──────────────────────────────────────────────────
  /** 每次需要完整重置时调用，返回全新初始默认参数对象 */
  function _defaultParams(): ChapterParams {
    const y = new Date().getFullYear()
    const m = String(new Date().getMonth() + 1).padStart(2, '0')
    return {
      bazi: { mode: 'dual', solar_time_enabled: false, liunian_range: [y - 5, y + 10] },
      ziwei: { gender: 'M', template_version: 'standard', liunian_year: y, dayun_index: null },
      name: { name_override: null, birth_year_override: null },
      zeri: { purpose: 'general', month: `${y}-${m}`, house_direction: null },
      fengshui: { birth_year_override: null, gender_override: null },
    }
  }

  const chapterParams = ref<ChapterParams>(_defaultParams())
  const pendingParams = ref<ChapterParams>(JSON.parse(JSON.stringify(chapterParams.value)))
  const dirtyParams = ref<Record<string, boolean>>({ bazi: false, ziwei: false, name: false, zeri: false, fengshui: false })

  // ─── 词条卡片（卡2）──────────────────────────────────────────
  const glossaryTerm      = ref<string | null>(null)
  const glossaryEntry     = ref<GlossaryEntry | null>(null)
  /** 卡2 宫格详情模式：当前激活的宫格 index（null = 词条模式） */
  const activePalaceIndex = ref<number | null>(null)

  // ─── 笔记（按 sectionId）────────────────────────────────────
  const notes = ref<Record<string, string>>({})

  // ─── 卡片折叠状态 ─────────────────────────────────────────────
  const cardCollapsed = ref<Record<string, boolean>>({
    overview: false, glossary: false, fortune: false, notes: true,
  })

  // ─── 内容区详情区展开状态 ─────────────────────────────────────
  const sectionDetailExpanded = ref<Record<string, boolean>>({})

  // ── computed ────────────────────────────────────────────────────

  const currentChapterDef = computed(() =>
    CHAPTERS.find(c => c.num === activeChapter.value) ?? CHAPTERS[0]
  )

  const isCacheValid = (key: string) => {
    const ts = cacheTimestamps.value[key]
    return ts != null && Date.now() - ts < CACHE_TTL
  }

  const cacheAge = (key: string): string => {
    const ts = cacheTimestamps.value[key]
    if (!ts) return ''
    const mins = Math.floor((Date.now() - ts) / 60000)
    return mins < 1 ? '刚刚' : `${mins}分钟前`
  }

  // ── 初始化默认参数（依赖 caseData）──────────────────────────────

  function _initDefaultParams() {
    if (!caseData.value) return
    // ① 先完整重置到初始默认值（防止切换案例时旧参数污染新案例）
    chapterParams.value = _defaultParams()
    // ② 应用案例特定值
    const birthYear = caseData.value.birth_dt_local
      ? Number(caseData.value.birth_dt_local.slice(0, 4))
      : undefined
    chapterParams.value.bazi.solar_time_enabled = caseData.value.solar_time_enabled
    chapterParams.value.ziwei.gender = caseData.value.gender === 'female' ? 'F' : 'M'
    if (birthYear) chapterParams.value.name.birth_year_override = birthYear
    // ③ 尝试从 sessionStorage 恢复用户上次保存的参数（仅恢复本案例的存档）
    if (caseId.value) {
      try {
        const saved = sessionStorage.getItem(`report:params:${caseId.value}`)
        if (saved) {
          const parsed = JSON.parse(saved)
          for (const key of Object.keys(parsed) as Array<keyof typeof chapterParams.value>) {
            if (chapterParams.value[key] !== undefined) {
              Object.assign(chapterParams.value[key] as object, parsed[key])
            }
          }
        }
      } catch { /* ignore */ }
    }
    // ④ 同步 pending
    pendingParams.value = JSON.parse(JSON.stringify(chapterParams.value))
    dirtyParams.value = { bazi: false, ziwei: false, name: false, zeri: false, fengshui: false }
  }

  // ── Actions ──────────────────────────────────────────────────────

  async function loadCaseList() {
    caseListError.value = null
    try {
      const res = await fetchCaseList({ limit: 50 })
      caseList.value = res.items
    } catch {
      caseList.value = []
      caseListError.value = '案例列表加载失败，请刷新重试'
    }
  }

  async function loadCase(id: string) {
    if (caseId.value === id && caseData.value && isCacheValid('case')) return
    const isNewCase = caseId.value !== id
    caseId.value = id
    caseLoading.value = true
    caseError.value = null
    // 切换案例时：清空章节数据、词条、宫格激活、笔记
    if (isNewCase) {
      baziData.value = null; ziweiData.value = null
      nameData.value = null; zeriData.value = null; fengshuiData.value = null
      cacheTimestamps.value = {}
      glossaryTerm.value = null; glossaryEntry.value = null
      activePalaceIndex.value = null
      notes.value = {}
      sectionDetailExpanded.value = {}
      activeChapter.value = 1
      activeSection.value = '1-1'
    }
    // 尝试 sessionStorage 恢复
    try {
      const cached = sessionStorage.getItem(`report:case:${id}`)
      if (cached) {
        const { data, ts } = JSON.parse(cached)
        if (Date.now() - ts < CACHE_TTL) {
          caseData.value = data
          cacheTimestamps.value['case'] = ts
          _initDefaultParams()
          caseLoading.value = false
          return
        }
      }
    } catch { /* ignore */ }
    try {
      caseData.value = await fetchCase(id)
      const ts = Date.now()
      cacheTimestamps.value['case'] = ts
      sessionStorage.setItem(`report:case:${id}`, JSON.stringify({ data: caseData.value, ts }))
      _initDefaultParams()
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? '加载案例失败'
      caseError.value = msg
    } finally {
      caseLoading.value = false
    }
  }

  async function loadChapterData(chapterNum: number, force = false) {
    if (!caseData.value) return
    const chapter = CHAPTERS.find(c => c.num === chapterNum)
    if (!chapter?.hasApi || !chapter.apiKey) return
    const key = chapter.apiKey

    if (!force && isCacheValid(key)) return
    if (loadingMap.value[key]) return   // 防止并发重复请求

    loadingMap.value[key] = true
    errorMap.value[key] = null

    const c = caseData.value
    const p = chapterParams.value

    try {
      if (key === 'bazi') {
        if (!c.birth_dt_local) { errorMap.value[key] = '案例缺少出生时间，无法计算'; return }
        const [y, m, d, ...rest] = c.birth_dt_local.replace('T', '-').split(/[-T:]/)
        const hm = rest.join(':').slice(0, 5)
        const dt = `${y}-${m}-${d}T${hm}:00`
        const [sy, ey] = p.bazi.liunian_range
        const years: number[] = []
        for (let yr = sy; yr <= ey; yr++) years.push(yr)
        baziData.value = await computeFullBazi({
          dt, lon: c.lon, tz: c.tz,
          mode: p.bazi.mode,
          solar_time_enabled: p.bazi.solar_time_enabled,
          liunian_years: years,
        })
        sessionStorage.setItem(`report:bazi:${caseId.value}`, JSON.stringify({ data: baziData.value, ts: Date.now() }))
      } else if (key === 'ziwei') {
        if (!c.birth_dt_local) { errorMap.value[key] = '案例缺少出生时间，无法计算'; return }
        const dtParts = c.birth_dt_local.split('T')
        const [yr, mo, da] = dtParts[0].split('-').map(Number)
        const [hr, mi] = (dtParts[1] ?? '00:00').split(':').map(Number)
        ziweiData.value = await computeZiwei({
          year: yr, month: mo, day: da, hour: hr, minute: mi ?? 0,
          gender: genderToZh(c.gender),
          liunian_year: p.ziwei.liunian_year,
          longitude: c.lon,
          template_version: p.ziwei.template_version,
        })
        sessionStorage.setItem(`report:ziwei:${caseId.value}`, JSON.stringify({ data: ziweiData.value, ts: Date.now() }))
      } else if (key === 'name') {
        const fullName = p.name.name_override ?? c.name
        if (fullName.length < 2) throw new Error('姓名少于2字，无法分析')
        // 必须是纯汉字姓名（2-9字），非汉字的案例标签无法进行五格分析
        const chineseNameRe = /^[\u4e00-\u9fff]{2,9}$/
        if (!chineseNameRe.test(fullName)) {
          throw new Error(`"${fullName.slice(0, 10)}" 含非汉字或过长，请在参数控制中填写实际中文姓名（2-9字）`)
        }
        const surname = fullName.slice(0, 1)
        const givenName = fullName.slice(1)
        const birthYear = p.name.birth_year_override
          ?? (c.birth_dt_local ? Number(c.birth_dt_local.slice(0, 4)) : 0)
        nameData.value = await computeName({ surname, given_name: givenName, birth_year: birthYear })
        sessionStorage.setItem(`report:name:${caseId.value}`, JSON.stringify({ data: nameData.value, ts: Date.now() }))
      } else if (key === 'zeri') {
        if (!ziweiData.value) throw new Error('择日需先加载紫微命盘')
        const [yr, mo] = p.zeri.month.split('-').map(Number)
        // 从紫微命盘提取命宫地支
        const lifePalace = ziweiData.value.palaces.find((pa: { name: string }) => pa.name.includes('命'))
        const lifePalaceBranch = (lifePalace as { branch?: string })?.branch
          ?? ziweiData.value.life_palace_gz?.slice(-1)
          ?? ''
        zeriData.value = await fetchZeriRecommend({
          year: yr, month: mo,
          life_palace_branch: lifePalaceBranch,
          wuxing_ju_name: ziweiData.value.wuxing_ju_name,
          purpose: p.zeri.purpose,
        })
      } else if (key === 'fengshui') {
        const birthYear = p.fengshui.birth_year_override
          ?? (c.birth_dt_local ? Number(c.birth_dt_local.slice(0, 4)) : 0)
        const gender = p.fengshui.gender_override ?? genderToZh(c.gender)
        fengshuiData.value = await fetchFengshuiBagua({ birth_year: birthYear, gender })
      }
      cacheTimestamps.value[key] = Date.now()
    } catch (e: unknown) {
      const msg = (e as { message?: string; response?: { data?: { detail?: string } } })
        .response?.data?.detail ?? (e as Error).message ?? `${key} 计算失败`
      errorMap.value[key] = msg
    } finally {
      loadingMap.value[key] = false
    }
  }

  /** 单独加载风水八卦数据（chapter 5 的 5-2 小节使用） */
  async function loadFengshuiData(force = false) {
    if (!caseData.value) return
    const key = 'fengshui'
    if (!force && isCacheValid(key)) return
    if (loadingMap.value[key]) return
    loadingMap.value[key] = true
    errorMap.value[key] = null
    const c = caseData.value
    const p = chapterParams.value
    try {
      const birthYear = p.fengshui.birth_year_override
        ?? (c.birth_dt_local ? Number(c.birth_dt_local.slice(0, 4)) : 0)
      const gender = p.fengshui.gender_override ?? genderToZh(c.gender)
      fengshuiData.value = await fetchFengshuiBagua({ birth_year: birthYear, gender })
      cacheTimestamps.value[key] = Date.now()
    } catch (e: unknown) {
      const msg = (e as { message?: string; response?: { data?: { detail?: string } } })
        .response?.data?.detail ?? (e as Error).message ?? '风水数据加载失败'
      errorMap.value[key] = msg
    } finally {
      loadingMap.value[key] = false
    }
  }

  /** 应用 pendingParams 并重新计算当前章节 */
  async function applyParamsAndRecompute(chapterKey: string) {
    chapterParams.value = JSON.parse(JSON.stringify(pendingParams.value))
    dirtyParams.value[chapterKey] = false
    // 持久化参数到 sessionStorage
    if (caseId.value) {
      try {
        sessionStorage.setItem(
          `report:params:${caseId.value}`,
          JSON.stringify(chapterParams.value),
        )
      } catch { /* ignore */ }
    }
    // fengshui 是独立加载项（不属于任何章节 apiKey）
    if (chapterKey === 'fengshui') {
      await loadFengshuiData(true)
      return
    }
    const ch = CHAPTERS.find(c => c.key === chapterKey)
    if (ch) await loadChapterData(ch.num, true)
  }

  /** 清除所有章节缓存并重置数据（顶栏「重新计算」按钮使用） */
  function clearAllCache() {
    cacheTimestamps.value = {}
    baziData.value = null
    ziweiData.value = null
    nameData.value = null
    zeriData.value = null
    fengshuiData.value = null
    Object.keys(errorMap.value).forEach(k => { errorMap.value[k] = null })
  }

  /** 丢弃 pendingParams 的修改 */
  function discardParams(chapterKey: string) {
    pendingParams.value[chapterKey as keyof ChapterParams] =
      JSON.parse(JSON.stringify(chapterParams.value[chapterKey as keyof ChapterParams]))
    dirtyParams.value[chapterKey] = false
  }

  /** 更新 pendingParams（不立即触发计算，等用户点"重新计算"） */
  function updatePendingParam<K extends keyof ChapterParams>(
    chapterKey: K,
    patch: Partial<ChapterParams[K]>,
  ) {
    Object.assign(pendingParams.value[chapterKey] as object, patch)
    dirtyParams.value[chapterKey] = true
  }

  function setActiveChapter(num: number) {
    activeChapter.value = num
    activeSection.value = firstSectionId(num)
    // 如果章节有 API，触发懒加载
    const ch = CHAPTERS.find(c => c.num === num)
    if (ch?.hasApi) void loadChapterData(num)
  }

  function setActiveSection(id: string) {
    activeSection.value = id
  }

  function setGlossaryTerm(term: string | null) {
    glossaryTerm.value = term
    if (!term) { glossaryEntry.value = null; return }
    glossaryEntry.value = lookupGlossary(term) ?? { term, definition: '（词条暂未收录）' }
  }

  /** 切换卡2宫格详情模式；传 null 回到词条模式 */
  function setActivePalace(palaceIndex: number | null) {
    activePalaceIndex.value = palaceIndex
  }

  function saveNote(sectionId: string, text: string) {
    notes.value[sectionId] = text
    try {
      localStorage.setItem(`report:notes:${sectionId}`, text)
    } catch { /* ignore */ }
  }

  function toggleCard(cardId: string) {
    cardCollapsed.value[cardId] = !cardCollapsed.value[cardId]
    localStorage.setItem(`report:card:${cardId}:collapsed`, String(cardCollapsed.value[cardId]))
  }

  function toggleSectionDetail(sectionId: string) {
    sectionDetailExpanded.value[sectionId] = !sectionDetailExpanded.value[sectionId]
  }

  /** 恢复 sessionStorage 中缓存的章节数据 */
  function restoreFromSession() {
    if (!caseId.value) return
    const id = caseId.value
    const restore = <T>(key: string): T | null => {
      try {
        const s = sessionStorage.getItem(`report:${key}:${id}`)
        if (!s) return null
        const { data, ts } = JSON.parse(s)
        if (Date.now() - ts > CACHE_TTL) return null
        cacheTimestamps.value[key] = ts
        return data as T
      } catch { return null }
    }
    baziData.value = restore<BaziFullResponse>('bazi') ?? baziData.value
    ziweiData.value = restore<ZiweiResponse>('ziwei') ?? ziweiData.value
    nameData.value = restore<NameAnalysisResponse>('name') ?? nameData.value
    zeriData.value = restore<ZeriResponse>('zeri') ?? zeriData.value
    fengshuiData.value = restore<FengshuiResponse>('fengshui') ?? fengshuiData.value
    // 从 localStorage 按 sectionId 逐条恢复笔记
    try {
      const allSids = CHAPTERS.flatMap(c => c.sections.map((s: { id: string }) => s.id))
      const restoredNotes: Record<string, string> = {}
      for (const sid of allSids) {
        const n = localStorage.getItem(`report:notes:${sid}`)
        if (n) restoredNotes[sid] = n
      }
      if (Object.keys(restoredNotes).length) notes.value = restoredNotes
    } catch { /* ignore */ }
  }

  return {
    // state
    caseId, caseData, caseList, caseListError, caseLoading, caseError,
    baziData, ziweiData, nameData, zeriData, fengshuiData,
    loadingMap, errorMap, cacheTimestamps,
    activeChapter, activeSection, currentChapterDef,
    chapterParams, pendingParams, dirtyParams,
    glossaryTerm, glossaryEntry, activePalaceIndex,
    notes, cardCollapsed, sectionDetailExpanded,
    // computed
    isCacheValid, cacheAge,
    // actions
    loadCaseList, loadCase, loadChapterData, loadFengshuiData,
    applyParamsAndRecompute, discardParams, updatePendingParam,
    setActiveChapter, setActiveSection,
    clearAllCache,
    setGlossaryTerm, setActivePalace, saveNote, toggleCard, toggleSectionDetail,
    restoreFromSession,
  }
})
