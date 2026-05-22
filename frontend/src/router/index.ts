import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/pages/LayoutPage.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/search'
      },
      {
        path: 'search',
        name: 'Search',
        component: () => import('@/pages/SearchPage.vue')
      },
      {
        path: 'trending',
        name: 'Trending',
        component: () => import('@/pages/TrendingPage.vue')
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('@/pages/HistoryTrendingPage.vue')
      },
      {
        path: 'starred',
        name: 'Starred',
        component: () => import('@/pages/StarredPage.vue')
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/pages/ProjectsPage.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/pages/SettingsPage.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
let authChecked = false

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 首次导航时检查是否需要登录
  if (!authChecked) {
    authChecked = true
    await authStore.checkRequireLogin()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router