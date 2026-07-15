import { createRouter, createWebHistory, type Router } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import { isArchiveReady } from '@/utils/profileReadiness'

const router = createRouter({
  history: createWebHistory('/static/app/'),
  scrollBehavior(to) {
    if (to.hash) {
      return { el: to.hash, top: 72, behavior: 'smooth' }
    }
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/new/NewHomeView.vue'),
      meta: { title: '首页' },
    },
    // NAV-03：首页仅以 `/` 为 canonical；旧入口收敛
    { path: '/home', redirect: '/' },
    { path: '/new', redirect: '/' },
    // ROUTE-01：后端/书签旧路径 → 现行 Vue 路由
    { path: '/cases', redirect: '/' },
    { path: '/bazi', redirect: '/new/bazi' },
    { path: '/ziwei', redirect: '/new/ziwei' },
    { path: '/admin', redirect: '/extensions' },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { title: '档案' },
    },
    {
      path: '/new/bazi',
      name: 'new-bazi',
      component: () => import('@/views/new/NewBaziView.vue'),
      meta: { title: '八字', requiresArchive: true },
    },
    {
      path: '/new/ziwei',
      name: 'new-ziwei',
      component: () => import('@/views/new/FushengZiweiView.vue'),
      meta: { title: '紫微', requiresArchive: true },
    },
    {
      path: '/new/ziwei/timeline',
      name: 'new-ziwei-timeline',
      component: () => import('@/views/new/FushengZiweiTimeline.vue'),
      meta: { title: '紫微运限', requiresArchive: true },
    },
    {
      path: '/report',
      name: 'report',
      component: () => import('@/views/ReportView.vue'),
      meta: { title: '报告', requiresArchive: true },
    },
    {
      path: '/relation/new',
      name: 'relation-new',
      component: () => import('@/views/RelationCompatView.vue'),
      meta: { title: '关系合盘', requiresArchive: true },
    },
    {
      path: '/extensions',
      name: 'extensions',
      component: () => import('@/views/extensions/ExtensionHubView.vue'),
      meta: { title: '扩展工具', requiresArchive: true },
    },
    {
      path: '/extensions/compat',
      name: 'extensions-compat',
      component: () => import('@/views/extensions/CompatView.vue'),
      meta: { title: '八字合婚', requiresArchive: true },
    },
    {
      path: '/extensions/ziwei-compat',
      name: 'extensions-ziwei-compat',
      component: () => import('@/views/extensions/ZiweiCompatView.vue'),
      meta: { title: '紫微合盘', requiresArchive: true },
    },
    {
      path: '/extensions/similarity',
      name: 'extensions-similarity',
      component: () => import('@/views/extensions/SimilarityView.vue'),
      meta: { title: '相似命盘', requiresArchive: true },
    },
    {
      path: '/extensions/zeri',
      name: 'extensions-zeri',
      component: () => import('@/views/extensions/ZeriView.vue'),
      meta: { title: '择日推荐', requiresArchive: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录', public: true },
    },
    {
      path: '/landing',
      name: 'landing',
      component: () => import('@/views/landing/LandingVolume.vue'),
      meta: { title: '卷首', public: true },
    },
    {
      path: '/payment/callback',
      name: 'payment-callback',
      component: () => import('@/views/payment/PaymentCallbackView.vue'),
      meta: { title: '支付结果', public: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

export function registerRouterGuards(target: Router) {
  target.beforeEach((to) => {
    if (to.meta.public) return true
    if (to.meta.requiresArchive) {
      const profile = useProfileStore()
      if (!isArchiveReady(profile.asProfileData())) {
        return {
          path: '/profile',
          query: { redirect: to.fullPath, reason: 'archive' },
        }
      }
    }
    return true
  })
}

router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} — 浮生` : '浮生 · 知命知心'
})

export default router
