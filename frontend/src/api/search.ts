import api from './request'
import type { Project, SearchQuery, DownloadRequest } from '@/types'

export const searchApi = {
  // 搜索GitHub项目
  search: (query: SearchQuery) => {
    return api.post<Project[]>('/search/', query)
  },

  // 通过URL获取项目
  searchByUrl: (url: string) => {
    return api.post<Project>('/search/url', { url })
  },

  // 启动下载
  download: (data: DownloadRequest) => {
    return api.post<{ task_id: string; project_name: string }>('/search/download', data)
  },

  // 获取下载状态
  getDownloadStatus: (taskId: string) => {
    return api.get(`/search/download/${taskId}`)
  },

  // 测试连接
  testConnection: () => {
    return api.get<{ success: boolean; message: string }>('/search/test-connection')
  }
}