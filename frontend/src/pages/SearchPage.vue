<template>
  <div class="search-page">
    <!-- Search Bar -->
    <div class="search-header">
      <div class="search-input-wrapper">
        <el-input
          v-model="searchQuery"
          placeholder="搜索 GitHub 项目..."
          size="large"
          clearable
          @keyup.enter="handleSearch"
          class="search-input"
        >
          <template #prefix>
            <el-icon class="search-icon"><Search /></el-icon>
          </template>
          <template #append>
            <el-button :icon="Search" :loading="searching" @click="handleSearch" class="search-btn">
              搜索
            </el-button>
          </template>
        </el-input>
      </div>
      <div class="search-hints">
        <span class="hint">提示：输入项目名或粘贴 GitHub URL</span>
      </div>
    </div>

    <!-- Results Grid -->
    <div class="results-container">
      <!-- Left: Results List -->
      <div class="results-panel">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon><FolderOpened /></el-icon>
            <span>搜索结果</span>
            <span class="result-count">{{ searchResults.length }}</span>
          </div>
        </div>

        <div class="results-list" v-loading="searching">
          <div
            v-for="(project, index) in searchResults"
            :key="project.full_name"
            class="result-card"
            :class="{ selected: selectedProject?.full_name === project.full_name }"
            @click="handleSelectProject(project)"
            :style="{ animationDelay: `${index * 50}ms` }"
          >
            <div class="card-header">
              <a :href="project.html_url" target="_blank" class="project-link" @click.stop>
                <span class="project-name">{{ project.full_name }}</span>
                <el-icon class="external-icon"><Link /></el-icon>
              </a>
            </div>
            <p class="project-desc">{{ project.description || '暂无描述' }}</p>
            <div class="card-footer">
              <div class="stat-item">
                <el-icon class="stat-icon star"><Star /></el-icon>
                <span class="stat-value">{{ formatNumber(project.stars) }}</span>
              </div>
              <div class="stat-item" v-if="project.language">
                <span class="language-dot" :style="{ background: getLanguageColor(project.language) }"></span>
                <span class="stat-value">{{ project.language }}</span>
              </div>
              <el-button
                type="primary"
                size="small"
                :loading="downloading === project.full_name"
                @click.stop="handleDownload(project)"
                class="download-btn"
              >
                <el-icon v-if="!downloading"><Download /></el-icon>
                <span>{{ downloading === project.full_name ? '下载中' : '下载' }}</span>
              </el-button>
            </div>
          </div>

          <el-empty v-if="!searching && searchResults.length === 0" description="开始搜索探索开源项目" />
        </div>
      </div>

      <!-- Right: Project Detail -->
      <div class="detail-panel">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon><InfoFilled /></el-icon>
            <span>项目详情</span>
          </div>
        </div>

        <div class="detail-content" v-if="selectedProject">
          <div class="detail-header">
            <h3 class="detail-title">{{ selectedProject.full_name }}</h3>
            <p class="detail-desc">{{ selectedProject.description || '暂无描述' }}</p>
          </div>

          <div class="detail-stats">
            <div class="stat-card">
              <el-icon class="stat-icon-large star"><Star /></el-icon>
              <div class="stat-info">
                <span class="stat-number">{{ formatNumber(selectedProject.stars) }}</span>
                <span class="stat-label">Stars</span>
              </div>
            </div>
            <div class="stat-card">
              <el-icon class="stat-icon-large"><Share /></el-icon>
              <div class="stat-info">
                <span class="stat-number">{{ formatNumber(selectedProject.forks) }}</span>
                <span class="stat-label">Forks</span>
              </div>
            </div>
          </div>

          <div class="detail-info">
            <div class="info-row">
              <span class="info-label">语言</span>
              <span class="info-value">
                <span class="language-dot" :style="{ background: getLanguageColor(selectedProject.language) }"></span>
                {{ selectedProject.language || '未知' }}
              </span>
            </div>
            <div class="info-row">
              <span class="info-label">创建时间</span>
              <span class="info-value">{{ formatDate(selectedProject.created_at) }}</span>
            </div>
          </div>

          <div class="topics-wrapper" v-if="selectedProject.topics?.length">
            <span class="topic-label">标签</span>
            <div class="topics-list">
              <span v-for="topic in selectedProject.topics.slice(0, 6)" :key="topic" class="topic-tag">
                {{ topic }}
              </span>
            </div>
          </div>

          <el-button
            type="primary"
            size="large"
            :loading="downloading === selectedProject.full_name"
            @click="handleDownload(selectedProject)"
            class="detail-download-btn"
          >
            <el-icon v-if="!downloading"><Download /></el-icon>
            <span>{{ downloading === selectedProject.full_name ? '正在下载...' : '下载项目' }}</span>
          </el-button>
        </div>

        <el-empty v-else description="选择一个项目查看详情" />
      </div>
    </div>

    <!-- Download Progress Dialog -->
    <el-dialog v-model="showProgress" title="下载进度" width="500px" class="progress-dialog">
      <div class="progress-content">
        <div class="progress-header">
          <span class="progress-project">{{ downloadingProject }}</span>
        </div>
        <el-progress :percentage="downloadProgress" :status="downloadStatus" :stroke-width="8" />
        <div class="progress-logs">
          <el-scrollbar height="150px">
            <div v-for="(log, index) in downloadLogs" :key="index" class="log-item">
              {{ log }}
            </div>
          </el-scrollbar>
        </div>
      </div>
      <template #footer>
        <el-button v-if="downloadStatus === 'success'" type="primary" @click="closeProgress">
          完成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Search, Star, Share, Download, FolderOpened, InfoFilled, Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { searchApi } from '@/api/search'
import type { Project } from '@/types'

const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref<Project[]>([])
const selectedProject = ref<Project | null>(null)
const downloading = ref<string | null>(null)

const showProgress = ref(false)
const downloadingProject = ref('')
const downloadProgress = ref(0)
const downloadStatus = ref<'success' | 'exception' | undefined>()
const downloadLogs = ref<string[]>([])

// Language colors
const languageColors: Record<string, string> = {
  JavaScript: '#f7df1e',
  TypeScript: '#3178c6',
  Python: '#3776ab',
  Java: '#b07219',
  Go: '#00add8',
  Rust: '#dea584',
  C: '#555555',
  'C++': '#f34b7d',
  Ruby: '#701516',
  PHP: '#4f5d95',
  Swift: '#fa734d',
  Kotlin: '#a97bff',
  Shell: '#89e051',
  Vue: '#42b883',
  HTML: '#e34c26',
  CSS: '#563d7c',
  SCSS: '#c6538c',
  Less: '#1d365d'
}

function getLanguageColor(lang: string): string {
  return languageColors[lang] || '#8b949e'
}

function formatNumber(num: number): string {
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return String(num)
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '未知'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

async function handleSearch() {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  searching.value = true
  selectedProject.value = null

  try {
    if (searchQuery.value.includes('github.com')) {
      const res = await searchApi.searchByUrl(searchQuery.value)
      searchResults.value = res.data ? [res.data] : []
    } else {
      const res = await searchApi.search({ query: searchQuery.value, limit: 10 })
      searchResults.value = res.data
    }
  } finally {
    searching.value = false
  }
}

function handleSelectProject(project: Project | null) {
  selectedProject.value = project
}

async function handleDownload(project: Project) {
  if (!project.clone_url) {
    ElMessage.error('无法获取克隆URL')
    return
  }

  downloading.value = project.full_name
  downloadingProject.value = project.name
  downloadProgress.value = 0
  downloadStatus.value = undefined
  downloadLogs.value = []
  showProgress.value = true

  try {
    const res = await searchApi.download({
      clone_url: project.clone_url,
      project_name: project.name
    })
    await pollDownloadStatus(res.data.task_id)
  } catch {
    downloadStatus.value = 'exception'
  } finally {
    downloading.value = null
  }
}

async function pollDownloadStatus(taskId: string) {
  const poll = async () => {
    const res = await searchApi.getDownloadStatus(taskId)
    const status = res.data

    downloadLogs.value.push(status.message)

    if (status.status === 'completed') {
      downloadProgress.value = 100
      downloadStatus.value = 'success'
      ElMessage.success('下载完成')
    } else if (status.status === 'failed') {
      downloadStatus.value = 'exception'
      ElMessage.error(status.message)
    } else {
      downloadProgress.value = status.progress || 50
      setTimeout(poll, 1000)
    }
  }

  await poll()
}

function closeProgress() {
  showProgress.value = false
}
</script>

<style scoped>
.search-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: relative;
  z-index: 1;
}

/* ========================================
   Search Header
   ======================================== */
.search-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-input-wrapper {
  position: relative;
}

.search-input :deep(.el-input__wrapper) {
  background: var(--bg-secondary);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 4px 16px;
  box-shadow: none;
  transition: all var(--transition-base);
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 212, 255, 0.5);
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--accent-cyan);
  box-shadow: var(--glow-cyan-sm);
}

.search-input :deep(.el-input__inner) {
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 1rem;
}

.search-input :deep(.el-input__inner::placeholder) {
  color: var(--text-muted);
}

.search-icon {
  color: var(--text-muted);
  font-size: 18px;
}

.search-input :deep(.el-input-group__append) {
  background: transparent;
  border: none;
  padding: 0;
}

.search-btn {
  background: var(--gradient-cyan);
  border: none;
  border-radius: var(--radius-md);
  color: var(--bg-primary);
  font-family: var(--font-display);
  font-weight: 600;
  padding: 8px 20px;
}

.search-btn:hover {
  box-shadow: var(--glow-cyan-sm);
}

.search-hints {
  padding-left: 4px;
}

.hint {
  font-family: var(--font-display);
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ========================================
   Results Container
   ======================================== */
.results-container {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 20px;
  min-height: 0;
}

.results-panel,
.detail-panel {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--glass-border);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-display);
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.result-count {
  background: rgba(0, 212, 255, 0.15);
  color: var(--accent-cyan);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
}

/* ========================================
   Results List
   ======================================== */
.results-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-card {
  background: var(--bg-tertiary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  padding: 16px;
  cursor: pointer;
  transition: all var(--transition-base);
  animation: fadeInUp 0.4s ease forwards;
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-card:hover {
  border-color: rgba(0, 212, 255, 0.3);
  background: var(--bg-elevated);
}

.result-card.selected {
  border-color: var(--accent-cyan);
  background: rgba(0, 212, 255, 0.08);
}

.card-header {
  margin-bottom: 8px;
}

.project-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--accent-cyan);
  text-decoration: none;
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 0.95rem;
  transition: color var(--transition-fast);
}

.project-link:hover {
  color: var(--text-primary);
}

.external-icon {
  font-size: 12px;
  opacity: 0.6;
}

.project-desc {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin: 0 0 12px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-icon {
  font-size: 14px;
}

.stat-icon.star {
  color: var(--accent-amber);
}

.stat-value {
  font-family: var(--font-display);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.language-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.download-btn {
  margin-left: auto;
  font-family: var(--font-display);
  font-size: 0.75rem;
}

/* ========================================
   Detail Panel
   ======================================== */
.detail-content {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

.detail-header {
  text-align: center;
}

.detail-title {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.detail-desc {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin: 0;
  line-height: 1.5;
}

.detail-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-card {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon-large {
  font-size: 24px;
  color: var(--accent-cyan);
}

.stat-icon-large.star {
  color: var(--accent-amber);
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

.info-label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.info-value {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-display);
  font-size: 0.85rem;
  color: var(--text-primary);
}

.topics-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.topic-label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.topics-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.topic-tag {
  background: rgba(0, 212, 255, 0.1);
  color: var(--accent-cyan);
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-family: var(--font-display);
  font-size: 0.7rem;
}

.detail-download-btn {
  width: 100%;
  height: 48px;
  font-family: var(--font-display);
  font-size: 1rem;
  margin-top: auto;
}

/* ========================================
   Progress Dialog
   ======================================== */
.progress-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

.progress-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-header {
  text-align: center;
}

.progress-project {
  font-family: var(--font-display);
  font-weight: 600;
  color: var(--text-primary);
}

.progress-logs {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 12px;
}

.log-item {
  font-family: var(--font-display);
  font-size: 0.75rem;
  color: var(--text-muted);
  padding: 4px 0;
}

/* ========================================
   Responsive
   ======================================== */
@media (max-width: 1024px) {
  .results-container {
    grid-template-columns: 1fr;
  }

  .detail-panel {
    display: none;
  }
}
</style>
