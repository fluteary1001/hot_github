export interface Project {
  id: number
  name: string
  full_name?: string
  html_url?: string
  description?: string
  stars: number
  forks: number
  language?: string
  topics: string[]
  clone_url?: string
  local_path?: string
  downloaded_at?: string
  is_manual: number
}

export interface SearchQuery {
  query: string
  limit: number
}

export interface DownloadRequest {
  clone_url: string
  project_name: string
}

export interface User {
  username: string
}

export interface LoginRequest {
  username: string
  password: string
}