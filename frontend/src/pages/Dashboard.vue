<template>
  <div style="padding:24px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h2>仪表盘</h2>
      <div>
        <el-button type="text" @click="fetchMe">刷新用户</el-button>
        <el-button type="danger" @click="logout">登出</el-button>
      </div>
    </div>

    <el-card>
      <p>欢迎，{{ user?.username || '用户' }}</p>
      <p>角色：{{ user?.role || '-' }}</p>
    </el-card>
  </div>
</template>

<script>
import { ref } from 'vue'
import api from '../api/auth'
import { useRouter } from 'vue-router'

export default {
  setup() {
    const user = ref(null)
    const router = useRouter()

    const fetchMe = async () => {
      try {
        const res = await api.get('/me')
        user.value = res.data
      } catch (e) {
        console.error(e)
      }
    }

    const logout = () => {
      localStorage.removeItem('access_token')
      try {
        const axios = window.axios || null
        if (axios) delete axios.defaults.headers.common['Authorization']
      } catch (e) {}
      // also clear api instance
      delete api.defaults.headers.common['Authorization']
      router.push('/login')
    }

    fetchMe()

    return { user, fetchMe, logout }
  },
}
</script>

<style scoped>
</style>
