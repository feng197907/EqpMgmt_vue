<template>
  <div style="max-width:420px;margin:80px auto;padding:24px;border:1px solid #eee;border-radius:8px;">
    <h3 style="text-align:center;margin-bottom:16px;">登录 - DMS</h3>
    <el-form :model="form" ref="formRef" @submit.native.prevent="onSubmit">
      <el-form-item>
        <el-input v-model="form.username" placeholder="用户名" clearable />
      </el-form-item>
      <el-form-item>
        <el-input v-model="form.password" placeholder="密码" show-password />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSubmit" style="width:100%">登录</el-button>
      </el-form-item>
      <el-alert v-if="error" :title="error" type="error" show-icon />
    </el-form>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { login } from '../api/auth'

export default {
  setup() {
    const form = ref({ username: '', password: '' })
    const error = ref('')
    const router = useRouter()

    const onSubmit = async () => {
      error.value = ''
      try {
        const res = await login(form.value.username, form.value.password)
        const token = res.access_token
        const refresh = res.refresh_token
        localStorage.setItem('access_token', token)
        if (refresh) localStorage.setItem('refresh_token', refresh)
        // set Authorization header for api instance
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        router.push('/dashboard')
      } catch (e) {
        error.value = e.response?.data?.detail || '登录失败，请检查账号密码'
      }
    }

    return { form, error, onSubmit }
  },
}
</script>

<style scoped>
</style>
