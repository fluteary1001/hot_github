import { defineStore } from 'pinia'
import { ref } from 'vue'
import { configApi } from '@/api/config'

export const useConfigStore = defineStore('config', () => {
  const appName = ref('Hot Github')
  const version = ref('2.0.0')
  const loaded = ref(false)

  async function loadConfig() {
    if (loaded.value) return
    try {
      const res = await configApi.getConfig()
      appName.value = res.data.app_name
      version.value = res.data.version
      loaded.value = true
    } catch {
      // 加载失败时使用默认值
      loaded.value = true
    }
  }

  return { appName, version, loaded, loadConfig }
})
