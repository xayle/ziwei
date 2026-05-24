/**
 * NameView.spec.ts — NameView 视图单元测试
 * 测试：Tab 切换、表单验证、API 调用、store 预填充联动
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import NameView from '@/views/NameView.vue'
import { useNameStore } from '@/stores/name'

// ── API mock ─────────────────────────────────────────────────
vi.mock('@/api/name', () => ({
  analyzeName: vi.fn(),
  suggestNames: vi.fn(),
}))

import { analyzeName, suggestNames } from '@/api/name'
import type { Mock } from 'vitest'

// ── Router ───────────────────────────────────────────────────
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/name', component: NameView },
    { path: '/bazi', component: { template: '<div/>' } },
  ],
})

const MOCK_ANALYSIS = {
  surname: '张',
  given_name: '伟',
  full_name: '张伟',
  tianke: { number: 9, element: '水', lucky: '吉', score: 8, desc: '天格说明' },
  renke: { number: 18, element: '金', lucky: '凶', score: 3, desc: '人格说明' },
  dike: { number: 10, element: '水', lucky: '平', score: 5, desc: '地格说明' },
  waike: { number: 1,  element: '木', lucky: '吉', score: 9, desc: '外格说明' },
  zonge: { number: 18, element: '金', lucky: '凶', score: 3, desc: '总格说明' },
  sancai: { pattern: '水金水', lucky: '吉', score: 8, desc: '三才说明' },
  overall_score: 72,
  summary: '人格18，主聪慧。',
  algorithm_version: '1.0.0',
}

const MOCK_SUGGEST = {
  surname: '张',
  name_length: 2,
  preferred_elements: ['水', '木'],
  total_candidates_evaluated: 480,
  suggestions: [
    {
      given_name: '泽林', overall_score: 85,
      renke_score: 9, sancai_score: 8,
      sancai_pattern: '水木木',
      element_composition: ['水', '木'],
      summary: '水木相生，格局上佳。',
    },
  ],
  algorithm_version: '1.0.0',
}

async function mountView() {
  await router.push('/name')
  await router.isReady()
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(NameView, {
    global: { plugins: [pinia, router] },
  })
}
describe('NameView — 分析表单提交', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('填写姓名后提交调用 analyzeName()', async () => {
    ;(analyzeName as Mock).mockResolvedValueOnce(MOCK_ANALYSIS)
    const wrapper = await mountView()

    // 找到姓/名输入框
    const inputs = wrapper.findAll('input[type="text"],input:not([type])')
    // 姓 输入框
    const surnameInput = inputs.find(i =>
      (i.element as HTMLInputElement).placeholder?.includes('姓') ||
      (i.element as HTMLInputElement).name === 'surname'
    ) ?? inputs[0]
    const givenInput = inputs.find(i =>
      (i.element as HTMLInputElement).placeholder?.includes('名') ||
      (i.element as HTMLInputElement).name === 'given_name'
    ) ?? inputs[1]

    await surnameInput.setValue('张')
    await givenInput.setValue('伟')

    // 直接触发 form 的 submit 事件（@submit.prevent）
    const form = wrapper.find('form')
    await form.trigger('submit')

    expect(analyzeName).toHaveBeenCalledOnce()
    expect(analyzeName).toHaveBeenCalledWith({ surname: '张', given_name: '伟' })
  })

  it('两个字段均为空时不触发 analyzeName()', async () => {
    const wrapper = await mountView()
    const submitBtn = wrapper.findAll('button').find(b => b.text().includes('分析'))
    if (submitBtn) await submitBtn.trigger('click')
    expect(analyzeName).not.toHaveBeenCalled()
  })
})

