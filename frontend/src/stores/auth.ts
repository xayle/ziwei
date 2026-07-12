import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { logout as apiLogout, refreshAccessToken } from '@/api/auth'

const REFRESH_KEY = 'refresh_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_KEY))
  const username = ref<string | null>(localStorage.getItem('username'))

  const isLoggedIn = computed(() => !!token.value)

  function setTokens(accessToken: string, nextRefreshToken?: string | null, user?: string) {
    token.value = accessToken
    localStorage.setItem('token', accessToken)
    if (nextRefreshToken) {
      refreshToken.value = nextRefreshToken
      localStorage.setItem(REFRESH_KEY, nextRefreshToken)
    }
    if (user) {
      username.value = user
      localStorage.setItem('username', user)
    }
  }

  /** @deprecated use setTokens */
  function setToken(newToken: string, user?: string) {
    setTokens(newToken, refreshToken.value, user)
  }

  async function tryRefreshToken(): Promise<boolean> {
    const current = refreshToken.value || localStorage.getItem(REFRESH_KEY)
    if (!current) return false
    try {
      const res = await refreshAccessToken(current)
      setTokens(res.access_token, res.refresh_token)
      return true
    } catch {
      return false
    }
  }

  async function logout() {
    const current = refreshToken.value || localStorage.getItem(REFRESH_KEY)
    if (current) {
      try {
        await apiLogout(current)
      } catch {
        // 客户端仍应丢弃本地令牌
      }
    }
    clearToken()
  }

  function clearToken() {
    token.value = null
    refreshToken.value = null
    username.value = null
    localStorage.removeItem('token')
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem('username')
  }

  return {
    token,
    refreshToken,
    username,
    isLoggedIn,
    setToken,
    setTokens,
    tryRefreshToken,
    logout,
    clearToken,
  }
})
