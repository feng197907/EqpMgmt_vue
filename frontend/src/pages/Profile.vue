<template>
  <div style="max-width:720px;">
    <h2 style="margin:0 0 16px;">个人设置</h2>

    <!-- 账号信息 -->
    <el-card style="margin-bottom:16px;">
      <template #header><strong>账号信息</strong></template>
      <el-form :model="profileForm" label-width="100px" ref="profileFormRef">
        <el-form-item label="用户名">
          <el-input v-model="profileForm.username" placeholder="当前用户名" />
        </el-form-item>
        <el-form-item label="角色">
          <el-tag :type="roleTagType" size="small">{{ roleLabel }}</el-tag>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="savingProfile" @click="saveProfile">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 修改密码 -->
    <el-card style="margin-bottom:16px;">
      <template #header><strong>修改密码</strong></template>
      <el-form :model="pwdForm" label-width="100px" ref="pwdFormRef" :rules="pwdRules">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入原密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="请输入新密码(至少6位)" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="danger" :loading="changingPwd" @click="changePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/auth'

export default {
  setup() {
    const profileForm = reactive({ username: '' })
    const profileFormRef = ref(null)
    const savingProfile = ref(false)

    const pwdForm = reactive({ old_password: '', new_password: '', confirm_password: '' })
    const pwdFormRef = ref(null)
    const changingPwd = ref(false)

    const currentUser = ref(null)

    const pwdRules = {
      old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
      new_password: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 6, message: '新密码至少6位', trigger: 'blur' },
      ],
      confirm_password: [
        { required: true, message: '请再次输入新密码', trigger: 'blur' },
        {
          validator: (rule, value, callback) => {
            if (value !== pwdForm.new_password) callback(new Error('两次输入的密码不一致'))
            else callback()
          },
          trigger: 'blur',
        },
      ],
    }

    const roleLabelMap = {
      admin: '管理员',
      equipment_engineer: '设备工程师',
      quality_engineer: '质量工程师',
      operator: '操作员',
      maintenance_engineer: '维修工程师',
      viewer: '查看者',
    }

    const roleLabel = computed(() => roleLabelMap[currentUser.value?.role] || currentUser.value?.role || '-')

    const roleTagType = computed(() => {
      const map = { admin: 'danger', equipment_engineer: 'success', quality_engineer: 'warning', operator: 'info', maintenance_engineer: '', viewer: 'info' }
      return map[currentUser.value?.role] || 'info'
    })

    const loadProfile = async () => {
      try {
        const res = await api.get('/api/v1/auth/me')
        currentUser.value = res.data
        profileForm.username = res.data.username
      } catch (e) {
        ElMessage.error('加载账号信息失败')
      }
    }

    const saveProfile = async () => {
      savingProfile.value = true
      try {
        await api.put('/api/v1/auth/profile', { username: profileForm.username })
        ElMessage.success('账号信息已更新')
        await loadProfile()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '保存失败')
      } finally {
        savingProfile.value = false
      }
    }

    const changePassword = async () => {
      const valid = await pwdFormRef.value.validate().catch(() => false)
      if (!valid) return
      changingPwd.value = true
      try {
        await api.put('/api/v1/auth/change-password', {
          old_password: pwdForm.old_password,
          new_password: pwdForm.new_password,
        })
        ElMessage.success('密码修改成功，下次登录请使用新密码')
        pwdForm.old_password = ''
        pwdForm.new_password = ''
        pwdForm.confirm_password = ''
        pwdFormRef.value.resetFields()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '修改密码失败')
      } finally {
        changingPwd.value = false
      }
    }

    onMounted(loadProfile)

    return {
      profileForm, profileFormRef, savingProfile,
      pwdForm, pwdFormRef, pwdRules, changingPwd,
      currentUser, roleLabel, roleTagType,
      saveProfile, changePassword,
    }
  },
}
</script>
