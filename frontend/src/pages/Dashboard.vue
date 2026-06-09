<template>
  <div class="dashboard">
    <!-- 页面头 -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">仪表盘</h1>
        <p class="page-subtitle">欢迎回来，{{ username }} — 这是系统今日概况</p>
      </div>
      <div class="page-header-right">
        <span class="dashboard-time">{{ currentTime }}</span>
      </div>
    </div>

    <!-- 统计指标卡片 -->
    <el-row :gutter="16" class="metric-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="metric-card metric-card--blue" @click="$router.push('/devices')" style="cursor:pointer;">
          <div class="metric-value">{{ deviceCount }}</div>
          <div class="metric-label">活跃设备</div>
          <div class="metric-icon">
            <el-icon><Monitor /></el-icon>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="metric-card metric-card--teal" @click="$router.push('/documents')" style="cursor:pointer;">
          <div class="metric-value">{{ docCount }}</div>
          <div class="metric-label">文档总数</div>
          <div class="metric-icon">
            <el-icon><Document /></el-icon>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="metric-card metric-card--amber" @click="$router.push('/approvals')" style="cursor:pointer;">
          <div class="metric-value">{{ pendingCount }}</div>
          <div class="metric-label">待审批任务</div>
          <div class="metric-icon">
            <el-icon><Check /></el-icon>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="metric-card metric-card--red" @click="$router.push('/spare-parts')" style="cursor:pointer;">
          <div class="metric-value">{{ lowStockCount }}</div>
          <div class="metric-label">库存预警</div>
          <div class="metric-icon">
            <el-icon><Box /></el-icon>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷导航 + 近期活动 -->
    <el-row :gutter="16" style="margin-top:16px;">
      <!-- 快捷导航 -->
      <el-col :xs="24" :lg="14">
        <el-card>
          <template #header>
            <span class="card-title">快捷导航</span>
          </template>
          <div class="quick-nav-grid">
            <div
              v-for="nav in navItems"
              :key="nav.path"
              class="quick-nav-item"
              @click="$router.push(nav.path)"
            >
              <div class="nav-icon-wrap" :class="`nav-icon-wrap--${nav.color}`">
                <el-icon class="nav-icon"><component :is="nav.icon" /></el-icon>
              </div>
              <span class="nav-label">{{ nav.label }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 系统状态 -->
      <el-col :xs="24" :lg="10">
        <el-card>
          <template #header>
            <span class="card-title">系统模块状态</span>
          </template>
          <div class="status-list">
            <div class="status-item" v-for="s in systemStatus" :key="s.name">
              <div class="status-item-left">
                <div class="status-dot" :class="`status-dot--${s.level}`"></div>
                <span class="status-name">{{ s.name }}</span>
              </div>
              <div class="status-item-right">
                <span class="status-value" :class="`status-value--${s.level}`">{{ s.label }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Monitor, Document, Check, Box, Tools, Reading,
  User, Search, List, Setting, Upload
} from '@element-plus/icons-vue'
import { listDevices } from '../api/devices'
import { listDocuments } from '../api/documents'
import api from '../api/auth'

export default {
  name: 'DashboardPage',
  components: { Monitor, Document, Check, Box, Tools, Reading, User, Search, List, Setting, Upload },
  setup() {
    const deviceCount = ref(0)
    const docCount = ref(0)
    const pendingCount = ref(0)
    const lowStockCount = ref(0)
    const username = ref('用户')
    const currentTime = ref('')
    let timer = null

    const updateTime = () => {
      const now = new Date()
      currentTime.value = now.toLocaleString('zh-CN', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit',
      })
    }
    updateTime()
    timer = setInterval(updateTime, 30000)

    const navItems = [
      { path: '/devices', label: '设备管理', icon: Monitor, color: 'blue' },
      { path: '/documents', label: '文档管理', icon: Document, color: 'teal' },
      { path: '/documents/upload', label: '上传文档', icon: Upload, color: 'indigo' },
      { path: '/approvals', label: '审批任务', icon: Check, color: 'amber' },
      { path: '/maintenance', label: '维护管理', icon: Tools, color: 'slate' },
      { path: '/spare-parts', label: '备件管理', icon: Box, color: 'red' },
      { path: '/borrowing', label: '借阅管理', icon: Reading, color: 'teal' },
      { path: '/users', label: '用户管理', icon: User, color: 'blue' },
      { path: '/search', label: '全局搜索', icon: Search, color: 'slate' },
      { path: '/audit-logs', label: '审计日志', icon: List, color: 'indigo' },
    ]

    const systemStatus = ref([
      { name: '设备管理模块', level: 'active', label: '正常运行' },
      { name: '文档审批流程', level: 'active', label: '正常运行' },
      { name: '备件库存监控', level: 'active', label: '正常运行' },
      { name: '数据备份服务', level: 'active', label: '正常运行' },
    ])

    onMounted(async () => {
      // 获取用户信息
      try {
        const res = await api.get('/api/v1/auth/me')
        username.value = res.data?.username || '用户'
      } catch (e) { /* ignore */ }

      // 设备数
      try {
        const devices = await listDevices()
        deviceCount.value = devices.length
      } catch (e) { /* ignore */ }

      // 文档数
      try {
        const docs = await listDocuments()
        docCount.value = docs.length
      } catch (e) { /* ignore */ }

      // 待审批
      try {
        const approvals = await api.get('/api/v1/approvals/')
        pendingCount.value = (approvals.data || []).length
      } catch (e) { /* ignore */ }

      // 库存预警（简单模拟）
      try {
        const parts = await api.get('/api/v1/spare-parts/')
        const low = (parts.data || []).filter(p => (p.quantity || 0) < (p.min_quantity || 5))
        lowStockCount.value = low.length
      } catch (e) { /* ignore */ }
    })

    onUnmounted(() => {
      if (timer) clearInterval(timer)
    })

    return {
      deviceCount, docCount, pendingCount, lowStockCount,
      username, currentTime, navItems, systemStatus
    }
  },
}
</script>

<style scoped>
.dashboard {}

.dashboard-time {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  padding: 5px 12px;
  border-radius: 20px;
  border: 1px solid var(--el-border-color);
}

.metric-row .el-col { margin-bottom: 0; }

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 快捷导航 */
.quick-nav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 10px;
}

.quick-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 8px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fff;
  gap: 8px;
}

.quick-nav-item:hover {
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(26, 86, 219, 0.12);
  transform: translateY(-2px);
}

.nav-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s;
}

.nav-icon-wrap--blue   { background: #dbeafe; color: #1d4ed8; }
.nav-icon-wrap--teal   { background: #ccfbf1; color: #0f766e; }
.nav-icon-wrap--amber  { background: #fef3c7; color: #b45309; }
.nav-icon-wrap--red    { background: #fee2e2; color: #b91c1c; }
.nav-icon-wrap--slate  { background: #f1f5f9; color: #475569; }
.nav-icon-wrap--indigo { background: #e0e7ff; color: #4338ca; }

.quick-nav-item:hover .nav-icon-wrap--blue   { background: #1d4ed8; color: #fff; }
.quick-nav-item:hover .nav-icon-wrap--teal   { background: #0f766e; color: #fff; }
.quick-nav-item:hover .nav-icon-wrap--amber  { background: #b45309; color: #fff; }
.quick-nav-item:hover .nav-icon-wrap--red    { background: #b91c1c; color: #fff; }
.quick-nav-item:hover .nav-icon-wrap--slate  { background: #475569; color: #fff; }
.quick-nav-item:hover .nav-icon-wrap--indigo { background: #4338ca; color: #fff; }

.nav-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-regular);
  text-align: center;
  line-height: 1.2;
}

/* 状态列表 */
.status-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
  transition: background 0.15s;
}

.status-item:hover { background: var(--el-fill-color-light); }

.status-item-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-dot--active  { background: #059669; box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.2); }
.status-dot--warning { background: #d97706; box-shadow: 0 0 0 2px rgba(217, 119, 6, 0.2); }
.status-dot--error   { background: #dc2626; box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2); }

.status-name {
  font-size: 13px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.status-value {
  font-size: 12px;
  font-weight: 500;
}
.status-value--active  { color: #059669; }
.status-value--warning { color: #d97706; }
.status-value--error   { color: #dc2626; }
</style>
