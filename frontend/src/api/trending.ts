import api from './request'
import type { Project } from '@/types'

export const trendingApi = {
  // 获取官方Trending
  getOfficial: (since: string = 'daily', language: string = '') => {
    return api.get<Project[]>('/trending/official', {
      params: { since, language }
    })
  },

  // 获取高星项目
  getStarred: (category: string = 'ALL', pushedPeriod: string = '不限制') => {
    return api.get<Project[]>('/trending/stars', {
      params: { category, pushed_period: pushedPeriod }
    })
  },

  // 获取分类列表
  getCategories: () => {
    return api.get<{ categories: string[] }>('/trending/categories')
  }
}