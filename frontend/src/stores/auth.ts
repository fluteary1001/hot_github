import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const requireLogin = ref(true)

  const isAuthenticated = computed(() => !!token.value || !requireLogin.value)

  async function checkRequireLogin() {
    try {
      const res = await authApi.check()
      requireLogin.value = res.data.require_login
      if (!requireLogin.value && !token.value) {
        // 无需登录时自动获取 token
        const loginRes = await authApi.login({ username: 'admin', password: '' })
        token.value = loginRes.data.access_token
        username.value = 'anonymous'
        localStorage.setItem('token', loginRes.data.access_token)
        localStorage.setItem('username', 'anonymous')
      }
    } catch {
      requireLogin.value = true
    }
    return requireLogin.value
  }

  async function login(usernameInput: string, password: string) {
    try {
      const res = await authApi.login({ username: usernameInput, password })
      token.value = res.data.access_token
      username.value = usernameInput
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('username', usernameInput)
      ElMessage.success('登录成功')
      return true
    } catch {
      return false
    }
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  async function checkAuth() {
    if (!requireLogin.value) return true
    if (!token.value) return false
    try {
      await authApi.getMe()
      return true
    } catch {
      logout()
      return false
    }
  }

  return {
    token,
    username,
    requireLogin,
    isAuthenticated,
    login,
    logout,
    checkAuth,
    checkRequireLogin
  }
})
