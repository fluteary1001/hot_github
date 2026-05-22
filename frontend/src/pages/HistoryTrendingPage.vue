<template>
  <div class="history-trending-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">
          <el-icon class="title-icon"><Clock /></el-icon>
          历史官方热点
        </h2>
        <p class="page-desc">查看历史采集的 GitHub 热点数据</p>
      </div>
      <div class="header-actions">
        <el-select v-model="collectType" placeholder="采集类型" class="collect-select">
          <el-option label="今日热点" value="daily" />
          <el-option label="本周热点" value="weekly" />
          <el-option label="本月热点" value="monthly" />
        </el-select>
        <el-button type="primary" :loading="collecting" @click="handleCollect">
          <el-icon><Download /></el-icon>
          手动采集
        </el-button>
        <el-button :icon="Refresh" @click="loadTree">刷新</el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧树形导航 -->
      <div class="tree-panel">
        <div class="panel-header">
          <el-icon><FolderOpened /></el-icon>
          <span>历史记录</span>
        </div>
        <el-scrollbar class="tree-scrollbar">
          <el-tree
            ref="treeRef"
            :data="treeData"
            :props="treeProps"
            node-key="value"
            highlight-current
            :expand-on-click-node="false"
            @node-click="handleNodeClick"
            v-loading="treeLoading"
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <el-icon v-if="data.type === 'year'" class="node-icon year"><Calendar /></el-icon>
                <el-icon v-else-if="data.type === 'month'" class="node-icon month"><Calendar /></el-icon>
                <el-icon v-else-if="data.type === 'week'" class="node-icon week"><Timer /></el-icon>
                <el-icon v-else class="node-icon day"><Document /></el-icon>
                <span class="node-label">{{ data.label }}</span>
                <el-badge v-if="data.count" :value="data.count" class="node-badge" />
              </span>
            </template>
          </el-tree>
          <el-empty v-if="!treeLoading && treeData.length === 0" description="暂无历史数据" />
        </el-scrollbar>
      </div>

      <!-- 右侧详情面板 -->
      <div class="detail-panel">
        <div v-if="selectedNode" class="detail-header">
          <h3 class="detail-title">{{ selectedNode.label }} 热点详情</h3>
          <span v-if="detailData.collected_at" class="collected-time">
            采集时间: {{ detailData.collected_at }}
          </span>
        </div>

        <div v-if="selectedNode" class="project-list" v-loading="detailLoading">
          <div
            v-for="project in detailData.projects"
            :key="project.full_name"
            class="project-card"
          >
            <div class="project-rank" :class="getRankClass(project.rank)">
              #{{ project.rank }}
            </div>
            <div class="project-info">
              <a :href="project.html_url" target="_blank" class="project-name">
                {{ project.full_name }}
                <el-icon class="external-icon"><Link /></el-icon>
              </a>
              <p class="project-desc">{{ project.description || '暂无描述' }}</p>
              <div class="project-meta">
                <span class="meta-item">
                  <el-icon class="meta-icon star"><StarFilled /></el-icon>
                  {{ formatNumber(project.stars) }}
                </span>
                <span v-if="project.stars_change" class="meta-item hot">
                  <el-icon class="meta-icon fire"><Sunny /></el-icon>
                  +{{ formatNumber(project.stars_change) }}
                </span>
                <span v-if="project.language" class="meta-item">
                  <span class="language-dot" :style="{ background: getLanguageColor(project.language) }"></span>
                  {{ project.language }}
                </span>
              </div>
            </div>
            <div class="project-actions">
              <el-tag v-if="project.downloaded" type="success" size="small">
                <el-icon><Check /></el-icon> 已下载
              </el-tag>
              <el-tag v-else type="info" size="small">未下载</el-tag>

              <div v-if="project.reports" class="report-links">
                <el-link
                  v-if="project.reports.design_html"
                  :href="getFileUrl(project.project_id, project.reports.design_html)"
                  target="_blank"
                  type="primary"
                  :underline="false"
                >
                  设计说明书
                </el-link>
                <el-link
                  v-if="project.reports.usage_html"
                  :href="getFileUrl(project.project_id, project.reports.usage_html)"
                  target="_blank"
                  type="primary"
                  :underline="false"
                >
                  使用说明书
                </el-link>
                <el-link
                  v-if="project.reports.value_html"
                  :href="getFileUrl(project.project_id, project.reports.value_html)"
                  target="_blank"
                  type="primary"
                  :underline="false"
                >
                  价值分析
                </el-link>
              </div>
            </div>
          </div>

          <el-empty v-if="detailData.projects.length === 0" description="该周期暂无热点数据" />
        </div>

        <el-empty v-else description="请从左侧选择一个日期查看热点详情" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  Clock, Download, Refresh, FolderOpened, Calendar, Timer,
  Document, Link, StarFilled, Sunny, Check
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { historyApi } from '@/api/history'

interface TreeNode {
  label: string
  value: string
  type: string
  count?: number
  collected_at?: string
  children?: TreeNode[]
}

interface Project {
  rank: number
  name: string
  full_name: string
  html_url: string
  description: string
  stars: number
  stars_change: number
  language: string
  downloaded: boolean
  project_id: number
  history_id: number
  reports?: {
    design_html: string
    usage_html: string
    value_html: string
  }
}

const treeRef = ref()
const treeData = ref<TreeNode[]>([])
const treeProps = {
  children: 'children',
  label: 'label'
}
const treeLoading = ref(false)
const selectedNode = ref<TreeNode | null>(null)
const detailLoading = ref(false)
const detailData = ref<{
  period_type: string
  period_value: string
  collected_at: string | null
  projects: Project[]
}>({
  period_type: '',
  period_value: '',
  collected_at: null,
  projects: []
})

const collectType = ref('daily')
const collecting = ref(false)

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

function getRankClass(rank: number): string {
  if (rank <= 3) return 'top-rank'
  if (rank <= 10) return 'high-rank'
  return ''
}

function getFileUrl(projectId: number, path: string): string {
  if (!path || projectId <= 0) return '#'
  // 转换本地路径为 API 路径 - 支持正斜杠和反斜杠
  // 先尝试反斜杠分割（Windows路径），再尝试正斜杠分割（Unix路径）
  let fileName = ''
  if (path.includes('\\')) {
    fileName = path.split('\\').pop() || ''
  } else if (path.includes('/')) {
    fileName = path.split('/').pop() || ''
  } else {
    fileName = path // 如果没有分隔符，整个字符串就是文件名
  }

  if (!fileName) return '#'

  // 对文件名进行 URL 编码，确保中文字符正确传递
  const encodedFileName = encodeURIComponent(fileName)
  return `/api/docs/file/${projectId}/${encodedFileName}`
}

onMounted(() => {
  loadTree()
})

async function loadTree() {
  treeLoading.value = true
  try {
    const res = await historyApi.getTree()
    treeData.value = res.data.data || []
  } catch (error) {
    console.error('加载树数据失败:', error)
  } finally {
    treeLoading.value = false
  }
}

async function handleNodeClick(data: TreeNode) {
  if (data.type !== 'day') return

  selectedNode.value = data
  detailLoading.value = true

  try {
    const periodType = 'daily'
    const res = await historyApi.getDetail(periodType, data.value)
    detailData.value = res.data
  } catch (error) {
    console.error('加载详情失败:', error)
    ElMessage.error('加载热点详情失败')
  } finally {
    detailLoading.value = false
  }
}

async function handleCollect() {
  collecting.value = true
  try {
    const res = await historyApi.manualCollect(collectType.value)
    ElMessage.success(`采集成功，保存了 ${res.data.saved_count} 个项目`)
    // 刷新树数据
    await loadTree()
  } catch (error) {
    console.error('采集失败:', error)
    ElMessage.error('采集失败')
  } finally {
    collecting.value = false
  }
}
</script>

<style scoped>
.history-trending-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
  position: relative;
  z-index: 1;
}

/* 页面头部 */
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
  color: var(--accent-cyan);
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

.collect-select {
  width: 120px;
}

/* 主内容区 */
.main-content {
  display: flex;
  gap: 24px;
  flex: 1;
  min-height: 0;
}

/* 树形面板 */
.tree-panel {
  width: 320px;
  flex-shrink: 0;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border-bottom: 1px solid var(--glass-border);
  color: var(--text-primary);
  font-weight: 600;
}

.tree-scrollbar {
  flex: 1;
  padding: 12px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.node-icon {
  font-size: 16px;
}

.node-icon.year {
  color: var(--accent-purple);
}

.node-icon.month {
  color: var(--accent-cyan);
}

.node-icon.week {
  color: var(--accent-amber);
}

.node-icon.day {
  color: var(--text-muted);
}

.node-label {
  flex: 1;
}

.node-badge {
  margin-left: 8px;
}

/* 详情面板 */
.detail-panel {
  flex: 1;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--glass-border);
}

.detail-title {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.collected-time {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.project-list {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.project-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}

.project-card:hover {
  background: rgba(30, 41, 59, 0.8);
}

.project-rank {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.project-rank.top-rank {
  background: var(--gradient-amber);
  color: var(--bg-primary);
}

.project-rank.high-rank {
  background: var(--gradient-cyan);
  color: var(--bg-primary);
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-name {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--accent-cyan);
  text-decoration: none;
  font-weight: 600;
  transition: color var(--transition-fast);
}

.project-name:hover {
  color: var(--text-primary);
}

.external-icon {
  font-size: 12px;
  opacity: 0.6;
}

.project-desc {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin: 8px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.meta-item.hot {
  color: var(--accent-rose);
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

.language-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.project-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.report-links {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 响应式 */
@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }

  .tree-panel {
    width: 100%;
    max-height: 300px;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
