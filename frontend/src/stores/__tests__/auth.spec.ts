/**
 * stores/auth.spec.ts — Pinia auth store 单元测试
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('初始状态：未登录', () => {
    const store = useAuthStore()
    expect(store.isLoggedIn).toBe(false)
    expect(store.token).toBeNull()
    expect(store.username).toBeNull()
  })

  it('setToken 后 isLoggedIn 为 true', () => {
    const store = useAuthStore()
    store.setToken('test-token-abc', 'admin')
    expect(store.isLoggedIn).toBe(true)
    expect(store.token).toBe('test-token-abc')
    expect(store.username).toBe('admin')
  })

  it('setToken 持久化到 localStorage', () => {
    const store = useAuthStore()
    store.setToken('tok-xyz', 'user1')
    expect(localStorage.getItem('token')).toBe('tok-xyz')
    expect(localStorage.getItem('username')).toBe('user1')
  })

  it('clearToken 后 isLoggedIn 为 false', () => {
    const store = useAuthStore()
    store.setToken('tok-xyz', 'user1')
    store.clearToken()
    expect(store.isLoggedIn).toBe(false)
    expect(store.token).toBeNull()
    expect(store.username).toBeNull()
  })

  it('clearToken 清除 localStorage', () => {
    const store = useAuthStore()
    store.setToken('tok', 'u')
    store.clearToken()
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('username')).toBeNull()
  })

  it('从 localStorage 恢复 token', () => {
    localStorage.setItem('token', 'saved-tok')
    localStorage.setItem('username', 'saved-user')
    // 重新创建 store（模拟页面刷新）
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.isLoggedIn).toBe(true)
    expect(store.token).toBe('saved-tok')
    expect(store.username).toBe('saved-user')
  })

  it('setToken 可不传 username', () => {
    const store = useAuthStore()
    store.setToken('tok-only')
    expect(store.isLoggedIn).toBe(true)
    expect(store.username).toBeNull()
  })
})
