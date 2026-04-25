<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route  = useRoute()
const auth   = useAuthStore()

const username = ref('admin')
const password = ref('cad123qwe')
const loading  = ref(false)
const error    = ref('')

async function doLogin() {
  loading.value = true
  error.value   = ''
  try {
    const res = await login(username.value, password.value)
    auth.setToken(res.access_token, username.value)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (e: unknown) {
    error.value = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '登录失败，请检查服务是否启动'
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
        <h1 class="logo-title">命理系统</h1>
        <p class="logo-sub">登录以使用完整功能</p>
      </div>

      <!-- 表单 -->
      <div class="form-body">
        <p v-if="error" class="error-msg">{{ error }}</p>

        <div class="field">
          <label class="field-label">用户名</label>
          <input
            v-model="username"
            class="field-input"
            type="text"
            placeholder="请输入用户名"
            @keyup.enter="doLogin"
          />
        </div>

        <div class="field">
          <label class="field-label">密码</label>
          <input
            v-model="password"
            class="field-input"
            type="password"
            placeholder="请输入密码"
            @keyup.enter="doLogin"
          />
        </div>

        <button
          class="btn-login"
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

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-6) var(--sp-4);
  background: var(--bg);
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--sp-8) var(--sp-7);
  box-shadow: var(--shadow);
}

/* Logo区 */
.login-logo {
  text-align: center;
  margin-bottom: var(--sp-7);
}

.logo-icon {
  display: block;
  font-size: 48px;
  line-height: 1;
  margin-bottom: var(--sp-3);
}

.logo-title {
  font-size: var(--fs-2xl);
  font-weight: 700;
  color: var(--text);
  margin: 0 0 var(--sp-1);
  font-family: var(--font-cn);
}

.logo-sub {
  font-size: var(--fs-sm);
  color: var(--text-3);
  margin: 0;
}

/* 字段 */
.form-body {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.field-label {
  font-size: var(--fs-sm);
  color: var(--text-2);
  font-weight: 500;
}

.field-input {
  padding: 9px var(--sp-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  font-size: var(--fs-md);
  outline: none;
  transition: border-color var(--dur-fast);
}

.field-input:focus {
  border-color: var(--accent);
}

.error-msg {
  color: var(--danger-dark);
  font-size: var(--fs-sm);
  margin: 0;
  padding: var(--sp-2) var(--sp-3);
  background: rgba(220, 38, 38, .08);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--danger-dark);
}

.btn-login {
  padding: 11px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--fs-md);
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 0.05em;
  transition: background var(--dur-fast), transform var(--dur-fast);
}

.btn-login:hover:not(:disabled) {
  background: var(--accent-dark);
  transform: translateY(-1px);
}

.btn-login:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.login-hint {
  margin: var(--sp-5) 0 0;
  font-size: var(--fs-xs);
  color: var(--text-3);
  text-align: center;
}
</style>
