<template>
  <el-container style="height:100vh;">
    <!-- 侧边栏 -->
    <el-aside width="220px" style="background:#304156;overflow-y:auto;">
      <div style="height:60px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:18px;font-weight:bold;border-bottom:1px solid #4a5a6a;">
        DMS 设备管理
      </div>
      <el-menu
        :default-active="activeMenu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
        style="border-right:none;"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/documents">
          <el-icon><Document /></el-icon>
          <span>文档管理</span>
        </el-menu-item>
        <el-menu-item index="/documents/upload">
          <el-icon><Upload /></el-icon>
          <span>上传文档</span>
        </el-menu-item>
        <el-menu-item index="/approvals">
          <el-icon><Check /></el-icon>
          <span>审批任务</span>
        </el-menu-item>
        <el-menu-item index="/maintenance">
          <el-icon><Tools /></el-icon>
          <span>维护管理</span>
        </el-menu-item>
        <el-menu-item index="/devices">
          <el-icon><Monitor /></el-icon>
          <span>设备管理</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/spare-parts">
          <el-icon><Box /></el-icon>
          <span>备件管理</span>
        </el-menu-item>
        <el-menu-item index="/borrowing">
          <el-icon><Reading /></el-icon>
          <span>借阅管理</span>
        </el-menu-item>
        <el-menu-item index="/search">
          <el-icon><SearchIcon /></el-icon>
          <span>全局搜索</span>
        </el-menu-item>
        <el-menu-item index="/audit-logs">
          <el-icon><List /></el-icon>
          <span>审计日志</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><UserFilled /></el-icon>
          <span>个人设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主体区域 -->
    <el-container>
      <!-- 顶栏 -->
      <el-header style="height:50px;background:#fff;border-bottom:1px solid #e6e6e6;display:flex;align-items:center;justify-content:flex-end;padding:0 20px;">
        <span style="margin-right:12px;color:#666;">{{ user?.username || '用户' }}</span>
        <el-tag size="small" type="info">{{ user?.role || '-' }}</el-tag>
        <el-button type="danger" size="small" style="margin-left:12px;" @click="logout">登出</el-button>
      </el-header>

      <!-- 内容区 -->
      <el-main style="background:#f0f2f5;padding:20px;">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { HomeFilled, Document, Upload, Check, Tools, Monitor, User, Box, Reading, Search as SearchIcon, List, Setting, UserFilled } from '@element-plus/icons-vue'
import api from '../api/auth'

export default {
  name: 'AppLayout',
  components: { HomeFilled, Document, Upload, Check, Tools, Monitor, User, Box, Reading, SearchIcon, List, Setting, UserFilled },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const user = ref(null)

    const activeMenu = computed(() => {
      const path = route.path
      if (path.startsWith('/maintenance')) return '/maintenance'
      if (path.startsWith('/documents/upload')) return '/documents/upload'
      return path
    })

    const fetchMe = async () => {
      try {
        const res = await api.get('/api/v1/auth/me')
        user.value = res.data
      } catch (e) {
        console.error('获取用户信息失败', e)
      }
    }

    const logout = () => {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      delete api.defaults.headers.common['Authorization']
      router.push('/login')
    }

    fetchMe()

    return { user, activeMenu, logout }
  },
}
</script>
