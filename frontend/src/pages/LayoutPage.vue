<template>
  <el-container class="layout-container">
    <!-- Header -->
    <el-header class="layout-header">
      <div class="header-left">
        <div class="brand">
          <div class="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="brand-text">{{ configStore.appName }}</span>
        </div>
      </div>
      <div class="header-right">
        <el-dropdown v-if="authStore.requireLogin" @command="handleCommand" trigger="click">
          <div class="user-trigger">
            <div class="user-avatar">
              <el-icon><User /></el-icon>
            </div>
            <span class="user-name">{{ authStore.username }}</span>
            <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="settings">
                <el-icon><Setting /></el-icon>
                <span>设置</span>
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>
                <span>退出登录</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button v-else text @click="router.push('/settings')" class="settings-btn">
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </el-header>

    <el-container class="layout-body">
      <!-- Sidebar -->
      <el-aside width="220px" class="layout-aside">
        <nav class="sidebar-nav">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ active: isActive(item.path) }"
          >
            <el-icon class="nav-icon">
              <component :is="item.icon" />
            </el-icon>
            <span class="nav-text">{{ item.label }}</span>
            <div class="nav-glow"></div>
          </router-link>
        </nav>

        <!-- Sidebar Footer -->
        <div class="sidebar-footer">
          <div class="status-indicator">
            <span class="status-dot"></span>
            <span class="status-text">系统运行中</span>
          </div>
        </div>
      </el-aside>

      <!-- Main Content -->
      <el-main class="layout-main">
        <transition name="page-fade" mode="out-in">
          <router-view />
        </transition>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  User,
  ArrowDown,
  Setting,
  SwitchButton,
  Search,
  TrendCharts,
  Star,
  FolderOpened,
  Clock
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useConfigStore } from '@/stores/config'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const configStore = useConfigStore()

// 加载应用配置
configStore.loadConfig()

const menuItems = [
  { path: '/search', label: '搜索下载', icon: markRaw(Search) },
  { path: '/trending', label: '官方热点', icon: markRaw(TrendCharts) },
  { path: '/history', label: '历史热点', icon: markRaw(Clock) },
  { path: '/starred', label: '高星项目', icon: markRaw(Star) },
  { path: '/projects', label: '项目管理', icon: markRaw(FolderOpened) }
]

const activeMenu = computed(() => route.path)

function isActive(path: string) {
  return route.path === path
}

function handleCommand(command: string) {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (command === 'settings') {
    router.push('/settings')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background: var(--bg-primary);
}

/* ========================================
   Header Styles
   ======================================== */
.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
  padding: 0 24px;
  background: var(--glass-bg);
  border-bottom: 1px solid var(--glass-border);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  position: relative;
  z-index: 100;
}

.layout-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
  opacity: 0.3;
}

.header-left {
  display: flex;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 36px;
  height: 36px;
  background: var(--gradient-cyan);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--glow-cyan-sm);
}

.brand-icon svg {
  width: 20px;
  height: 20px;
  color: var(--bg-primary);
}

.brand-text {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base);
  background: transparent;
  border: 1px solid transparent;
}

.user-trigger:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: var(--glass-border);
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: var(--gradient-violet);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
}

.user-name {
  font-family: var(--font-body);
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.settings-btn {
  color: var(--text-muted);
  font-size: 20px;
  padding: 8px;
}

.settings-btn:hover {
  color: var(--accent-cyan);
}

.dropdown-arrow {
  color: var(--text-muted);
  font-size: 12px;
  transition: transform var(--transition-fast);
}

.user-trigger:hover .dropdown-arrow {
  transform: rotate(180deg);
}

/* ========================================
   Sidebar Styles
   ======================================== */
.layout-aside {
  background: var(--glass-bg);
  border-right: 1px solid var(--glass-border);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  flex-direction: column;
  position: relative;
}

.layout-aside::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 1px;
  background: linear-gradient(180deg, transparent, var(--accent-cyan), transparent);
  opacity: 0.2;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  font-family: var(--font-body);
  font-weight: 500;
  font-size: 0.9rem;
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.nav-item:hover {
  color: var(--text-primary);
  background: rgba(0, 212, 255, 0.08);
}

.nav-item.active {
  color: var(--accent-cyan);
  background: rgba(0, 212, 255, 0.12);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: var(--accent-cyan);
  border-radius: 0 2px 2px 0;
  box-shadow: var(--glow-cyan-sm);
}

.nav-icon {
  font-size: 18px;
  transition: transform var(--transition-base);
}

.nav-item:hover .nav-icon {
  transform: scale(1.1);
}

.nav-item.active .nav-icon {
  color: var(--accent-cyan);
}

.nav-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at left, rgba(0, 212, 255, 0.15), transparent 70%);
  opacity: 0;
  transition: opacity var(--transition-base);
}

.nav-item.active .nav-glow {
  opacity: 1;
}

/* Sidebar Footer */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--glass-border);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.status-dot {
  width: 8px;
  height: 8px;
  background: var(--accent-emerald);
  border-radius: 50%;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.4);
  }
  50% {
    opacity: 0.8;
    box-shadow: 0 0 0 4px rgba(52, 211, 153, 0);
  }
}

.status-text {
  font-family: var(--font-display);
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ========================================
   Main Content Styles
   ======================================== */
.layout-main {
  background: var(--bg-primary);
  padding: 24px;
  position: relative;
  overflow-y: auto;
}

/* Subtle grid pattern */
.layout-main::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 212, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.02) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}

/* Page transition */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: all 0.3s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* ========================================
   Responsive Styles
   ======================================== */
@media (max-width: 768px) {
  .layout-header {
    padding: 0 16px;
  }

  .brand-text {
    display: none;
  }

  .layout-aside {
    width: 64px !important;
  }

  .nav-text {
    display: none;
  }

  .nav-item {
    justify-content: center;
    padding: 12px;
  }

  .sidebar-footer {
    display: none;
  }

  .layout-main {
    padding: 16px;
  }
}
</style>
