/**
 * AppNav.spec.ts — AppNav 组件单元测试
 * 测试：主题切换、登录/登出状态显示、导航链接
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import { useAuthStore } from '@/stores/auth'

// ── router mock ──────────────────────────────────────────────
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div/>' } },
    { path: '/cases', component: { template: '<div/>' } },
    { path: '/login', component: { template: '<div/>' } },
    { path: '/ziwei', component: { template: '<div/>' } },
    { path: '/bazi',  component: { template: '<div/>' } },
    { path: '/name',  component: { template: '<div/>' } },
    { path: '/admin', component: { template: '<div/>' } },
  ],
})

function mountNav() {
  return mount(AppNav, {
    global: {
      plugins: [createPinia(), router],
    },
  })
}

describe('AppNav — 未登录状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    delete document.documentElement.dataset.theme
  })

  it('显示 Logo 链接', () => {
    const wrapper = mountNav()
    expect(wrapper.text()).toContain('命理系统')
  })

  it('未登录时不渲染导航链接', () => {
    const wrapper = mountNav()
    expect(wrapper.find('.nav-links').exists()).toBe(false)
  })

  it('未登录时不显示退出按钮', () => {
    const wrapper = mountNav()
    const logoutBtn = wrapper.findAll('button').find(b => b.text() === '退出')
    expect(logoutBtn).toBeUndefined()
  })
})

describe('AppNav — 已登录状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    delete document.documentElement.dataset.theme
  })

  async function mountLoggedIn(username = '天机') {
    const wrapper = mountNav()
    const auth = useAuthStore()
    auth.setToken('tok_test', username)
    await wrapper.vm.$nextTick()
    return wrapper
  }

  it('显示用户名', async () => {
    const wrapper = await mountLoggedIn('天机')
    expect(wrapper.text()).toContain('天机')
  })

  it('显示十一条导航链接', async () => {
    const wrapper = await mountLoggedIn()
    const links = wrapper.findAll('.nav-link')
    expect(links).toHaveLength(11)
    const labels = links.map(l => l.text())
    expect(labels).toContain('案例中心')
    expect(labels).toContain('报告书')
    expect(labels).toContain('八字排盘')
    expect(labels).toContain('紫微斗数')
    expect(labels).toContain('姓名学')
    expect(labels).toContain('择日')
    expect(labels).toContain('西方占星')
    expect(labels).toContain('数字学')
    expect(labels).toContain('合婚')
    expect(labels).toContain('塔罗')
    expect(labels).toContain('管理后台')
  })

  it('点击退出清除 token 并跳转 /login', async () => {
    const wrapper = await mountLoggedIn()
    const auth = useAuthStore()
    expect(auth.isLoggedIn).toBe(true)

    const logoutBtn = wrapper.findAll('button').find(b => b.text() === '退出')
    expect(logoutBtn).toBeDefined()
    await logoutBtn!.trigger('click')

    expect(auth.isLoggedIn).toBe(false)
    expect(auth.token).toBeNull()
  })
})

describe('AppNav — 主题切换', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    delete document.documentElement.dataset.theme
  })

  it('初始状态按钮显示 ☯（默认主题）', () => {
    const wrapper = mountNav()
    const btn = wrapper.find('.btn-theme')
    expect(btn.text()).toBe('☯')
  })

  it('点击切换到 bazi 主题，按钮变为 ☉', async () => {
    const wrapper = mountNav()
    const btn = wrapper.find('.btn-theme')
    await btn.trigger('click')
    expect(btn.text()).toBe('☉')
    expect(document.documentElement.dataset.theme).toBe('bazi')
    expect(localStorage.getItem('theme')).toBe('bazi')
  })

  it('再次点击还原默认主题', async () => {
    const wrapper = mountNav()
    const btn = wrapper.find('.btn-theme')
    await btn.trigger('click')  // → bazi
    await btn.trigger('click')  // → default
    expect(btn.text()).toBe('☯')
    expect(document.documentElement.dataset.theme).toBe(undefined)
    expect(localStorage.getItem('theme')).toBe('default')
  })

  it('fromLocalStorage 恢复 bazi 主题', async () => {
    localStorage.setItem('theme', 'bazi')
    const wrapper = mountNav()
    await wrapper.vm.$nextTick()
    const btn = wrapper.find('.btn-theme')
    expect(btn.text()).toBe('☉')
    expect(document.documentElement.dataset.theme).toBe('bazi')
  })
})
