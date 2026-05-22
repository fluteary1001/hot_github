<template>
  <div class="starred-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">
          <el-icon class="title-icon"><Star /></el-icon>
          高星项目
        </h2>
        <p class="page-desc">发现各领域最受欢迎的开源项目</p>
      </div>
      <div class="header-actions">
        <el-select v-model="category" placeholder="分类" class="category-select">
          <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
        </el-select>
        <el-button :icon="Refresh" @click="loadStarred" class="refresh-btn">刷新</el-button>
      </div>
    </div>

    <!-- Starred Grid -->
    <div class="starred-grid" v-loading="loading">
      <div
        v-for="(project, index) in starredList"
        :key="project.full_name"
        class="starred-card"
        :style="{ animationDelay: `${index * 50}ms` }"
      >
        <div class="card-rank">
          <span class="rank-number">{{ index + 1 }}</span>
        </div>

        <div class="card-content">
          <a :href="project.html_url" target="_blank" class="project-link">
            <span class="project-name">{{ project.full_name }}</span>
            <el-icon class="external-icon"><Link /></el-icon>
          </a>

          <p class="project-desc">{{ project.description || '暂无描述' }}</p>

          <div class="card-meta">
            <div class="meta-item">
              <el-icon class="meta-icon star"><Star /></el-icon>
              <span class="meta-value">{{ formatNumber(project.stars) }}</span>
            </div>
            <div class="meta-item" v-if="project.daily_stars">
              <el-icon class="meta-icon fire"><Sunny /></el-icon>
              <span class="meta-value hot">+{{ formatNumber(project.daily_stars) }}/天</span>
            </div>
            <div class="meta-item" v-if="project.language">
              <span class="language-dot" :style="{ background: getLanguageColor(project.language) }"></span>
              <span class="meta-value">{{ project.language }}</span>
            </div>
          </div>
        </div>

        <el-button
          type="primary"
          size="small"
          :loading="downloading === project.full_name"
          @click="handleDownload(project)"
          class="download-btn"
        >
          <el-icon v-if="!downloading"><Download /></el-icon>
          <span>{{ downloading === project.full_name ? '下载中' : '下载' }}</span>
        </el-button>
      </div>

      <el-empty v-if="!loading && starredList.length === 0" description="暂无高星项目数据" />
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
import { ref, onMounted, watch } from 'vue'
import { Star, Refresh, Sunny, Download, Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { trendingApi } from '@/api/trending'
import { searchApi } from '@/api/search'
import type { Project } from '@/types'

const category = ref('ALL')
const categories = ref<string[]>(['ALL', 'AI', '实用工具', '游戏&创意', '学习资源'])
const loading = ref(false)
const starredList = ref<Project[]>([])
const downloading = ref<string | null>(null)

const showProgress = ref(false)
const downloadingProject = ref('')
const downloadProgress = ref(0)
const downloadStatus = ref<'success' | 'exception' | undefined>()
const downloadLogs = ref<string[]>([])

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
  CSS: '#563d7c'
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

onMounted(() => {
  loadCategories()
  loadStarred()
})

watch(category, () => {
  loadStarred()
})

async function loadCategories() {
  try {
    const res = await trendingApi.getCategories()
    if (res.data.categories?.length) {
      categories.value = res.data.categories
    }
  } catch {
    // 使用默认分类
  }
}

async function loadStarred() {
  loading.value = true
  try {
    const res = await trendingApi.getStarred(category.value)
    starredList.value = res.data
  } finally {
    loading.value = false
  }
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
    ElMessage.error('下载任务启动失败')
  } finally {
    downloading.value = null
  }
}

async function pollDownloadStatus(taskId: string) {
  const poll = async () => {
    try {
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
    } catch {
      downloadStatus.value = 'exception'
      ElMessage.error('查询下载状态失败')
    }
  }

  await poll()
}

function closeProgress() {
  showProgress.value = false
}
</script>

<style scoped>
.starred-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  position: relative;
  z-index: 1;
}

/* ========================================
   Page Header
   ======================================== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.title-icon {
  color: var(--accent-amber);
}

.page-desc {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.category-select {
  width: 140px;
}

.refresh-btn {
  font-family: var(--font-display);
  font-weight: 500;
}

/* ========================================
   Starred Grid
   ======================================== */
.starred-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.starred-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
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

.starred-card:hover {
  border-color: rgba(0, 212, 255, 0.3);
  transform: translateY(-4px);
  box-shadow: var(--glass-shadow);
}

.card-rank {
  position: absolute;
  top: -8px;
  right: 16px;
  background: var(--gradient-amber);
  border-radius: var(--radius-full);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--glow-amber);
}

.rank-number {
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--bg-primary);
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.project-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--accent-cyan);
  text-decoration: none;
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1rem;
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
  margin: 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-icon {
  font-size: 14px;
}

.meta-icon.star {
  color: var(--accent-amber);
}

.meta-icon.fire {
  color: var(--accent-rose);
}

.meta-value {
  font-family: var(--font-display);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.meta-value.hot {
  color: var(--accent-rose);
  font-weight: 600;
}

.language-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.download-btn {
  width: 100%;
  font-family: var(--font-display);
  font-size: 0.85rem;
}

/* Responsive */
@media (max-width: 480px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    justify-content: space-between;
  }

  .starred-grid {
    grid-template-columns: 1fr;
  }
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
</style>
