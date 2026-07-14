<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppLoading from '@/components/AppLoading.vue'
import NewAppShell from '@/components/new/NewAppShell.vue'
import { useAuthStore } from '@/stores/auth'
import { useEntitlementStore } from '@/stores/entitlement'

const router = useRouter()
const route  = useRoute()
const auth = useAuthStore()
const entitlement = useEntitlementStore()

const isBareRoute = computed(
  () => route.name === 'login' || route.name === 'landing' || route.name === 'payment-callback',
)

function handleUnauthorized() {
  auth.clearToken()
  entitlement.reset()
  const redirect = router.currentRoute.value.fullPath
  const safeRedirect = redirect.startsWith('/') && !redirect.startsWith('//') && !redirect.startsWith('/login')
    ? redirect
    : '/'
  router.replace({ name: 'login', query: { redirect: safeRedirect } })
}

function handleTokensRefreshed(ev: Event) {
  const detail = (ev as CustomEvent<{ access_token?: string; refresh_token?: string }>).detail
  if (detail?.access_token) {
    auth.setTokens(detail.access_token, detail.refresh_token ?? null)
  }
}

onMounted(() => {
  window.addEventListener('app:unauthorized', handleUnauthorized)
  window.addEventListener('app:tokens-refreshed', handleTokensRefreshed as EventListener)
})
onUnmounted(() => {
  window.removeEventListener('app:unauthorized', handleUnauthorized)
  window.removeEventListener('app:tokens-refreshed', handleTokensRefreshed as EventListener)
})
</script>

<template>
  <!-- 登录 / 抖音落地：裸渲染，无三栏壳 -->
  <RouterView v-if="isBareRoute" />

  <!-- 其他页面：统一使用新壳 -->
  <NewAppShell v-else>
    <Suspense>
      <template #default>
        <RouterView />
      </template>
      <template #fallback>
        <AppLoading />
      </template>
    </Suspense>
  </NewAppShell>
</template>
