<template>
  <div class="settings-page">
    <div class="settings-card about-card">
      <div class="card-header">
        <div class="card-icon about">
          <el-icon><InfoFilled /></el-icon>
        </div>
        <div class="card-info">
          <h3 class="card-title">关于</h3>
          <p class="card-desc">{{ configStore.appName }} 版本信息</p>
        </div>
      </div>

      <div class="about-content">
        <div class="about-item">
          <span class="about-label">应用名称</span>
          <span class="about-value">{{ configStore.appName }}</span>
        </div>
        <div class="about-item">
          <span class="about-label">版本</span>
          <span class="about-value version">v{{ configStore.version }}</span>
        </div>
        <div class="about-item">
          <span class="about-label">技术栈</span>
          <span class="about-value">FastAPI + Vue 3 + Element Plus</span>
        </div>
        <div class="about-item">
          <span class="about-label">功能</span>
          <span class="about-value">GitHub 项目搜索、下载、管理、AI 文档分析</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { InfoFilled } from '@element-plus/icons-vue'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()
configStore.loadConfig()
</script>

<style scoped>
.settings-page {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
  position: relative;
  z-index: 1;
}

.settings-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  overflow: hidden;
  transition: all var(--transition-base);
}

.settings-card:hover {
  border-color: rgba(0, 212, 255, 0.2);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-bottom: 1px solid var(--glass-border);
  background: rgba(0, 212, 255, 0.02);
}

.card-icon.about {
  width: 48px;
  height: 48px;
  background: var(--gradient-amber);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--bg-primary);
  box-shadow: var(--glow-amber);
}

.card-info {
  flex: 1;
}

.card-title {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.card-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0;
}

.about-content {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 480px) {
  .about-content {
    grid-template-columns: 1fr;
  }
}

.about-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.about-label {
  font-family: var(--font-display);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.about-value {
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: var(--text-primary);
}

.about-value.version {
  font-family: var(--font-display);
  color: var(--accent-cyan);
  font-weight: 600;
}
</style>
