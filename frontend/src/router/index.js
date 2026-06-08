import { createRouter, createWebHistory } from 'vue-router'
import Login from '../pages/Login.vue'
import Layout from '../pages/Layout.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: Login },
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('../pages/Dashboard.vue'),
      },
      {
        path: '/documents',
        name: 'Documents',
        component: () => import('../pages/Documents.vue'),
      },
      {
        path: '/documents/upload',
        name: 'UploadDocument',
        component: () => import('../pages/UploadDocument.vue'),
      },
      {
        path: '/approvals',
        name: 'Approvals',
        component: () => import('../pages/Approvals.vue'),
      },
      {
        path: '/maintenance/:deviceId?',
        name: 'Maintenance',
        component: () => import('../pages/Maintenance.vue'),
      },
      {
        path: '/devices',
        name: 'Devices',
        component: () => import('../pages/Devices.vue'),
      },
      {
        path: '/users',
        name: 'Users',
        component: () => import('../pages/Users.vue'),
      },
      {
        path: '/spare-parts',
        name: 'SpareParts',
        component: () => import('../pages/SpareParts.vue'),
      },
      {
        path: '/borrowing',
        name: 'Borrowing',
        component: () => import('../pages/Borrowing.vue'),
      },
      {
        path: '/audit-logs',
        name: 'AuditLogs',
        component: () => import('../pages/AuditLogs.vue'),
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('../pages/Settings.vue'),
      },
      {
        path: '/search',
        name: 'Search',
        component: () => import('../pages/Search.vue'),
      },
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('../pages/Profile.vue'),
      },
      {
        path: '/esign',
        name: 'ESign',
        component: () => import('../pages/ESign.vue'),
      },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

export default router

// Simple auth guard: protect all routes except /login
router.beforeEach((to, from, next) => {
  const publicPaths = ['/login']
  const token = localStorage.getItem('access_token')
  if (!token && !publicPaths.includes(to.path)) {
    return next('/login')
  }
  if (token && to.path === '/login') {
    return next('/dashboard')
  }
  return next()
})
