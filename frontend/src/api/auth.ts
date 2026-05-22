import api from './request'
import type { User, LoginRequest } from '@/types'

export const authApi = {
  // 检查是否需要登录
  check: () => {
    return api.get<{ require_login: boolean }>('/auth/check')
  },

  // 登录
  login: (data: LoginRequest) => {
    return api.post<{ access_token: string }>('/auth/login', data)
  },

  // 登出
  logout: () => {
    return api.post('/auth/logout')
  },

  // 获取当前用户
  getMe: () => {
    return api.get<User>('/auth/me')
  }
}