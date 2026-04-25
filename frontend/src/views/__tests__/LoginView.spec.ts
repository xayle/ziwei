/**
 * views/LoginView.spec.ts — LoginView 组件渲染测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHashHistory } from 'vue-router'

// mock auth API
vi.mock('@/api/auth', () => ({
  login: vi.fn(),
}))

import { login } from '@/api/auth'
import LoginView from '@/views/LoginView.vue'

function makeRouter() {
  return createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: '/', component: { template: '<div>Home</div>' } },
      { path: '/login', component: LoginView },
    ],
  })
}

describe('LoginView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('渲染登录表单', () => {
    const router = makeRouter()
    const wrapper = mount(LoginView, {
      global: { plugins: [createPinia(), router] },
    })
    expect(wrapper.find('input[type="text"]').exists()).toBe(true)
    expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    expect(wrapper.find('button.btn-login').exists()).toBe(true)
  })

  it('空表单提交：调用 API 并显示默认错误提示', async () => {
    const mockLogin = login as ReturnType<typeof vi.fn>
    mockLogin.mockRejectedValueOnce({}) // 无 detail 字段
    const router = makeRouter()
    const wrapper = mount(LoginView, {
      global: { plugins: [createPinia(), router] },
    })
    await wrapper.find('button.btn-login').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('登录失败，请检查服务是否启动')
  })

  it('登录成功：存储 token 并跳转', async () => {
    const mockLogin = login as ReturnType<typeof vi.fn>
    mockLogin.mockResolvedValueOnce({
      access_token: 'tok-ok',
      refresh_token: 'ref-ok',
      token_type: 'bearer',
      expires_in: 3600,
    })

    const router = makeRouter()
    await router.push('/login')
    const wrapper = mount(LoginView, {
      global: { plugins: [createPinia(), router] },
    })

    await wrapper.find('input[type="text"]').setValue('admin')
    await wrapper.find('input[type="password"]').setValue('pass123')
    await wrapper.find('button.btn-login').trigger('click')
    await flushPromises()

    expect(localStorage.getItem('token')).toBe('tok-ok')
  })

  it('登录失败 401：显示默认错误信息', async () => {
    const mockLogin = login as ReturnType<typeof vi.fn>
    mockLogin.mockRejectedValueOnce({ response: { status: 401, data: {} } })

    const router = makeRouter()
    const wrapper = mount(LoginView, {
      global: { plugins: [createPinia(), router] },
    })

    await wrapper.find('input[type="text"]').setValue('bad')
    await wrapper.find('input[type="password"]').setValue('bad')
    await wrapper.find('button.btn-login').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('登录失败，请检查服务是否启动')
  })

  it('登录按钮禁用状态：loading 中不可点击', async () => {
    const mockLogin = login as ReturnType<typeof vi.fn>
    // never resolves → 保持 loading 状态
    mockLogin.mockImplementationOnce(() => new Promise(() => {}))

    const router = makeRouter()
    const wrapper = mount(LoginView, {
      global: { plugins: [createPinia(), router] },
    })

    await wrapper.find('input[type="text"]').setValue('admin')
    await wrapper.find('input[type="password"]').setValue('pass')
    await wrapper.find('button.btn-login').trigger('click')

    const btn = wrapper.find('button.btn-login')
    expect((btn.element as HTMLButtonElement).disabled).toBe(true)
    expect(btn.text()).toContain('登录中')
  })
})
