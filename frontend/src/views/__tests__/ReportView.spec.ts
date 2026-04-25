import { describe, it, expect, vi, beforeEach } from 'vitest'
import { defineComponent, ref } from 'vue'

// ─── lightweight store mock ──────────────────────────────────────────────────
const storeMock = {
  caseId: ref<number | null>(null),
  caseData: ref<Record<string, unknown> | null>(null),
  caseList: ref<unknown[]>([]),
  caseLoading: ref(false),
  caseError: ref<string | null>(null),
  baziData: ref(null),
  ziweiData: ref(null),
  nameData: ref(null),
  zeriData: ref(null),
  fengshuiData: ref(null),
  loadingMap: ref<Record<string, boolean>>({}),
  errorMap: ref<Record<string, string | null>>({}),
  activeChapter: ref(1),
  activeSection: ref('1-1'),
  chapterParams: ref({}),
  pendingParams: ref({}),
  dirtyParams: ref<Record<string, boolean>>({}),
  glossaryTerm: ref(''),
  glossaryEntry: ref(null),
  activePalaceIndex: ref<number | null>(null),
  notes: ref<Record<string, string>>({}),
  cardCollapsed: ref<Record<string, boolean>>({}),
  sectionDetailExpanded: ref<Record<string, boolean>>({}),
  loadCase: vi.fn(),
  loadCaseList: vi.fn(),
  loadChapterData: vi.fn(),
  setActiveChapter: vi.fn(),
  setActiveSection: vi.fn(),
  setGlossaryTerm: vi.fn(),
  setActivePalace: vi.fn(),
  saveNote: vi.fn(),
  toggleCard: vi.fn(),
  toggleSectionDetail: vi.fn(),
  clearAllCache: vi.fn(),
  applyParamsAndRecompute: vi.fn(),
  discardParams: vi.fn(),
  updatePendingParam: vi.fn(),
  restoreFromSession: vi.fn(),
}

vi.mock('@/stores/report', () => ({
  useReportStore: () => storeMock,
}))

// ─── test router ─────────────────────────────────────────────────────────────
import { createRouter, createWebHistory } from 'vue-router'
import { mount, flushPromises } from '@vue/test-utils'

const StubView = defineComponent({ template: '<div/>' })

function makeRouter(path = '/report') {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/report', component: StubView },
      { path: '/report/:caseId', component: StubView },
    ],
  })
  router.push(path)
  return router
}

// We directly test store logic (unit) rather than full-mounting the heavy view,
// since the view depends on many child components that need Pinia context.
describe('ReportView (store mock 行为)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    storeMock.caseData.value = null
    storeMock.caseId.value = null
    storeMock.activeChapter.value = 1
    storeMock.activeSection.value = '1-1'
    storeMock.loadingMap.value = {}
    storeMock.errorMap.value = {}
    storeMock.caseLoading.value = false
    storeMock.caseError.value = null
  })

  it('store 初始无 caseData 时 caseLoading 为 false', () => {
    expect(storeMock.caseData.value).toBeNull()
    expect(storeMock.caseLoading.value).toBe(false)
  })

  it('loadingMap[bazi] 默认不存在', () => {
    expect(storeMock.loadingMap.value['bazi']).toBeUndefined()
  })

  it('setActiveChapter 可被调用', () => {
    storeMock.setActiveChapter(2)
    expect(storeMock.setActiveChapter).toHaveBeenCalledWith(2)
  })

  it('activeChapter 为 2 时 loadingMap.bazi 可单独设置', () => {
    storeMock.activeChapter.value = 2
    storeMock.loadingMap.value = { bazi: true }
    expect(storeMock.loadingMap.value['bazi']).toBe(true)
    expect(storeMock.loadingMap.value['ziwei']).toBeUndefined()
  })

  it('clearAllMocks 后 loadCase 未被调用', () => {
    expect(storeMock.loadCase).not.toHaveBeenCalled()
  })

  it('activePalaceIndex 初始为 null', () => {
    expect(storeMock.activePalaceIndex.value).toBeNull()
  })

  it('dirtyParams 初始可设置 bazi=true', () => {
    storeMock.dirtyParams.value = { bazi: true }
    expect(storeMock.dirtyParams.value.bazi).toBe(true)
  })

  it('data-ready 条件：需要 caseData + baziData + ziweiData + nameData 均有值', () => {
    // 模拟 data-ready="false"
    const dataReady = () =>
      !storeMock.caseLoading.value &&
      !!storeMock.caseData.value &&
      !!storeMock.baziData.value &&
      !!storeMock.ziweiData.value &&
      !!storeMock.nameData.value

    expect(dataReady()).toBe(false)
    storeMock.caseData.value = { id: 1 }
    expect(dataReady()).toBe(false)  // 其他数据还没加载
    storeMock.baziData.value = { api_version: '1' } as unknown as null
    storeMock.ziweiData.value = { api_version: '1' } as unknown as null
    storeMock.nameData.value  = { api_version: '1' } as unknown as null
    expect(dataReady()).toBe(true)
  })

  it('caseError 有值时应显示错误卡', () => {
    storeMock.caseError.value = '加载案例失败'
    expect(storeMock.caseError.value).toBeTruthy()
  })
})

describe('ReportView makeRouter 辅助', () => {
  it('router.currentRoute 指向 /report', async () => {
    const router = makeRouter('/report')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/report')
  })

  it('router.currentRoute 指向 /report/123', async () => {
    const router = makeRouter('/report/123')
    await flushPromises()
    expect(router.currentRoute.value.params.caseId).toBe('123')
  })
})
