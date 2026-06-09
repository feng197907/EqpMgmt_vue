<template>
  <el-container class="app-shell">
    <!-- ── 侧边栏 ─────────────────────────────────────────── -->
    <el-aside class="sidebar" :width="sidebarWidth">
      <!-- Logo 区域 -->
      <div class="sidebar-logo">
        <div class="sidebar-logo-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <rect x="2" y="2" width="9" height="9" rx="1.5" fill="#60a5fa"/>
            <rect x="13" y="2" width="9" height="9" rx="1.5" fill="#60a5fa" opacity="0.6"/>
            <rect x="2" y="13" width="9" height="9" rx="1.5" fill="#60a5fa" opacity="0.6"/>
            <rect x="13" y="13" width="9" height="9" rx="1.5" fill="#60a5fa" opacity="0.3"/>
          </svg>
        </div>
        <transition name="fade">
          <span v-if="!collapsed" class="sidebar-logo-text">DMS 设备管理</span>
        </transition>
        <el-icon class="sidebar-collapse-btn" @click="toggleCollapse">
          <Fold v-if="!collapsed" />
          <Expand v-else />
        </el-icon>
      </div>

      <!-- 导航菜单 -->
      <div class="sidebar-nav">
        <div class="nav-section-label" v-if="!collapsed">主要功能</div>
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          :collapse="collapsed"
          :collapse-transition="false"
          router
        >
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>
          <el-menu-item index="/devices">
            <el-icon><Monitor /></el-icon>
            <template #title>设备管理</template>
          </el-menu-item>
          <el-menu-item index="/documents">
            <el-icon><Document /></el-icon>
            <template #title>文档管理</template>
          </el-menu-item>
          <el-menu-item index="/documents/upload">
            <el-icon><Upload /></el-icon>
            <template #title>上传文档</template>
          </el-menu-item>
          <el-menu-item index="/approvals">
            <el-icon><Check /></el-icon>
            <template #title>
              <span>审批任务</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/maintenance">
            <el-icon><Tools /></el-icon>
            <template #title>维护管理</template>
          </el-menu-item>
          <el-menu-item index="/spare-parts">
            <el-icon><Box /></el-icon>
            <template #title>备件管理</template>
          </el-menu-item>
          <el-menu-item index="/borrowing">
            <el-icon><Reading /></el-icon>
            <template #title>借阅管理</template>
          </el-menu-item>
        </el-menu>

        <div class="nav-section-label" v-if="!collapsed" style="margin-top:16px;">系统管理</div>
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          :collapse="collapsed"
          :collapse-transition="false"
          router
        >
          <!-- 用户管理：仅 admin 可见，带密码申请徽章 -->
          <el-menu-item v-if="isAdmin" index="/users">
            <el-icon><User /></el-icon>
            <template #title>
              <span>用户管理</span>
              <el-badge
                v-if="pendingResetCount > 0"
                :value="pendingResetCount"
                :max="99"
                class="sidebar-badge"
              />
            </template>
          </el-menu-item>
          <el-menu-item index="/search">
            <el-icon><Search /></el-icon>
            <template #title>全局搜索</template>
          </el-menu-item>
          <!-- 审计日志：仅 admin 可见 -->
          <el-menu-item v-if="isAdmin" index="/audit-logs">
            <el-icon><List /></el-icon>
            <template #title>审计日志</template>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <template #title>系统设置</template>
          </el-menu-item>
        </el-menu>
      </div>

      <!-- 侧边栏底部用户信息 -->
      <div class="sidebar-footer" v-if="!collapsed">
        <div class="sidebar-user">
          <div class="sidebar-user-avatar">
            {{ (user?.username || 'U')[0].toUpperCase() }}
          </div>
          <div class="sidebar-user-info">
            <div class="sidebar-user-name">{{ user?.username || '用户' }}</div>
            <div class="sidebar-user-role">{{ user?.role || '—' }}</div>
          </div>
          <el-tooltip content="退出登录" placement="right">
            <el-icon class="sidebar-logout-btn" @click="logout">
              <SwitchButton />
            </el-icon>
          </el-tooltip>
        </div>
      </div>
    </el-aside>

    <!-- ── 主体区域 ──────────────────────────────────────── -->
    <el-container class="main-container">
      <!-- 顶栏 -->
      <el-header class="app-header">
        <!-- 面包屑 -->
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentPage">{{ currentPage }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <!-- 右侧操作区 -->
        <div class="header-right">
          <el-tooltip content="全局搜索" placement="bottom">
            <el-icon class="header-action-btn" @click="$router.push('/search')">
              <Search />
            </el-icon>
          </el-tooltip>

          <!-- admin 密码重置提醒铃铛 -->
          <el-tooltip
            v-if="isAdmin && pendingResetCount > 0"
            :content="`${pendingResetCount} 条密码重置申请待处理`"
            placement="bottom"
          >
            <div class="header-bell-wrap" @click="$router.push('/users')">
              <el-icon class="header-action-btn header-bell"><Bell /></el-icon>
              <span class="header-bell-badge">{{ pendingResetCount > 9 ? '9+' : pendingResetCount }}</span>
            </div>
          </el-tooltip>

          <div class="header-divider"></div>
          <router-link to="/profile" class="header-user">
            <div class="header-user-avatar">
              {{ (user?.username || 'U')[0].toUpperCase() }}
            </div>
            <span class="header-user-name">{{ user?.username || '用户' }}</span>
            <el-tag size="small" class="header-role-tag">{{ user?.role || '—' }}</el-tag>
          </router-link>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  HomeFilled, Document, Upload, Check, Tools, Monitor,
  User, Box, Reading, Search, List, Setting, UserFilled,
  Fold, Expand, SwitchButton, Bell
} from '@element-plus/icons-vue'
import api from '../api/auth'

const PAGE_NAMES = {
  '/dashboard': '仪表盘',
  '/devices': '设备管理',
  '/documents': '文档管理',
  '/documents/upload': '上传文档',
  '/approvals': '审批任务',
  '/maintenance': '维护管理',
  '/spare-parts': '备件管理',
  '/borrowing': '借阅管理',
  '/users': '用户管理',
  '/search': '全局搜索',
  '/audit-logs': '审计日志',
  '/settings': '系统设置',
  '/profile': '个人设置',
  '/esign': '电子签章',
}

export default {
  name: 'AppLayout',
  components: {
    HomeFilled, Document, Upload, Check, Tools, Monitor,
    User, Box, Reading, Search, List, Setting, UserFilled,
    Fold, Expand, SwitchButton, Bell
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const user = ref(null)
    const collapsed = ref(false)
    const pendingResetCount = ref(0)
    let pollTimer = null

    const sidebarWidth = computed(() => collapsed.value ? '60px' : '220px')

    const isAdmin = computed(() => user.value?.role === 'admin')

    const activeMenu = computed(() => {
      const path = route.path
      if (path.startsWith('/maintenance')) return '/maintenance'
      if (path.startsWith('/documents/upload')) return '/documents/upload'
      return path
    })

    const currentPage = computed(() => {
      const path = route.path
      if (path.startsWith('/maintenance')) return PAGE_NAMES['/maintenance']
      return PAGE_NAMES[path] || ''
    })

    const toggleCollapse = () => {
      collapsed.value = !collapsed.value
    }

    const fetchMe = async () => {
      try {
        const res = await api.get('/api/v1/auth/me')
        user.value = res.data
        // 如果是 admin，立即拉取待处理数
        if (res.data?.role === 'admin') {
          fetchPendingCount()
        }
      } catch (e) {
        console.error('获取用户信息失败', e)
      }
    }

    const fetchPendingCount = async () => {
      // 仅 admin 才有权限访问此接口，非 admin 直接跳过
      if (!isAdmin.value) return
      try {
        // 使用 /resets?status=pending 获取数量，兼容旧版后端（无 /count 接口）
        const res = await api.get('/api/v1/password/resets', { params: { status: 'pending' } })
        pendingResetCount.value = Array.isArray(res.data) ? res.data.length : 0
      } catch (e) {
        // 请求失败时静默忽略（例如网络错误或权限不足）
        pendingResetCount.value = 0
      }
    }

    const startPoll = () => {
      // 每 60 秒轮询一次
      pollTimer = setInterval(() => {
        if (isAdmin.value) fetchPendingCount()
      }, 60000)
    }

    const logout = () => {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      delete api.defaults.headers.common['Authorization']
      router.push('/login')
    }

    onMounted(() => {
      fetchMe()
      startPoll()
    })

    onUnmounted(() => {
      if (pollTimer) clearInterval(pollTimer)
    })

    return {
      user, collapsed, sidebarWidth, activeMenu, currentPage,
      isAdmin, pendingResetCount,
      toggleCollapse, logout, fetchPendingCount,
    }
  },
}
</script>

<style scoped>
/* ── 整体布局 ─────────────────────────────────── */
.app-shell {
  height: 100vh;
  background: var(--content-bg);
}

/* ── 侧边栏 ───────────────────────────────────── */
.sidebar {
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
  flex-shrink: 0;
  overflow: hidden;
  position: relative;
}

/* Logo */
.sidebar-logo {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 14px;
  border-bottom: 1px solid var(--sidebar-border);
  gap: 10px;
  flex-shrink: 0;
}

.sidebar-logo-icon {
  width: 32px;
  height: 32px;
  background: rgba(26, 86, 219, 0.15);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sidebar-logo-text {
  font-size: 14px;
  font-weight: 700;
  color: #e2e8f0;
  letter-spacing: 0.3px;
  white-space: nowrap;
  flex: 1;
}

.sidebar-collapse-btn {
  color: #64748b;
  cursor: pointer;
  font-size: 18px;
  flex-shrink: 0;
  transition: color 0.15s;
}
.sidebar-collapse-btn:hover { color: #94a3b8; }

/* 导航 */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.nav-section-label {
  font-size: 10px;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 6px 22px 4px;
  margin-top: 4px;
}

/* 菜单全局色 */
:deep(.sidebar-menu) {
  background: transparent !important;
  border-right: none !important;
  padding: 0 10px;
}

:deep(.sidebar-menu .el-menu-item) {
  border-radius: 6px !important;
  margin: 1px 0 !important;
  height: 38px !important;
  line-height: 38px !important;
  font-size: 13.5px !important;
  font-weight: 500 !important;
  color: var(--sidebar-text) !important;
  transition: all 0.15s ease !important;
  position: relative;
}

:deep(.sidebar-menu .el-menu-item:hover) {
  background: rgba(148, 163, 184, 0.08) !important;
  color: var(--sidebar-text-hover) !important;
}

:deep(.sidebar-menu .el-menu-item.is-active) {
  background: rgba(26, 86, 219, 0.15) !important;
  color: #60a5fa !important;
}

:deep(.sidebar-menu .el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 18px;
  background: #1a56db;
  border-radius: 0 2px 2px 0;
}

:deep(.sidebar-menu .el-menu-item .el-icon) {
  font-size: 15px !important;
  color: inherit !important;
}

:deep(.el-menu--collapse .sidebar-menu .el-menu-item) {
  padding: 0 !important;
  justify-content: center;
}

/* 菜单徽章 */
.sidebar-badge {
  margin-left: auto;
}
:deep(.sidebar-badge .el-badge__content) {
  font-size: 10px !important;
  padding: 0 4px !important;
  height: 16px !important;
  line-height: 16px !important;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 10px;
  border-top: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 8px;
  border-radius: 8px;
  cursor: default;
}

.sidebar-user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(26, 86, 219, 0.3);
  color: #93c5fd;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sidebar-user-info {
  flex: 1;
  overflow: hidden;
}

.sidebar-user-name {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-user-role {
  font-size: 11px;
  color: #64748b;
  margin-top: 1px;
}

.sidebar-logout-btn {
  color: #64748b;
  cursor: pointer;
  font-size: 16px;
  flex-shrink: 0;
  transition: color 0.15s;
}
.sidebar-logout-btn:hover { color: #f87171; }

/* ── 主容器 ───────────────────────────────────── */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* ── 顶栏 ─────────────────────────────────────── */
.app-header {
  height: 56px !important;
  background: #fff;
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}

.header-left {}

:deep(.el-breadcrumb__separator) { color: #cbd5e1; }
:deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-action-btn {
  font-size: 18px;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: color 0.15s;
}
.header-action-btn:hover { color: var(--el-color-primary); }

/* 顶栏铃铛 */
.header-bell-wrap {
  position: relative;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.header-bell {
  font-size: 20px;
  color: #f59e0b !important;
  animation: bell-shake 2s infinite;
}

.header-bell-badge {
  position: absolute;
  top: -6px;
  right: -8px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  border-radius: 10px;
  padding: 1px 5px;
  line-height: 14px;
  min-width: 16px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(239, 68, 68, 0.4);
}

@keyframes bell-shake {
  0%, 90%, 100% { transform: rotate(0); }
  92% { transform: rotate(-12deg); }
  94% { transform: rotate(12deg); }
  96% { transform: rotate(-8deg); }
  98% { transform: rotate(8deg); }
}

.header-divider {
  width: 1px;
  height: 20px;
  background: var(--el-border-color);
}

.header-user {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.15s;
}
.header-user:hover { background: var(--el-fill-color); }

.header-user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 7px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.header-role-tag {
  background: var(--el-fill-color-light) !important;
  color: var(--el-text-color-secondary) !important;
  border: none !important;
  font-size: 11px !important;
  padding: 0 6px !important;
}

/* ── 内容区 ───────────────────────────────────── */
.app-main {
  padding: 20px !important;
  background: var(--content-bg);
  flex: 1;
  overflow-y: auto;
}

/* ── 过渡动画 ─────────────────────────────────── */
.fade-enter-active,
.fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
