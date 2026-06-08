<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h2 style="margin:0;">用户管理</h2>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon> 新增用户
      </el-button>
    </div>

    <el-card>
      <el-table :data="users" stripe v-loading="loading" empty-text="暂无用户">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="200" />
        <el-table-column prop="role" label="角色" width="160">
          <template #default="{ row }">
            <el-tag :type="roleTag(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="460px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="登录用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="isEdit ? '留空则不修改' : '登录密码'"
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width:100%;">
            <el-option label="管理员" value="admin" />
            <el-option label="设备工程师" value="equipment_engineer" />
            <el-option label="设备管理员" value="equipment_manager" />
            <el-option label="质量工程师" value="quality_engineer" />
            <el-option label="操作员" value="operator" />
            <el-option label="审核员" value="reviewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listUsers, createUser, updateUser, deleteUser } from '../api/users'

export default {
  components: { Plus },
  setup() {
    const users = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const dialogVisible = ref(false)
    const isEdit = ref(false)
    const editId = ref(null)
    const formRef = ref(null)

    const form = reactive({ username: '', password: '', role: 'equipment_engineer' })

    const rules = {
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      password: [
        {
          validator: (_rule, value, cb) => {
            if (!isEdit.value && !value) cb(new Error('请输入密码'))
            else if (value && value.length < 6) cb(new Error('密码至少6位'))
            else cb()
          },
          trigger: 'blur',
        },
      ],
      role: [{ required: true, message: '请选择角色', trigger: 'change' }],
    }

    const roleLabel = (role) => {
      const map = {
        admin: '管理员',
        equipment_engineer: '设备工程师',
        equipment_manager: '设备管理员',
        quality_engineer: '质量工程师',
        operator: '操作员',
        reviewer: '审核员',
      }
      return map[role] || role
    }

    const roleTag = (role) => {
      const map = {
        admin: 'danger',
        equipment_engineer: 'primary',
        quality_engineer: 'success',
        reviewer: 'warning',
      }
      return map[role] || 'info'
    }

    const resetForm = () => {
      form.username = ''
      form.password = ''
      form.role = 'equipment_engineer'
      editId.value = null
      isEdit.value = false
      formRef.value?.resetFields()
    }

    const load = async () => {
      loading.value = true
      try {
        users.value = await listUsers()
      } catch (e) {
        ElMessage.error('加载用户列表失败')
      } finally {
        loading.value = false
      }
    }

    const openCreate = () => {
      resetForm()
      dialogVisible.value = true
    }

    const openEdit = (row) => {
      isEdit.value = true
      editId.value = row.id
      form.username = row.username
      form.password = ''
      form.role = row.role || 'equipment_engineer'
      dialogVisible.value = true
    }

    const submit = async () => {
      const valid = await formRef.value.validate().catch(() => false)
      if (!valid) return

      saving.value = true
      try {
        const payload = {
          username: form.username,
          password: form.password,
          role: form.role,
        }
        if (isEdit.value) {
          // If password is empty when editing, pass the current password placeholder
          // The backend requires password; send current password if unchanged
          if (!form.password) {
            payload.password = '__KEEP__'  // placeholder, will be handled by backend
          }
          await updateUser(editId.value, payload)
          ElMessage.success('用户已更新')
        } else {
          await createUser(payload)
          ElMessage.success('用户已创建')
        }
        dialogVisible.value = false
        await load()
      } catch (e) {
        const detail = e.response?.data?.detail
        if (Array.isArray(detail)) {
          ElMessage.error(detail.map((d) => d.msg).join(', '))
        } else {
          ElMessage.error(detail || '操作失败')
        }
      } finally {
        saving.value = false
      }
    }

    const del = async (id) => {
      try {
        await ElMessageBox.confirm('确认删除该用户？此操作不可撤销。', '警告', { type: 'error' })
        await deleteUser(id)
        ElMessage.success('已删除')
        await load()
      } catch (e) { /* cancelled */ }
    }

    onMounted(load)

    return {
      users, loading, saving, dialogVisible, isEdit, formRef, form, rules,
      load, openCreate, openEdit, submit, del, roleLabel, roleTag,
    }
  },
}
</script>
