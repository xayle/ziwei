<script setup lang="ts">
import { useThemePreference } from '@/composables/useThemePreference'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()

const navItems = [
  { path: '/cases',     label: '案例中心' },
  { path: '/report',    label: '报告书' },
  { path: '/bazi',      label: '八字排盘' },
  { path: '/ziwei',     label: '紫微斗数' },
  { path: '/name',      label: '姓名学' },
  { path: '/zeri',      label: '择日' },
  { path: '/western',   label: '西方占星' },
  { path: '/numerology',label: '数字学' },
  { path: '/compat',    label: '合婚' },
  { path: '/tarot',     label: '塔罗' },
  { path: '/admin',     label: '管理后台' },
]

const { theme, toggleTheme } = useThemePreference()

function logout() {
  auth.clearToken()
  router.push('/login')
}
</script>

<template>
  <header class="app-nav">
    <div class="nav-wrap">
      <RouterLink class="nav-logo" to="/">命理系统</RouterLink>
      <nav class="nav-links" v-if="auth.isLoggedIn">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="['nav-link', { active: route.path.startsWith(item.path) }]"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
      <div class="nav-right">
        <button class="btn-theme" :title="theme === 'bazi' ? '切换科技主题' : '切换山水主题'" @click="toggleTheme">
          {{ theme === 'bazi' ? '☉' : '☯' }}
        </button>
        <span v-if="auth.isLoggedIn" class="nav-user">{{ auth.username }}</span>
        <button v-if="auth.isLoggedIn" class="btn-logout" @click="logout">退出</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--hdr-bg);
  color: var(--hdr-fg);
  height: 56px;
  box-shadow: 0 1px 4px rgba(0,0,0,.3);
}

.nav-wrap {
  max-width: var(--W);
  margin: 0 auto;
  padding: 0 var(--sp-4);
  height: 100%;
  display: flex;
  align-items: center;
  gap: var(--sp-8);
}

.nav-logo {
  font-size: var(--fs-lg);
  font-weight: 700;
  color: var(--hdr-fg);
  letter-spacing: 0.02em;
  text-decoration: none;
  flex-shrink: 0;
}

.nav-links {
  display: flex;
  gap: var(--sp-2);
  flex: 1;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-left: auto;
}

.nav-user {
  font-size: var(--fs-sm);
  color: var(--hdr-fg-2);
}

.btn-logout {
  padding: 5px 12px;
  background: transparent;
  color: var(--hdr-fg-2);
  border: 1px solid rgba(255,255,255,.25);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  cursor: pointer;
  transition: all var(--dur-fast);
}

.btn-logout:hover {
  background: rgba(255,255,255,.1);
  color: var(--hdr-fg);
}

.btn-theme {
  padding: 4px 8px;
  background: transparent;
  color: var(--hdr-fg-2);
  border: 1px solid rgba(255,255,255,.2);
  border-radius: var(--radius-sm);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  transition: all var(--dur-fast);
  user-select: none;
}

.btn-theme:hover {
  background: rgba(255,255,255,.1);
  color: var(--hdr-fg);
  transform: rotate(20deg);
}

.nav-link {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  color: var(--hdr-fg-2);
  font-size: var(--fs-md);
  text-decoration: none;
  transition: color var(--dur-fast), background var(--dur-fast);
}

.nav-link:hover {
  color: var(--hdr-fg);
  background: rgba(255,255,255,.08);
}

.nav-link.active {
  color: var(--hdr-fg);
  background: rgba(255,255,255,.12);
}
</style>
