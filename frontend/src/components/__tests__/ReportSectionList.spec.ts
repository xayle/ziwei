/**
 * ReportSectionList.spec.ts — 小节列表 + sectionStatus 逻辑测试
 * 覆盖：sectionStatus 5种状态、active类、chip行展开、click→setActiveSection
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { reactive, ref } from 'vue'
import ReportSectionList from '@/components/report/ReportSectionList.vue'
import { CHAPTERS } from '@/data/toc'

// ─── store mock ───────────────────────────────────────────────────
// Use reactive so DOM updates when we mutate storeMock inside tests
const storeMock = reactive({
  // currentChapterDef mirrors what the real store computes
  currentChapterDef: CHAPTERS.find(c => c.num === 2)!,   // default: ②八字
  activeSection: '2-1' as string | null,
  loadingMap: {} as Record<string, boolean>,
  errorMap: {} as Record<string, string | null>,
  baziData:     null as unknown,
  ziweiData:    null as unknown,
  nameData:     null as unknown,
  zeriData:     null as unknown,
  fengshuiData: null as unknown,
  setActiveSection: vi.fn(),
  setGlossaryTerm:  vi.fn(),
})

vi.mock('@/stores/report', () => ({
  useReportStore: () => storeMock,
}))

function mountList() {
  return mount(ReportSectionList, { global: { stubs: { transition: false } } })
}

// ─── helpers ──────────────────────────────────────────────────────
function resetStore() {
  storeMock.currentChapterDef = CHAPTERS.find(c => c.num === 2)!
  storeMock.activeSection = '2-1'
  storeMock.loadingMap = {}
  storeMock.errorMap = {}
  storeMock.baziData = null
  storeMock.ziweiData = null
  storeMock.nameData = null
  storeMock.zeriData = null
  storeMock.fengshuiData = null
  vi.clearAllMocks()
}

// ─── sectionStatus 逻辑（通过 DOM 状态符号验证）──────────────────

describe('ReportSectionList — sectionStatus: no-api (①个人信息)', () => {
  beforeEach(() => {
    resetStore()
    storeMock.currentChapterDef = CHAPTERS.find(c => c.num === 1)!
    storeMock.activeSection = '1-1'
  })

  it('①章节 hasApi=false，所有小节显示 — 符号', () => {
    const wrapper = mountList()
    const statusEls = wrapper.findAll('.section-status')
    statusEls.forEach(el => {
      expect(el.text().trim()).toBe('—')
    })
  })
})

describe('ReportSectionList — sectionStatus: idle (②八字，无数据)', () => {
  beforeEach(() => {
    resetStore()
    storeMock.currentChapterDef = CHAPTERS.find(c => c.num === 2)!
    storeMock.baziData = null
    storeMock.loadingMap = {}
    storeMock.errorMap = {}
  })

  it('无数据时小节显示 · 符号（idle）', () => {
    const wrapper = mountList()
    const statusEls = wrapper.findAll('.section-status')
    expect(statusEls.length).toBeGreaterThan(0)
    statusEls.forEach(el => {
      expect(el.text().trim()).toBe('·')
    })
  })
})

describe('ReportSectionList — sectionStatus: loaded', () => {
  beforeEach(() => {
    resetStore()
    storeMock.currentChapterDef = CHAPTERS.find(c => c.num === 2)!
    storeMock.baziData = { api_version: '2.0' }  // truthy
    storeMock.loadingMap = {}
    storeMock.errorMap = {}
  })

  it('baziData 有值时小节显示 ✓ 符号（loaded）', () => {
    const wrapper = mountList()
    const statusEls = wrapper.findAll('.section-status')
    expect(statusEls.length).toBeGreaterThan(0)
    statusEls.forEach(el => {
      expect(el.text().trim()).toBe('✓')
    })
  })
})

describe('ReportSectionList — sectionStatus: loading', () => {
  beforeEach(() => {
    resetStore()
    storeMock.currentChapterDef = CHAPTERS.find(c => c.num === 2)!
    storeMock.baziData = null
    storeMock.loadingMap = { bazi: true }
    storeMock.errorMap = {}
  })

  it('loading=true 时小节显示 ⟳ 符号（loading）', () => {
    const wrapper = mountList()
    const statusEls = wrapper.findAll('.section-status')
    expect(statusEls.length).toBeGreaterThan(0)
    statusEls.forEach(el => {
      expect(el.text().trim()).toBe('⟳')
    })
  })
})

describe('ReportSectionList — sectionStatus: error', () => {
  beforeEach(() => {
    resetStore()
    storeMock.currentChapterDef = CHAPTERS.find(c => c.num === 2)!
    storeMock.baziData = null
    storeMock.loadingMap = {}
    storeMock.errorMap = { bazi: '请求失败' }
  })

  it('errorMap 有值时小节显示 ✗ 符号（error）', () => {
    const wrapper = mountList()
    const statusEls = wrapper.findAll('.section-status')
    expect(statusEls.length).toBeGreaterThan(0)
    statusEls.forEach(el => {
      expect(el.text().trim()).toBe('✗')
    })
  })
})

// ─── 章节标题 + 渲染 ─────────────────────────────────────────────

describe('ReportSectionList — 章节标题渲染', () => {
  beforeEach(resetStore)

  it('②章节标题含 "八字四柱"', () => {
    const wrapper = mountList()
    expect(wrapper.find('.toc-chapter-label').text()).toContain('八字四柱')
  })

  it('③章节标题含 "紫微斗数"', () => {
    storeMock.currentChapterDef = CHAPTERS.find(c => c.num === 3)!
    storeMock.activeSection = '3-1'
    const wrapper = mountList()
    expect(wrapper.find('.toc-chapter-label').text()).toContain('紫微斗数')
  })

  it('⑦disabled章节显示 "尚未开放" 提示', () => {
    storeMock.currentChapterDef = CHAPTERS.find(c => c.num === 7)!
    storeMock.activeSection = null
    const wrapper = mountList()
    expect(wrapper.find('.toc-disabled').exists()).toBe(true)
    expect(wrapper.find('.section-list').exists()).toBe(false)
  })

  it('②章节渲染 8 个小节', () => {
    const wrapper = mountList()
    const items = wrapper.findAll('.section-item')
    expect(items).toHaveLength(8)
  })

  it('④ 姓名章节渲染 4 个小节', () => {
    storeMock.currentChapterDef = CHAPTERS.find(c => c.num === 4)!
    storeMock.activeSection = '4-1'
    const wrapper = mountList()
    expect(wrapper.findAll('.section-item')).toHaveLength(4)
  })
})

// ─── active 状态 ─────────────────────────────────────────────────

describe('ReportSectionList — active 小节高亮', () => {
  beforeEach(resetStore)

  it('activeSection=2-1 时第1个小节有 active 类', () => {
    storeMock.activeSection = '2-1'
    const wrapper = mountList()
    const items = wrapper.findAll('.section-item')
    expect(items[0].classes()).toContain('active')
    expect(items[1].classes()).not.toContain('active')
  })

  it('activeSection=2-5 时第5个小节有 active 类', () => {
    storeMock.activeSection = '2-5'
    const wrapper = mountList()
    const items = wrapper.findAll('.section-item')
    expect(items[4].classes()).toContain('active')
    for (let i = 0; i < 8; i++) {
      if (i !== 4) expect(items[i].classes()).not.toContain('active')
    }
  })
})

// ─── 点击小节 ────────────────────────────────────────────────────

describe('ReportSectionList — 点击小节', () => {
  beforeEach(resetStore)

  it('点击第2个小节调用 setActiveSection("2-2")', async () => {
    const wrapper = mountList()
    const items = wrapper.findAll('.section-item')
    await items[1].trigger('click')
    expect(storeMock.setActiveSection).toHaveBeenCalledWith('2-2')
  })

  it('点击第6个小节调用 setActiveSection("2-6")', async () => {
    const wrapper = mountList()
    const items = wrapper.findAll('.section-item')
    await items[5].trigger('click')
    expect(storeMock.setActiveSection).toHaveBeenCalledWith('2-6')
  })
})

// ─── 词条芯片（chip row）────────────────────────────────────────

describe('ReportSectionList — 词条芯片', () => {
  beforeEach(resetStore)

  it('激活小节（2-1）有词条时渲染 .chip-row', () => {
    // 2-1 有词条 ['四柱', '天干', ...]
    storeMock.activeSection = '2-1'
    const wrapper = mountList()
    const chipRow = wrapper.find('.chip-row')
    expect(chipRow.exists()).toBe(true)
  })

  it('chip 数量 <= 10', () => {
    storeMock.activeSection = '2-1'
    const wrapper = mountList()
    const chips = wrapper.findAll('.term-chip')
    expect(chips.length).toBeLessThanOrEqual(10)
  })

  it('点击 chip 调用 setGlossaryTerm', async () => {
    storeMock.activeSection = '2-1'
    const wrapper = mountList()
    const firstChip = wrapper.find('.term-chip')
    await firstChip.trigger('click')
    expect(storeMock.setGlossaryTerm).toHaveBeenCalled()
  })

  it('无词条的小节（2-8 有词条，activeSection=2-8）也渲染 chip', () => {
    storeMock.activeSection = '2-8'
    const wrapper = mountList()
    // 2-8 有词条 ['大运', '流年', '岁运并临']
    const chipRow = wrapper.find('.chip-row')
    expect(chipRow.exists()).toBe(true)
  })

  it('非激活小节不渲染 chip-row（只有激活小节显示chips）', () => {
    storeMock.activeSection = '2-1'
    const wrapper = mountList()
    // section-item active 的一行有 chip-row，其他行没有
    const items = wrapper.findAll('.section-item')
    // 只有 index=0 (2-1) 是 active 的，其他不应有 chip-row
    const nonActiveWithChips = items
      .filter((_, i) => i !== 0)
      .filter(item => item.find('.chip-row').exists())
    expect(nonActiveWithChips).toHaveLength(0)
  })
})
