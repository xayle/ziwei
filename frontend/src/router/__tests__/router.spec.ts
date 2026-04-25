/**
 * router.spec.ts — 路由守卫 + NotFoundView 单元测试
 * 测试：未登录重定向 /login / 已登录正常导航 / 404 页面渲染 / document.title 更新
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import NotFoundView from '@/views/NotFoundView.vue'

// ── 使用简化路由（不引入真实懒加载视图，避免额外依赖）────
const HomeStub   = { template: '<div>home</div>' }
const LoginStub  = { template: '<div>login</div>' }
const NameStub   = { template: '<div>name</div>' }

function makeRouter() {
  const r = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', redirect: '/name' },
      { path: '/login', name: 'login', component: LoginStub, meta: { title: '登录', public: true } },
      { path: '/name',  name: 'name',  component: NameStub,  meta: { title: '姓名学' } },
      { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
    ],
  })

  // 复制真实路由守卫逻辑
  r.beforeEach((to) => {
    if (to.meta.public) return true
    const auth = useAuthStore()
    if (!auth.isLoggedIn) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    return true
  })

  r.afterEach((to) => {
    const title = to.meta.title as string | undefined
    document.title = title ? `${title} — 命理系统` : '命理系统'
  })

  return r
}

// ─────────────────────────────────────────────────────────
describe('路由守卫 — 未登录', () => {
  beforeEach(() => {
    const pinia = createPinia()
    setActivePinia(pinia)
  })

  it('访问受保护路由 /name 被重定向到 /login', async () => {
    const router = makeRouter()
    await router.push('/name')
    await flushPromises()
    expect(router.currentRoute.value.name).toBe('login')
  })

  it('重定向时带 redirect 查询参数', async () => {
    const router = makeRouter()
    await router.push('/name')
    await flushPromises()
    expect(router.currentRoute.value.query.redirect).toBe('/name')
  })

  it('访问 /login（public）不被重定向', async () => {
    const router = makeRouter()
    await router.push('/login')
    await flushPromises()
    expect(router.currentRoute.value.name).toBe('login')
  })
})

// ─────────────────────────────────────────────────────────
describe('路由守卫 — 已登录', () => {
  beforeEach(() => {
    const pinia = createPinia()
    setActivePinia(pinia)
    // 模拟登录状态
    const auth = useAuthStore()
    auth.setToken('valid-token', 'testuser')
  })

  it('访问 /name 正常导航（不重定向）', async () => {
    const router = makeRouter()
    await router.push('/name')
    await flushPromises()
    expect(router.currentRoute.value.name).toBe('name')
  })
})

// ─────────────────────────────────────────────────────────
describe('路由 afterEach — document.title', () => {
  beforeEach(() => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const auth = useAuthStore()
    auth.setToken('valid-token', 'testuser')
  })

  it('有 meta.title 时更新标题', async () => {
    const router = makeRouter()
    await router.push('/name')
    await flushPromises()
    expect(document.title).toBe('姓名学 — 命理系统')
  })

  it('无 meta.title 时显示默认标题', async () => {
    const router = makeRouter()
    await router.push('/unknown-path')
    await flushPromises()
    expect(document.title).toBe('命理系统')
  })
})

// ─────────────────────────────────────────────────────────
describe('NotFoundView — 渲染', () => {
  it('显示 404 标题', () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const router = makeRouter()
    const wrapper = mount(NotFoundView, {
      global: { plugins: [pinia, router] },
    })
    expect(wrapper.text()).toContain('404')
    expect(wrapper.text()).toContain('页面不存在')
  })

  it('包含「返回首页」链接', () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const router = makeRouter()
    const wrapper = mount(NotFoundView, {
      global: { plugins: [pinia, router] },
    })
    const link = wrapper.find('a')
    expect(link.exists()).toBe(true)
    expect(link.text()).toContain('返回首页')
  })
})
