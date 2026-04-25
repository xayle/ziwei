import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const username = ref<string | null>(localStorage.getItem('username'))

  const isLoggedIn = computed(() => !!token.value)

  function setToken(newToken: string, user?: string) {
    token.value = newToken
    localStorage.setItem('token', newToken)
    if (user) {
      username.value = user
      localStorage.setItem('username', user)
    }
  }

  function clearToken() {
    token.value = null
    username.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  return { token, username, isLoggedIn, setToken, clearToken }
})
