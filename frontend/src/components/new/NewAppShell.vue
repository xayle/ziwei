<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import brandMark from '@/assets/brand/fusheng-mark.svg'
import { useFushengFlow } from '@/composables/useFushengFlow'
import { useVolumeRouteMeta } from '@/composables/useVolumeRouteMeta'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { flowSteps } = useFushengFlow()
const volumeMeta = useVolumeRouteMeta()
const backendDown = ref(false)

const navItems = computed(() => flowSteps.value)

function isHomePath(path: string) {
  return path === '/' || path === '/home' || path === '/new'
}

function isNavItemActive(item: { id: string; path: string }) {
  if (item.id === 'home') return isHomePath(route.path)
  if (item.id === 'extensions') return route.path.startsWith('/extensions')
  if (item.id === 'ziwei') return route.path.startsWith('/new/ziwei')
  return route.path === item.path
}

const activeLabel = computed(() => {
  if (isHomePath(route.path)) return '首页'
  const matched = navItems.value.find((item) => isNavItemActive(item))
  return matched?.label || volumeMeta.value.pageTitle
})

const volumeEyebrow = computed(() => (
  isHomePath(route.path) ? null : volumeMeta.value.volumeLabel
))

function onBackendUnavailable() {
  backendDown.value = true
}

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

onMounted(() => {
  window.addEventListener('app:backend-unavailable', onBackendUnavailable)
})

onUnmounted(() => {
  window.removeEventListener('app:backend-unavailable', onBackendUnavailable)
})
</script>

<template>
  <div class="shell" :class="{ 'shell--home': isHomePath(route.path) }">
    <p v-if="backendDown" class="backend-banner">
      后端服务暂不可用，排盘与报告可能失败。请确认 API 已启动后刷新页面。
      <button type="button" class="backend-banner__dismiss" @click="backendDown = false">知道了</button>
    </p>
    <header class="bar">
      <div class="brand-block">
        <img class="brand-logo" :src="brandMark" alt="浮生" width="44" height="44" />
        <div v-if="!isHomePath(route.path)" class="title-block">
          <p v-if="volumeEyebrow" class="eyebrow">{{ volumeEyebrow }}</p>
          <h1>{{ activeLabel }}</h1>
        </div>
      </div>

      <nav class="nav nav--desktop" aria-label="主导航">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          class="nav-btn"
          :class="{
            'is-active': isNavItemActive(item),
            'is-locked': !item.ready,
          }"
          :to="item.ready || !item.requiresBirth ? item.path : '/profile'"
        >
          {{ item.label }}
        </RouterLink>
        <RouterLink
          v-if="!auth.isLoggedIn"
          class="nav-btn nav-btn--auth"
          :class="{ 'is-active': route.path === '/login' }"
          to="/login"
        >
          登录
        </RouterLink>
        <template v-else>
          <span class="nav-user">{{ auth.username || '已登录' }}</span>
          <button type="button" class="nav-btn nav-btn--auth" @click="handleLogout">登出</button>
        </template>
      </nav>
    </header>

    <main class="content">
      <slot />
    </main>

    <nav class="bottom-nav" aria-label="移动端导航">
      <RouterLink
        v-for="item in navItems"
        :key="`mobile-${item.path}`"
        class="bottom-nav__btn"
        :class="{
          'is-active': isNavItemActive(item),
          'is-locked': !item.ready,
        }"
        :to="item.ready || !item.requiresBirth ? item.path : '/profile'"
      >
        <span class="bottom-nav__label">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100dvh;
  background: var(--bg);
  color: var(--text);
  padding-bottom: 0;
}

.shell--home {
  background: var(--brand-paper);
}

.bar {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 56px;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-md);
  background: var(--hdr-bg);
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand-logo {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  display: block;
}

.title-block {
  min-width: 0;
}

.title-block h1 {
  margin: 0;
  font-size: 22px;
  line-height: 1.2;
  letter-spacing: 0.02em;
  color: var(--brand-ink);
  font-family: var(--font-display);
  font-weight: 600;
}

.eyebrow {
  margin: 0;
  font-size: 11px;
  letter-spacing: 0.1em;
  color: var(--brand-gold-dark);
  font-family: var(--font-display);
}

.eyebrow--home {
  font-size: 11px;
  letter-spacing: 0.22em;
  color: var(--brand-mist);
}

.subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--text-2);
  font-family: var(--font-cn);
}

.nav {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.nav-btn--auth {
  margin-left: 4px;
  border-color: rgba(184, 137, 77, 0.35);
}

.nav-user {
  font-size: 12px;
  color: var(--text-2);
  padding: 0 4px;
}

.backend-banner {
  margin: 0;
  padding: 10px 20px;
  background: var(--surface);
  border-bottom: 1px solid var(--brand-cinnabar);
  color: var(--brand-cinnabar);
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.backend-banner__dismiss {
  border: 1px solid var(--brand-cinnabar);
  background: var(--surface);
  color: var(--brand-cinnabar);
  border-radius: var(--radius-codex);
  padding: 4px 10px;
  cursor: pointer;
  font-size: 12px;
}

.nav-btn,
.bottom-nav__btn {
  min-height: 38px;
  padding: 0 14px;
  border-radius: var(--radius-codex);
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: border-color var(--dur-fast), background-color var(--dur-fast), color var(--dur-fast);
}

.nav-btn:hover,
.bottom-nav__btn:hover {
  border-color: var(--brand-gold);
  color: var(--brand-gold-dark);
}

.nav-btn.is-active,
.bottom-nav__btn.is-active {
  border-color: var(--brand-gold);
  background: var(--brand-gold-lt);
  color: var(--brand-gold-dark);
  font-weight: 600;
}

.nav-btn.is-locked,
.bottom-nav__btn.is-locked {
  opacity: 0.55;
}

.content {
  padding: var(--sp-6) 28px;
  max-width: var(--page-max-w);
  margin: 0 auto;
  width: 100%;
}

.shell--home .bar {
  border-bottom-color: var(--border);
  background: rgba(245, 240, 230, 0.92);
}

.shell--home .content {
  max-width: min(1180px, 100%);
  padding: 20px 20px 40px;
}

.shell--home .nav-btn {
  min-height: 36px;
  padding: 0 10px;
  border: none;
  background: transparent;
  border-radius: 0;
  font-family: var(--font-display);
  font-size: 13px;
  letter-spacing: 0.08em;
  color: var(--brand-mist);
}

.shell--home .nav-btn:hover {
  color: var(--brand-ink);
  background: transparent;
}

.shell--home .nav-btn.is-active {
  border: none;
  border-bottom: 2px solid var(--brand-gold);
  background: transparent;
  color: var(--brand-ink);
  font-weight: 600;
}

.shell--home .nav-btn--auth {
  border: 1px solid var(--border-md);
  border-radius: var(--radius-codex);
  padding: 0 12px;
}

.bottom-nav {
  display: none;
}

@media (max-width: 640px) {
  .bar {
    align-items: flex-start;
    flex-direction: column;
    padding: 12px;
  }

  .brand-logo {
    width: 40px;
    height: 40px;
  }

  .title-block h1 {
    font-size: 18px;
  }

  .subtitle {
    font-size: 11px;
  }

  .nav--desktop {
    display: none;
  }

  .content {
    padding: 12px 12px 76px;
  }

  .shell {
    padding-bottom: 64px;
  }

  .bottom-nav {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: var(--z-nav-mobile);
    gap: 4px;
    padding: 8px 8px calc(8px + env(safe-area-inset-bottom));
    border-top: 1px solid var(--border);
    background: rgba(255, 250, 245, 0.96);
    backdrop-filter: blur(8px);
  }

  .bottom-nav__btn {
    min-height: 44px;
    padding: 6px 4px;
    border-radius: 10px;
    display: grid;
    place-items: center;
  }

  .bottom-nav__label {
    font-size: 11px;
    font-weight: 600;
    font-family: var(--font-cn);
  }
}
</style>
