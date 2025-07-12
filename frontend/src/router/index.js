import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置NProgress
NProgress.configure({ showSpinner: false })

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layout/index.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'Monitor' }
      },
      {
        path: '/system',
        name: 'System',
        meta: { title: '系统监控', icon: 'Monitor' },
        children: [
          {
            path: '/system/monitor',
            name: 'SystemMonitor',
            component: () => import('@/views/system/Monitor.vue'),
            meta: { title: '系统监控', icon: 'Monitor' }
          },
          {
            path: '/system/processes',
            name: 'SystemProcesses',
            component: () => import('@/views/system/Processes.vue'),
            meta: { title: '进程管理', icon: 'List' }
          },
          {
            path: '/system/services',
            name: 'SystemServices',
            component: () => import('@/views/system/Services.vue'),
            meta: { title: '系统服务', icon: 'Setting' }
          }
        ]
      },
      {
        path: '/packages',
        name: 'Packages',
        meta: { title: '软件管理', icon: 'Box' },
        children: [
          {
            path: '/packages/market',
            name: 'PackageMarket',
            component: () => import('@/views/packages/Market.vue'),
            meta: { title: '软件市场', icon: 'ShoppingCart' }
          },
          {
            path: '/packages/installed',
            name: 'PackageInstalled',
            component: () => import('@/views/packages/Installed.vue'),
            meta: { title: '已安装软件', icon: 'Box' }
          },
          {
            path: '/packages/lamp',
            name: 'PackageLamp',
            component: () => import('@/views/packages/Lamp.vue'),
            meta: { title: 'LAMP环境', icon: 'Platform' }
          }
        ]
      },
      {
        path: '/files',
        name: 'Files',
        component: () => import('@/views/Files.vue'),
        meta: { title: '文件管理', icon: 'Folder' }
      },
      {
        path: '/security',
        name: 'Security',
        meta: { title: '安全管理', icon: 'Lock' },
        children: [
          {
            path: '/security/firewall',
            name: 'SecurityFirewall',
            component: () => import('@/views/security/Firewall.vue'),
            meta: { title: '防火墙', icon: 'Shield' }
          },
          {
            path: '/security/ssh',
            name: 'SecuritySsh',
            component: () => import('@/views/security/Ssh.vue'),
            meta: { title: 'SSH配置', icon: 'Key' }
          }
        ]
      },
      {
        path: '/users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { title: '用户管理', icon: 'User' }
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/404.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  NProgress.start()
  
  const userStore = useUserStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  
  if (requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && userStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

router.afterEach((to) => {
  NProgress.done()
  document.title = to.meta.title ? `${to.meta.title} - HB-Panel` : 'HB-Panel'
})

export default router
