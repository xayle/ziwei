<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/components/AppShell.vue'

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

  <!-- 其他页：三栏 AppShell 包裹 -->
  <AppShell v-else>
    <RouterView />
  </AppShell>
</template>
