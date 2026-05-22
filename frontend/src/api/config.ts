import api from './request'

export interface AppConfig {
  app_name: string
  version: string
  download_path: string
  github_token: string
  claude_api_key: string
  claude_model: string
  claude_base_url: string
  require_login: boolean
}

export const configApi = {
  getConfig: () => {
    return api.get<AppConfig>('/config')
  },

  testGithub: () => {
    return api.post<{ success: boolean; message: string }>('/config/test-github')
  }
}
