import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { docsApi } from '@/api/project'

interface TaskInfo {
  taskId: string
  projectId: number
  projectName: string
}

const STORAGE_KEY = 'docs_task_info'

function loadFromStorage(): TaskInfo | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return null
}

function saveToStorage(info: TaskInfo | null) {
  if (info) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(info))
  } else {
    localStorage.removeItem(STORAGE_KEY)
  }
}

export const useDocsTaskStore = defineStore('docsTask', () => {
  const taskId = ref<string | null>(null)
  const projectId = ref<number | null>(null)
  const projectName = ref('')
  const status = ref('')
  const progress = ref(0)
  const message = ref('')
  const docs = ref<Record<string, string>>({})

  let pollTimer: ReturnType<typeof setInterval> | null = null

  const isActive = computed(() =>
    taskId.value && status.value !== 'completed' && status.value !== 'failed'
  )

  function start(info: TaskInfo) {
    taskId.value = info.taskId
    projectId.value = info.projectId
    projectName.value = info.projectName
    status.value = 'pending'
    progress.value = 0
    message.value = '准备生成文档...'
    docs.value = {
      design_md: '等待中', usage_md: '等待中', value_md: '等待中',
      design_html: '等待中', usage_html: '等待中', value_html: '等待中',
      design_pptx: '等待中', usage_pptx: '等待中', value_pptx: '等待中',
    }
    saveToStorage(info)
  }

  async function resume(): Promise<boolean> {
    const saved = loadFromStorage()
    if (!saved) return false

    // 先查询任务状态，确认任务是否还在进行中
    try {
      const res = await docsApi.getStatus(saved.taskId)
      const taskStatus = res.data.status

      // 只有 pending 或 processing 状态才恢复
      if (taskStatus === 'pending' || taskStatus === 'processing') {
        taskId.value = saved.taskId
        projectId.value = saved.projectId
        projectName.value = saved.projectName
        status.value = taskStatus
        progress.value = res.data.progress || 0
        message.value = res.data.message || ''
        if (res.data.docs) docs.value = res.data.docs
        return true
      } else {
        // 任务已完成或失败，清理 localStorage
        saveToStorage(null)
        return false
      }
    } catch {
      // 查询失败（任务不存在），清理 localStorage
      saveToStorage(null)
      return false
    }
  }

  function clear() {
    stopPolling()
    taskId.value = null
    projectId.value = null
    projectName.value = ''
    status.value = ''
    progress.value = 0
    message.value = ''
    docs.value = {}
    saveToStorage(null)
  }

  function startPolling() {
    stopPolling()
    if (!taskId.value) return

    pollTimer = setInterval(async () => {
      try {
        const res = await docsApi.getStatus(taskId.value!)
        status.value = res.data.status
        progress.value = res.data.progress
        message.value = res.data.message
        if (res.data.docs) docs.value = res.data.docs

        if (status.value === 'completed' || status.value === 'failed') {
          stopPolling()
          saveToStorage(null)
        }
      } catch {
        stopPolling()
      }
    }, 2000)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    taskId, projectId, projectName, status, progress, message, docs,
    isActive, start, resume, clear, startPolling, stopPolling
  }
})
