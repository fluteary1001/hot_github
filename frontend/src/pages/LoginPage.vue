<template>
  <div class="login-container">
    <!-- Animated Starfield Background -->
    <div class="starfield">
      <div v-for="n in 50" :key="n" class="star" :style="getStarStyle(n)"></div>
    </div>

    <!-- Gradient Orbs -->
    <div class="orb orb-cyan"></div>
    <div class="orb orb-violet"></div>
    <div class="orb orb-amber"></div>

    <!-- Login Card -->
    <div class="login-wrapper">
      <div class="login-card">
        <!-- Logo & Title -->
        <div class="login-header">
          <div class="logo-container">
            <svg class="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h1 class="login-title">{{ configStore.appName }}</h1>
          <p class="login-subtitle">探索开源宇宙 · 管理你的项目星系</p>
        </div>

        <!-- Login Form -->
        <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名"
              :prefix-icon="User"
              size="large"
              class="login-input"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              size="large"
              show-password
              class="login-input"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              @click="handleLogin"
              class="login-button"
            >
              <span v-if="!loading">进入观测站</span>
              <span v-else>正在验证...</span>
            </el-button>
          </el-form-item>
        </el-form>

        <!-- Footer -->
        <div class="login-footer">
          <span class="footer-text">默认账号: admin / admin123</span>
        </div>
      </div>

      <!-- Version Badge -->
      <div class="version-badge">
        <span>v{{ configStore.version }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useConfigStore } from '@/stores/config'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const configStore = useConfigStore()
configStore.loadConfig()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// Generate random star positions
function getStarStyle(n: number) {
  const size = Math.random() * 2 + 1
  const x = Math.random() * 100
  const y = Math.random() * 100
  const delay = Math.random() * 3
  const duration = Math.random() * 2 + 2

  return {
    left: `${x}%`,
    top: `${y}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`
  }
}

async function handleLogin() {
  const valid = await formRef.value?.validate()
  if (!valid) return

  loading.value = true
  try {
    const success = await authStore.login(form.username, form.password)
    if (success) {
      router.push('/')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--bg-primary);
  position: relative;
  overflow: hidden;
}

/* Starfield Background */
.starfield {
  position: absolute;
  inset: 0;
  overflow: hidden;
  z-index: 1;
}

.star {
  position: absolute;
  background: white;
  border-radius: 50%;
  animation: twinkle var(--duration, 3s) ease-in-out infinite;
  animation-delay: var(--delay, 0s);
}

@keyframes twinkle {
  0%, 100% {
    opacity: 0.2;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.5);
  }
}

/* Gradient Orbs */
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  z-index: 0;
  animation: float 20s ease-in-out infinite;
}

.orb-cyan {
  width: 400px;
  height: 400px;
  background: var(--accent-cyan);
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}

.orb-violet {
  width: 300px;
  height: 300px;
  background: var(--accent-violet);
  bottom: -50px;
  left: -50px;
  animation-delay: -7s;
}

.orb-amber {
  width: 200px;
  height: 200px;
  background: var(--accent-amber);
  top: 50%;
  left: 20%;
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(30px, -30px) scale(1.1);
  }
  50% {
    transform: translate(-20px, 20px) scale(0.9);
  }
  75% {
    transform: translate(-30px, -20px) scale(1.05);
  }
}

/* Login Wrapper */
.login-wrapper {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

/* Login Card */
.login-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: 48px 40px;
  width: 420px;
  max-width: 90vw;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow:
    var(--glass-shadow-lg),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  animation: fadeInUp 0.6s ease forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Header */
.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-container {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: var(--gradient-cyan);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--glow-cyan);
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: var(--glow-cyan-sm);
  }
  50% {
    box-shadow: var(--glow-cyan);
  }
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: var(--bg-primary);
}

.login-title {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  letter-spacing: -0.02em;
}

.login-subtitle {
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: var(--text-muted);
  margin: 0;
}

/* Form */
.login-card :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-card :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

.login-input :deep(.el-input__wrapper) {
  background: var(--bg-tertiary);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  box-shadow: none;
  transition: all var(--transition-base);
}

.login-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 212, 255, 0.5);
}

.login-input :deep(.el-input__wrapper.is-focus),
.login-input :deep(.el-input__wrapper:focus-within) {
  border-color: var(--accent-cyan);
  box-shadow: var(--glow-cyan-sm);
}

.login-input :deep(.el-input__inner) {
  color: var(--text-primary);
  font-family: var(--font-body);
}

.login-input :deep(.el-input__inner::placeholder) {
  color: var(--text-muted);
}

.login-input :deep(.el-input__prefix) {
  color: var(--text-muted);
}

/* Login Button */
.login-button {
  width: 100%;
  height: 48px;
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 600;
  background: var(--gradient-cyan);
  border: none;
  border-radius: var(--radius-md);
  color: var(--bg-primary);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.login-button::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transform: translateX(-100%);
  transition: transform 0.5s;
}

.login-button:hover::before {
  transform: translateX(100%);
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--glow-cyan);
}

.login-button:active {
  transform: translateY(0);
}

/* Footer */
.login-footer {
  margin-top: 24px;
  text-align: center;
}

.footer-text {
  font-family: var(--font-display);
  font-size: 0.75rem;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  padding: 6px 12px;
  border-radius: var(--radius-full);
}

/* Version Badge */
.version-badge {
  font-family: var(--font-display);
  font-size: 0.7rem;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  padding: 4px 12px;
  border-radius: var(--radius-full);
  border: 1px solid var(--glass-border);
}

/* Responsive */
@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px;
  }

  .login-title {
    font-size: 1.5rem;
  }

  .logo-container {
    width: 56px;
    height: 56px;
  }

  .logo-icon {
    width: 28px;
    height: 28px;
  }
}
</style>
