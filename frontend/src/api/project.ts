import api from './request'
import type { Project } from '@/types'

export const projectApi = {
  // 获取所有项目
  getAll: (keyword?: string) => {
    const params = keyword ? { keyword } : {}
    return api.get<Project[]>('/projects/', { params })
  },

  // 获取单个项目
  get: (id: number) => {
    return api.get<Project>(`/projects/${id}`)
  },

  // 删除项目
  delete: (id: number, deleteFiles: boolean = false) => {
    return api.delete(`/projects/${id}`, { params: { delete_files: deleteFiles } })
  },

  // 更新项目
  update: (id: number, data: Partial<Project>) => {
    return api.put<Project>(`/projects/${id}`, data)
  },

  // 更新项目代码
  updateCode: (id: number) => {
    return api.post(`/projects/${id}/update`)
  },

  // 导入项目
  import: (path: string, projectName?: string) => {
    return api.post<Project>('/projects/import', { path, project_name: projectName })
  }
}

export const docsApi = {
  // 启动 AI 文档生成
  generate: (projectId: number) => {
    return api.post<{ task_id: string; project_id: number; project_name: string }>(`/docs/generate/${projectId}`)
  },

  // 查询生成进度
  getStatus: (taskId: string) => {
    return api.get<{
      status: string
      progress: number
      message: string
      project_name: string
      docs: Record<string, string>
    }>(`/docs/status/${taskId}`)
  },

  // 获取项目文档列表
  getDocs: (projectId: number) => {
    return api.get<{ docs: Array<{ name: string; path: string; size: number; modified: number }> }>(`/docs/${projectId}`)
  },

  // 获取文档文件访问URL
  getDocUrl: (projectId: number, docName: string) => {
    // 对文件名进行 URL 编码，处理中文字符
    const encodedName = encodeURIComponent(docName)
    return `/api/docs/file/${projectId}/${encodedName}`
  }
}