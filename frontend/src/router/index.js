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
