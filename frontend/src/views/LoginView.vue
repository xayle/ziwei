<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { formatAxiosError } from '@/utils/formatApiDetail'

const router = useRouter()
const route  = useRoute()
const auth   = useAuthStore()
const profile = useProfileStore()

/** AUTH-01：仅 DEV 预填；生产构建为空 */
const isDevPrefill = import.meta.env.DEV
const username = ref(isDevPrefill ? 'admin' : '')
const password = ref(isDevPrefill ? 'cad123qwe' : '')
const loading  = ref(false)
const error    = ref('')

async function doLogin() {
  loading.value = true
  error.value   = ''
  try {
    const res = await login(username.value, password.value)
    auth.setTokens(res.access_token, res.refresh_token, username.value)
    void profile.pullRemoteCases()
    const rawRedirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    const redirect = rawRedirect.startsWith('/') && !rawRedirect.startsWith('//') ? rawRedirect : '/'
    router.push(redirect)
  } catch (e: unknown) {
    error.value = formatAxiosError(e, '登录失败，请检查服务是否启动')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo / 标题 -->
      <div class="login-logo">
        <span class="logo-icon">☯</span>
        <h1 class="logo-title">浮生</h1>
        <p class="logo-sub">登录以使用完整功能</p>
        <p v-if="isDevPrefill" class="logo-dev-hint">开发模式已预填演示账号（生产构建不会预填）</p>
      </div>

      <!-- 表单 -->
      <div class="form-body">
        <p v-if="error" class="error-msg" role="alert" aria-live="assertive">{{ error }}</p>

        <div class="field">
          <label class="field-label" for="login-username">用户名</label>
          <input
            id="login-username"
            v-model="username"
            class="field-input"
            type="text"
            name="username"
            autocomplete="username"
            placeholder="请输入用户名"
            @keyup.enter="doLogin"
          />
        </div>

        <div class="field">
          <label class="field-label" for="login-password">密码</label>
          <input
            id="login-password"
            v-model="password"
            class="field-input"
            type="password"
            name="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            @keyup.enter="doLogin"
          />
        </div>

        <button
          class="btn-login"
          type="button"
          :disabled="loading"
          @click="doLogin"
        >
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </div>

      <p class="login-hint">会话令牌存储于浏览器，关闭页面不会自动注销。</p>
    </div>
  </div>
</template>

<style src="./LoginView.css" scoped />
