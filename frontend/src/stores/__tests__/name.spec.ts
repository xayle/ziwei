/**
 * stores/name.spec.ts — Pinia name store 单元测试
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useNameStore } from '@/stores/name'

describe('useNameStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('初始状态：所有字段为默认值', () => {
    const store = useNameStore()
    expect(store.analyzeResult).toBeNull()
    expect(store.suggestResult).toBeNull()
    expect(store.analyzeLoading).toBe(false)
    expect(store.suggestLoading).toBe(false)
    expect(store.prefillSurname).toBe('')
    expect(store.prefillElements).toEqual([])
  })

  it('setPrefill 正确设置预填参数', () => {
    const store = useNameStore()
    store.setPrefill('张', ['水', '木'])
    expect(store.prefillSurname).toBe('张')
    expect(store.prefillElements).toEqual(['水', '木'])
  })

  it('setPrefill 清空：传入空值', () => {
    const store = useNameStore()
    store.setPrefill('张', ['水'])
    store.setPrefill('', [])
    expect(store.prefillSurname).toBe('')
    expect(store.prefillElements).toEqual([])
  })

  it('clearAnalyze 重置分析结果', () => {
    const store = useNameStore()
    store.analyzeResult = { surname: '张', given_name: '伟' } as any
    store.analyzeError = '错误信息'
    store.clearAnalyze()
    expect(store.analyzeResult).toBeNull()
    expect(store.analyzeError).toBeNull()
  })

  it('clearSuggest 重置建议结果', () => {
    const store = useNameStore()
    store.suggestResult = { surname: '张', suggestions: [] } as any
    store.suggestError = '错误'
    store.clearSuggest()
    expect(store.suggestResult).toBeNull()
    expect(store.suggestError).toBeNull()
  })
})
