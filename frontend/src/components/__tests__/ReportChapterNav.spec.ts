/**
 * ReportChapterNav.spec.ts — 章节导航栏组件测试
 * 覆盖：8个章节按钮状态、active类、disabled章节、click→setActiveChapter
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ReportChapterNav from '@/components/report/ReportChapterNav.vue'

// ─── store mock ───────────────────────────────────────────────────
// 使用 reactive 使 activeChapter 在模板中透明展开（不是 ref 对象）
const setActiveChapter = vi.fn()
const storeMock = reactive({
  activeChapter: 1,
  setActiveChapter,
})

vi.mock('@/stores/report', () => ({
  useReportStore: () => storeMock,
}))

// ─── router ───────────────────────────────────────────────────────
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div/>' } },
    { path: '/report', component: { template: '<div/>' } },
    { path: '/report/:caseId', component: { template: '<div/>' } },
  ],
})

function mountNav() {
  return mount(ReportChapterNav, { global: { plugins: [router] } })
}

// ReportChapterNav uses store.activeChapter directly (the ref value via Pinia unwrap).
// In the mock, store.activeChapter IS the ref, so template binds correctly.

describe('ReportChapterNav — 按钮渲染', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    storeMock.activeChapter = 1
  })

  it('渲染 8 个章节按钮（CHAPTERS数组）', () => {
    const wrapper = mountNav()
    // all .nav-icon buttons minus the top case-picker button
    const allBtns = wrapper.findAll('button.nav-icon')
    // 1 top + 8 chapters = 9 total
    expect(allBtns).toHaveLength(9)
  })

  it('顶部案例切换按钮（📚）存在', () => {
    const wrapper = mountNav()
    const topBtn = wrapper.find('.nav-icon--top')
    expect(topBtn.exists()).toBe(true)
    expect(topBtn.text()).toContain('📚')
  })

  it('章节按钮显示 icon-num 序号 1~8', () => {
    const wrapper = mountNav()
    const nums = wrapper.findAll('.icon-num').map(n => n.text())
    ;['1', '2', '3', '4', '5', '6', '7', '8'].forEach(n => {
      expect(nums).toContain(n)
    })
  })

  it('⑦⑧ 章节按钮有 disabled 属性', () => {
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    const ch7 = allBtns[6]
    const ch8 = allBtns[7]
    expect(ch7.attributes('disabled')).toBeDefined()
    expect(ch8.attributes('disabled')).toBeDefined()
  })

  it('⑦⑧ 章节按钮有 disabled 类', () => {
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    expect(allBtns[6].classes()).toContain('disabled')
    expect(allBtns[7].classes()).toContain('disabled')
  })

  it('①~⑥ 章节按钮不含 disabled 类', () => {
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    for (let i = 0; i < 6; i++) {
      expect(allBtns[i].classes()).not.toContain('disabled')
    }
  })
})

describe('ReportChapterNav — active 状态', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('activeChapter=1 时，第1个章节按钮有 active 类', () => {
    storeMock.activeChapter = 1
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    expect(allBtns[0].classes()).toContain('active')
    expect(allBtns[1].classes()).not.toContain('active')
  })

  it('activeChapter=2 时，第2个章节按钮有 active 类', () => {
    storeMock.activeChapter = 2
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    expect(allBtns[0].classes()).not.toContain('active')
    expect(allBtns[1].classes()).toContain('active')
  })

  it('activeChapter=5 时，第5个章节按钮有 active 类', () => {
    storeMock.activeChapter = 5
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    expect(allBtns[4].classes()).toContain('active')
    for (let i = 0; i < 8; i++) {
      if (i !== 4) expect(allBtns[i].classes()).not.toContain('active')
    }
  })
})

describe('ReportChapterNav — 点击交互', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    storeMock.activeChapter = 1
  })

  it('点击章节 1 调用 setActiveChapter(1)', async () => {
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    await allBtns[0].trigger('click')
    expect(setActiveChapter).toHaveBeenCalledWith(1)
  })

  it('点击章节 2 调用 setActiveChapter(2)', async () => {
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    await allBtns[1].trigger('click')
    expect(setActiveChapter).toHaveBeenCalledWith(2)
  })

  it('点击章节 6 调用 setActiveChapter(6)', async () => {
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    await allBtns[5].trigger('click')
    expect(setActiveChapter).toHaveBeenCalledWith(6)
  })

  it('点击 disabled 章节（⑦）不调用 setActiveChapter', async () => {
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    await allBtns[6].trigger('click')
    expect(setActiveChapter).not.toHaveBeenCalled()
  })

  it('点击 disabled 章节（⑧）不调用 setActiveChapter', async () => {
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    await allBtns[7].trigger('click')
    expect(setActiveChapter).not.toHaveBeenCalled()
  })

  it('连续点击两个不同章节，setActiveChapter 被正确调用两次', async () => {
    const wrapper = mountNav()
    const allBtns = wrapper.findAll('button.nav-icon:not(.nav-icon--top)')
    await allBtns[1].trigger('click')  // ch2
    await allBtns[2].trigger('click')  // ch3
    expect(setActiveChapter).toHaveBeenCalledTimes(2)
    expect(setActiveChapter).toHaveBeenNthCalledWith(1, 2)
    expect(setActiveChapter).toHaveBeenNthCalledWith(2, 3)
  })
})
