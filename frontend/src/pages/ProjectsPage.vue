<template>
  <div class="projects-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">
          <el-icon class="title-icon"><FolderOpened /></el-icon>
          项目管理
        </h2>
        <p class="page-desc">管理已下载的 GitHub 项目</p>
      </div>
      <div class="header-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索项目..."
          clearable
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button :icon="Refresh" @click="loadProjects" class="refresh-btn">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="showImportDialog = true" class="import-btn">
          导入项目
        </el-button>
      </div>
    </div>

    <!-- Projects Grid -->
    <div class="projects-grid" v-loading="loading">
      <div
        v-for="(project, index) in filteredProjects"
        :key="project.id"
        class="project-card"
        :style="{ animationDelay: `${index * 50}ms` }"
      >
        <div class="card-header">
          <div class="project-info">
            <a v-if="project.html_url" :href="project.html_url" target="_blank" class="project-link">
              <span class="project-name">{{ project.name }}</span>
              <el-icon class="external-icon"><Link /></el-icon>
            </a>
            <span v-else class="project-name">{{ project.name }}</span>
          </div>
          <div class="project-stats" v-if="project.stars">
            <el-icon class="stat-icon"><Star /></el-icon>
            <span class="stat-value">{{ formatNumber(project.stars) }}</span>
          </div>
        </div>

        <p class="project-desc">{{ project.description || '暂无描述' }}</p>

        <div class="card-meta">
          <div class="meta-item" v-if="project.language">
            <span class="language-dot" :style="{ background: getLanguageColor(project.language) }"></span>
            <span class="meta-value">{{ project.language }}</span>
          </div>
          <div class="meta-item" v-if="project.downloaded_at">
            <el-icon class="meta-icon"><Clock /></el-icon>
            <span class="meta-value">{{ formatDate(project.downloaded_at) }}</span>
          </div>
        </div>

        <div class="card-actions">
          <el-button size="small" @click="openFolder(project)" class="action-btn">
            <el-icon><FolderOpened /></el-icon>
            <span>打开</span>
          </el-button>
          <el-button size="small" type="primary" @click="startAnalysis(project)" :loading="analyzing === project.id" class="action-btn ai-btn">
            <el-icon v-if="analyzing !== project.id"><MagicStick /></el-icon>
            <span>{{ analyzing === project.id ? '分析中' : 'AI分析' }}</span>
          </el-button>
          <el-button size="small" @click="updateProject(project)" :loading="updating === project.id" class="action-btn">
            <el-icon v-if="!updating"><Refresh /></el-icon>
            <span>{{ updating === project.id ? '更新中' : '更新' }}</span>
          </el-button>
          <el-popconfirm title="确定删除此项目？" @confirm="deleteProject(project)" confirm-button-text="删除" cancel-button-text="取消">
            <template #reference>
              <el-button size="small" type="danger" class="action-btn danger">
                <el-icon><Delete /></el-icon>
                <span>删除</span>
              </el-button>
            </template>
          </el-popconfirm>
        </div>

        <!-- 文档快捷链接 -->
        <div class="doc-links" v-if="getLatestHtmlDocs(project.id).length">
          <el-button
            v-for="doc in getLatestHtmlDocs(project.id)"
            :key="doc.name"
            size="small"
            text
            class="doc-link-btn"
            @click="openDoc(project.id, doc.name)"
          >
            <el-icon><Document /></el-icon>
            <span>{{ doc.label }}</span>
          </el-button>
        </div>
      </div>

      <el-empty v-if="!loading && filteredProjects.length === 0" description="暂无项目，请先下载或导入" />
    </div>

    <!-- Import Dialog -->
    <el-dialog v-model="showImportDialog" title="导入项目" width="500px" class="import-dialog">
      <el-form :model="importForm" label-position="top" class="import-form">
        <el-form-item label="项目路径">
          <el-input v-model="importForm.path" placeholder="输入本地项目路径">
            <template #prefix>
              <el-icon><FolderOpened /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="项目名称">
          <el-input v-model="importForm.name" placeholder="可选，默认使用目录名">
            <template #prefix>
              <el-icon><Edit /></el-icon>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImport">导入</el-button>
      </template>
    </el-dialog>

    <!-- AI Analysis Progress Dialog -->
    <el-dialog v-model="showAnalysisDialog" title="AI 文档分析" width="520px" class="analysis-dialog" :close-on-click-modal="false" :close-on-press-escape="false">
      <div class="analysis-content" v-if="docsTask.taskId">
        <div class="analysis-header">
          <el-icon class="analysis-icon" :class="docsTask.status"><MagicStick /></el-icon>
          <span class="analysis-project">{{ docsTask.projectName }}</span>
        </div>

        <el-progress
          :percentage="docsTask.progress"
          :status="docsTask.status === 'failed' ? 'exception' : docsTask.status === 'completed' ? 'success' : undefined"
          :stroke-width="10"
          class="analysis-progress"
        />

        <p class="analysis-message">{{ docsTask.message }}</p>

        <div class="analysis-docs" v-if="docsTask.docs">
          <div
            v-for="(docStatus, docKey) in docsTask.docs"
            :key="docKey"
            class="doc-item"
            :class="{ 'doc-done': docStatus === '已生成' || docStatus === '已存在', 'doc-fail': docStatus === '失败' }"
          >
            <el-icon class="doc-icon">
              <CircleCheck v-if="docStatus === '已生成' || docStatus === '已存在'" />
              <CircleClose v-else-if="docStatus === '失败'" />
              <Loading v-else-if="docStatus.includes('生成中')" />
              <Clock v-else />
            </el-icon>
            <span class="doc-name">{{ getDocLabel(docKey as string) }}</span>
            <span class="doc-status">{{ docStatus }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button v-if="docsTask.status === 'completed' || docsTask.status === 'failed'" @click="closeAnalysisDialog">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  FolderOpened,
  Search,
  Refresh,
  Plus,
  Star,
  Clock,
  Delete,
  Link,
  Edit,
  MagicStick,
  CircleCheck,
  CircleClose,
  Loading,
  Document
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { projectApi, docsApi } from '@/api/project'
import { useDocsTaskStore } from '@/stores/docsTask'
import type { Project } from '@/types'

const loading = ref(false)
const projects = ref<Project[]>([])
const searchKeyword = ref('')
const updating = ref<number | null>(null)
const analyzing = ref<number | null>(null)
const showImportDialog = ref(false)
const importing = ref(false)
const importForm = ref({ path: '', name: '' })

// 项目文档缓存
const projectDocs = ref<Record<number, Array<{ name: string; path: string; size: number; modified: number }>>>({})

const docsTask = useDocsTaskStore()

const showAnalysisDialog = ref(false)

const DOC_LABELS: Record<string, string> = {
  design_md: '设计说明书 (MD)',
  usage_md: '使用说明书 (MD)',
  value_md: '价值分析 (MD)',
  design_html: '设计说明书 (HTML)',
  usage_html: '使用说明书 (HTML)',
  value_html: '价值分析 (HTML)',
  design_pptx: '设计说明书 (PPTX)',
  usage_pptx: '使用说明书 (PPTX)',
  value_pptx: '价值分析 (PPTX)',
}

function getDocLabel(key: string): string {
  return DOC_LABELS[key] || key
}

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

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const filteredProjects = computed(() => {
  if (!searchKeyword.value) return projects.value
  const keyword = searchKeyword.value.toLowerCase()
  return projects.value.filter(p =>
    p.name.toLowerCase().includes(keyword) ||
    p.description?.toLowerCase().includes(keyword)
  )
})

onMounted(async () => {
  loadProjects()
  // 恢复进行中的文档生成任务
  const resumed = await docsTask.resume()
  if (resumed && docsTask.isActive) {
    showAnalysisDialog.value = true
    docsTask.startPolling()
  }
})

onUnmounted(() => {
  docsTask.stopPolling()
})

async function loadProjects() {
  loading.value = true
  try {
    const res = await projectApi.getAll(searchKeyword.value || undefined)
    projects.value = res.data
    // 加载每个项目的文档列表
    loadProjectDocs(res.data)
  } finally {
    loading.value = false
  }
}

async function loadProjectDocs(projectList: Project[]) {
  for (const project of projectList) {
    try {
      const res = await docsApi.getDocs(project.id)
      projectDocs.value[project.id] = res.data.docs
    } catch {
      // 文档不存在时忽略错误
      projectDocs.value[project.id] = []
    }
  }
}

function getDocLinkLabel(docName: string): string {
  if (docName.includes('设计说明书')) return '设计说明书'
  if (docName.includes('使用说明书')) return '使用说明书'
  if (docName.includes('价值点分析')) return '价值点分析'
  return docName.replace('.html', '')
}

// 文档类型定义（固定顺序）
const DOC_TYPES = [
  { key: '设计说明书', label: '设计说明书' },
  { key: '使用说明书', label: '使用说明书' },
  { key: '价值点分析', label: '价值点分析' }
]

function getLatestHtmlDocs(projectId: number): Array<{ name: string; label: string }> {
  const docs = projectDocs.value[projectId] || []
  const htmlDocs = docs.filter(d => d.name.endsWith('.html'))

  const result: Array<{ name: string; label: string }> = []

  for (const docType of DOC_TYPES) {
    // 找到该类型的所有文档
    const matchedDocs = htmlDocs.filter(d => d.name.includes(docType.key))
    if (matchedDocs.length > 0) {
      // 按修改时间排序，取最新的
      const latestDoc = matchedDocs.sort((a, b) => b.modified - a.modified)[0]
      result.push({ name: latestDoc.name, label: docType.label })
    }
  }

  return result
}

function openDoc(projectId: number, docName: string) {
  const url = docsApi.getDocUrl(projectId, docName)
  // 使用文档类型作为窗口名称，确保同一文档类型复用同一个窗口
  const docType = DOC_TYPES.find(t => docName.includes(t.key))?.key || docName
  window.open(url, `doc_${projectId}_${docType}`)
}

async function updateProject(project: Project) {
  updating.value = project.id
  try {
    await projectApi.updateCode(project.id)
    ElMessage.success('更新成功')
    loadProjects()
  } finally {
    updating.value = null
  }
}

async function deleteProject(project: Project) {
  try {
    await projectApi.delete(project.id)
    ElMessage.success('删除成功')
    loadProjects()
  } catch {
    // 错误已在拦截器处理
  }
}

function openFolder(project: Project) {
  if (project.local_path) {
    ElMessage.info(`打开: ${project.local_path}`)
  }
}

async function handleImport() {
  if (!importForm.value.path) {
    ElMessage.warning('请输入项目路径')
    return
  }

  importing.value = true
  try {
    await projectApi.import(importForm.value.path, importForm.value.name || undefined)
    ElMessage.success('导入成功')
    showImportDialog.value = false
    importForm.value = { path: '', name: '' }
    loadProjects()
  } finally {
    importing.value = false
  }
}

async function startAnalysis(project: Project) {
  if (!project.local_path) {
    ElMessage.warning('该项目没有本地路径，请先下载')
    return
  }

  analyzing.value = project.id
  try {
    const res = await docsApi.generate(project.id)
    docsTask.start({
      taskId: res.data.task_id,
      projectId: res.data.project_id,
      projectName: res.data.project_name
    })
    showAnalysisDialog.value = true
    docsTask.startPolling()
  } catch {
    ElMessage.error('启动 AI 分析失败')
  } finally {
    analyzing.value = null
  }
}

function closeAnalysisDialog() {
  showAnalysisDialog.value = false
  // 任务完成后清理 store；进行中的任务只关对话框，不清理
  if (!docsTask.isActive) {
    docsTask.clear()
  }
}
</script>

<style scoped>
.projects-page {
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
  flex-wrap: wrap;
}

.search-input {
  width: 200px;
}

.refresh-btn,
.import-btn {
  font-family: var(--font-display);
  font-weight: 500;
}

/* ========================================
   Projects Grid
   ======================================== */
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.project-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.project-card:hover {
  border-color: rgba(0, 212, 255, 0.3);
  transform: translateY(-4px);
  box-shadow: var(--glass-shadow);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.project-info {
  flex: 1;
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

.project-name {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1rem;
  color: var(--text-primary);
}

.project-stats {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-icon {
  color: var(--accent-amber);
  font-size: 14px;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 0.85rem;
  color: var(--text-secondary);
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
  font-size: 12px;
  color: var(--text-muted);
}

.meta-value {
  font-family: var(--font-display);
  font-size: 0.8rem;
  color: var(--text-muted);
}

.language-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.card-actions {
  display: flex;
  gap: 6px;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--glass-border);
  flex-wrap: wrap;
}

.action-btn {
  flex: 1;
  font-family: var(--font-display);
  font-size: 0.8rem;
  min-width: 0;
}

.action-btn.danger {
  flex: 0.8;
}

.ai-btn {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(0, 212, 255, 0.15));
  border-color: rgba(139, 92, 246, 0.4);
  color: var(--accent-violet);
}

.ai-btn:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(0, 212, 255, 0.25));
  border-color: var(--accent-violet);
  color: var(--accent-violet);
}

/* ========================================
   Import Dialog
   ======================================== */
.import-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

.import-form :deep(.el-form-item__label) {
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
}

/* ========================================
   Analysis Dialog
   ======================================== */
.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.analysis-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.analysis-icon {
  font-size: 24px;
  color: var(--accent-violet);
  animation: spin 2s linear infinite;
}

.analysis-icon.completed {
  color: var(--accent-emerald);
  animation: none;
}

.analysis-icon.failed {
  color: var(--accent-rose);
  animation: none;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.analysis-project {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.analysis-progress {
  margin: 4px 0;
}

.analysis-message {
  font-family: var(--font-body);
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0;
}

.analysis-docs {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 260px;
  overflow-y: auto;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  transition: background var(--transition-fast);
}

.doc-item.doc-done {
  background: rgba(52, 211, 153, 0.08);
}

.doc-item.doc-fail {
  background: rgba(244, 63, 94, 0.08);
}

.doc-icon {
  font-size: 16px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.doc-item.doc-done .doc-icon {
  color: var(--accent-emerald);
}

.doc-item.doc-fail .doc-icon {
  color: var(--accent-rose);
}

.doc-name {
  flex: 1;
  font-family: var(--font-display);
  color: var(--text-secondary);
}

.doc-status {
  font-family: var(--font-display);
  color: var(--text-muted);
  font-size: 0.75rem;
  flex-shrink: 0;
}

.doc-item.doc-done .doc-status {
  color: var(--accent-emerald);
}

.doc-item.doc-fail .doc-status {
  color: var(--accent-rose);
}

/* ========================================
   Doc Links
   ======================================== */
.doc-links {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 8px;
  border-top: 1px solid var(--glass-border);
}

.doc-link-btn {
  font-family: var(--font-display);
  font-size: 0.75rem;
  color: var(--accent-cyan);
  padding: 4px 8px;
}

.doc-link-btn:hover {
  background: rgba(0, 212, 255, 0.1);
  color: var(--text-primary);
}

.doc-link-btn .el-icon {
  font-size: 14px;
  margin-right: 4px;
}

/* Responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    flex-direction: column;
  }

  .search-input {
    width: 100%;
  }

  .projects-grid {
    grid-template-columns: 1fr;
  }
}
</style>
