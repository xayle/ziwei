/**
 * stores/report.spec.ts — Pinia report store 单元测试
 * 聚焦于纯同步逻辑，不测试 API 调用（需 vitest mock）
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// ── 对 API 调用全部 mock 掉 ────────────────────────────────────

vi.mock('@/api/report', () => ({
  fetchCase: vi.fn(() => Promise.resolve({
    id: 1, name: '张三', gender: 'male',
    birth_dt_local: '1990-05-15T08:30:00',
    solar_time_enabled: false,
  })),
  fetchCaseList: vi.fn(() => Promise.resolve({ items: [] })),
  fetchBaziFull: vi.fn(() => Promise.reject(new Error('not used in these tests'))),
  fetchZiweiFull: vi.fn(() => Promise.reject(new Error('not used'))),
  fetchNameAnalysis: vi.fn(() => Promise.reject(new Error('not used'))),
  fetchZeriRecommend: vi.fn(() => Promise.reject(new Error('not used'))),
  fetchFengshuiBagua: vi.fn(() => Promise.reject(new Error('not used'))),
}))

vi.mock('@/api/cases', () => ({
  getCase: vi.fn(() => Promise.resolve({
    id: 1, name: '张三', gender: 'male',
    birth_dt_local: '1990-05-15T08:30:00',
    solar_time_enabled: false,
  })),
  listCases: vi.fn(() => Promise.resolve({ items: [] })),
}))

vi.mock('@/data/glossaryData', () => ({
  loadGlossary: vi.fn(() => Promise.resolve([])),
}))

import { useReportStore } from '@/stores/report'

// ─────────────────────────────────────────────────────────────────────────────
describe('useReportStore — 初始状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
    localStorage.clear()
  })

  it('caseData 初始为 null', () => {
    const store = useReportStore()
    expect(store.caseData).toBeNull()
  })

  it('activeChapter 初始为 1', () => {
    const store = useReportStore()
    expect(store.activeChapter).toBe(1)
  })

  it('activeSection 初始为 1-1', () => {
    const store = useReportStore()
    expect(store.activeSection).toBe('1-1')
  })

  it('dirtyParams 初始都为 false', () => {
    const store = useReportStore()
    for (const key of ['bazi', 'ziwei', 'name', 'zeri', 'fengshui']) {
      expect(store.dirtyParams[key]).toBe(false)
    }
  })

  it('chapterParams.bazi.mode 初始为 dual', () => {
    const store = useReportStore()
    expect(store.chapterParams.bazi.mode).toBe('dual')
  })

  it('chapterParams.ziwei.template_version 初始为 standard', () => {
    const store = useReportStore()
    expect(store.chapterParams.ziwei.template_version).toBe('standard')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('useReportStore — isCacheValid / cacheAge', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
  })

  it('无缓存时 isCacheValid(bazi) 为 false', () => {
    const store = useReportStore()
    expect(store.isCacheValid('bazi')).toBe(false)
  })

  it('无缓存时 cacheAge(bazi) 返回空字符串', () => {
    const store = useReportStore()
    expect(store.cacheAge('bazi')).toBe('')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('useReportStore — updatePendingParam / dirtyParams', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
  })

  it('updatePendingParam 将 dirtyParams.bazi 置为 true', () => {
    const store = useReportStore()
    expect(store.dirtyParams.bazi).toBe(false)
    store.updatePendingParam('bazi', { mode: 'single' })
    expect(store.dirtyParams.bazi).toBe(true)
  })

  it('updatePendingParam 更新 pendingParams 但不改 chapterParams', () => {
    const store = useReportStore()
    store.updatePendingParam('bazi', { mode: 'single' })
    expect(store.pendingParams.bazi.mode).toBe('single')
    expect(store.chapterParams.bazi.mode).toBe('dual')  // 原值不变
  })

  it('discardParams 还原 pendingParams 并清除 dirty', () => {
    const store = useReportStore()
    store.updatePendingParam('bazi', { mode: 'single' })
    expect(store.dirtyParams.bazi).toBe(true)
    store.discardParams('bazi')
    expect(store.pendingParams.bazi.mode).toBe('dual')
    expect(store.dirtyParams.bazi).toBe(false)
  })

  it('修改多个参数时其他 key 的 dirty 不受影响', () => {
    const store = useReportStore()
    store.updatePendingParam('ziwei', { template_version: 'pro' })
    expect(store.dirtyParams.ziwei).toBe(true)
    expect(store.dirtyParams.bazi).toBe(false)
    expect(store.dirtyParams.name).toBe(false)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('useReportStore — clearAllCache', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
  })

  it('clearAllCache 后 baziData/ziweiData/nameData 均为 null', () => {
    const store = useReportStore()
    // 模拟有数据的状态
    ;(store as unknown as Record<string, unknown>).baziData = { api_version: '1' }
    store.clearAllCache()
    expect(store.baziData).toBeNull()
    expect(store.ziweiData).toBeNull()
    expect(store.nameData).toBeNull()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('useReportStore — setActiveChapter / setActiveSection', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
  })

  it('setActiveSection 更新 activeSection', () => {
    const store = useReportStore()
    store.setActiveSection('2-3')
    expect(store.activeSection).toBe('2-3')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('useReportStore — toggleCard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    sessionStorage.clear()
  })
  afterEach(() => {
    localStorage.clear()
  })

  it('cardCollapsed.overview 初始为 false', () => {
    const store = useReportStore()
    expect(store.cardCollapsed.overview).toBe(false)
  })

  it('toggleCard(overview) 后 collapsed 变为 true', () => {
    const store = useReportStore()
    store.toggleCard('overview')
    expect(store.cardCollapsed.overview).toBe(true)
  })

  it('再次 toggleCard(overview) 恢复 false', () => {
    const store = useReportStore()
    store.toggleCard('overview')
    store.toggleCard('overview')
    expect(store.cardCollapsed.overview).toBe(false)
  })

  it('toggleCard 将状态写入 localStorage', () => {
    const store = useReportStore()
    store.toggleCard('overview')
    expect(localStorage.getItem('report:card:overview:collapsed')).toBe('true')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('useReportStore — toggleSectionDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
  })

  it('初始时所有 sectionDetailExpanded 为空', () => {
    const store = useReportStore()
    expect(Object.keys(store.sectionDetailExpanded)).toHaveLength(0)
  })

  it('toggleSectionDetail 切换指定 section', () => {
    const store = useReportStore()
    store.toggleSectionDetail('2-3')
    expect(store.sectionDetailExpanded['2-3']).toBe(true)
    store.toggleSectionDetail('2-3')
    expect(store.sectionDetailExpanded['2-3']).toBe(false)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('useReportStore — saveNote', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
  })

  it('saveNote 保存笔记到 notes[sectionId]', () => {
    const store = useReportStore()
    store.saveNote('2-1', '这是一段批注')
    expect(store.notes['2-1']).toBe('这是一段批注')
  })

  it('多个 sectionId 的笔记独立存储', () => {
    const store = useReportStore()
    store.saveNote('2-1', '批注A')
    store.saveNote('3-2', '批注B')
    expect(store.notes['2-1']).toBe('批注A')
    expect(store.notes['3-2']).toBe('批注B')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('useReportStore — setActivePalace', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
  })

  it('初始 activePalaceIndex 为 null', () => {
    const store = useReportStore()
    expect(store.activePalaceIndex).toBeNull()
  })

  it('setActivePalace(3) 设置 index', () => {
    const store = useReportStore()
    store.setActivePalace(3)
    expect(store.activePalaceIndex).toBe(3)
  })

  it('setActivePalace(null) 回到词条模式', () => {
    const store = useReportStore()
    store.setActivePalace(3)
    store.setActivePalace(null)
    expect(store.activePalaceIndex).toBeNull()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('useReportStore — loadCase（mock API）', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
    localStorage.clear()
  })

  it('loadCase 设置 caseId', async () => {
    const store = useReportStore()
    await store.loadCase('42')
    expect(store.caseId).toBe('42')
  })

  it('loadCase 成功后 caseLoading 为 false', async () => {
    const store = useReportStore()
    await store.loadCase('1')
    expect(store.caseLoading).toBe(false)
  })

  it('loadCase 成功后 caseData 正确', async () => {
    const store = useReportStore()
    await store.loadCase('1')
    expect(store.caseData).not.toBeNull()
    expect(store.caseData?.name).toBe('张三')
  })

  it('切换案例 id 时 activeChapter 重置为 1', async () => {
    const store = useReportStore()
    await store.loadCase('1')
    store.setActiveSection('2-3')
    await store.loadCase('2')          // 不同 id → isNewCase 触发
    expect(store.activeChapter).toBe(1)
    expect(store.activeSection).toBe('1-1')
  })

  it('切换案例时 notes 被清空', async () => {
    const store = useReportStore()
    await store.loadCase('1')
    store.saveNote('2-1', '笔记')
    await store.loadCase('2')
    expect(Object.keys(store.notes)).toHaveLength(0)
  })

  it('同一案例重复 loadCase 不重复请求（有效 cache）', async () => {
    const { fetchCase } = await import('@/api/report')
    const spy = vi.mocked(fetchCase)
    spy.mockClear()
    const store = useReportStore()
    await store.loadCase('99')
    await store.loadCase('99')  // 第二次命中 cache，不发请求
    // 第二次不应该再调 API（isCacheValid 为 true）
    expect(spy).toHaveBeenCalledTimes(1)
  })
})
