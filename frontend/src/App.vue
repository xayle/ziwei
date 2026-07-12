<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppLoading from '@/components/AppLoading.vue'
import NewAppShell from '@/components/new/NewAppShell.vue'

const router = useRouter()
const route  = useRoute()

const isLoginRoute = computed(() => route.name === 'login')

function handleUnauthorized() {
  const redirect = router.currentRoute.value.fullPath
  router.replace({ name: 'login', query: { redirect } })
}

onMounted(() => {
  window.addEventListener('app:unauthorized', handleUnauthorized)
})
onUnmounted(() => {
  window.removeEventListener('app:unauthorized', handleUnauthorized)
})
</script>

<template>
  <!-- 登录页：裸渲染，无三栏壳 -->
  <RouterView v-if="isLoginRoute" />

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
