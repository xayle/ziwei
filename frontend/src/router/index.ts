import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory('/static/app/'),
  routes: [
    {
      path: '/',
      redirect: '/home',
    },
    {
      path: '/home',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: '业务总览' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录', public: true },
    },
    {
      path: '/name',
      name: 'name',
      component: () => import('@/views/NameView.vue'),
      meta: { title: '姓名学' },
    },
    {
      path: '/bazi',
      name: 'bazi',
      component: () => import('@/views/BaziView.vue'),
      meta: { title: '八字排盘' },
    },
    {
      path: '/ziwei',
      name: 'ziwei',
      component: () => import('@/views/ZiweiView.vue'),
      meta: { title: '紫微斗数' },
    },
    {
      path: '/fengshui',
      name: 'fengshui',
      component: () => import('@/views/FengshuiView.vue'),
      meta: { title: '风水助手' },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminView.vue'),
      meta: { title: '管理后台' },
    },
    {
      path: '/workbench',
      name: 'workbench',
      component: () => import('@/views/WorkbenchView.vue'),
      meta: { title: '案例工作台' },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { title: '个人信息' },
    },
    {
      path: '/zeri',
      name: 'zeri',
      component: () => import('@/views/ZeriView.vue'),
      meta: { title: '择日推荐' },
    },
    {
      path: '/western',
      name: 'western',
      component: () => import('@/views/WesternView.vue'),
      meta: { title: '西方占星' },
    },
    {
      path: '/numerology',
      name: 'numerology',
      component: () => import('@/views/NumerologyView.vue'),
      meta: { title: '数字学' },
    },
    {
      path: '/compat',
      name: 'compat',
      component: () => import('@/views/CompatibilityView.vue'),
      meta: { title: '合婚诊断' },
    },
    {
      path: '/tarot',
      name: 'tarot',
      component: () => import('@/views/TarotView.vue'),
      meta: { title: '塔罗' },
    },
    {
      path: '/report',
      name: 'report',
      component: () => import('@/views/ReportView.vue'),
      meta: { title: '命理报告书' },
    },
    {
      path: '/report/:caseId',
      name: 'report-case',
      component: () => import('@/views/ReportView.vue'),
      meta: { title: '命理报告书' },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

// 导航守卫：已禁用登录验证，直接放行
router.beforeEach(() => true)

// 更新页面标题
router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} — 命理系统` : '命理系统'
})

export default router
