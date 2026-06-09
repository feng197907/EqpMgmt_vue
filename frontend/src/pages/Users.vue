<template>
  <div class="users-page">
    <!-- ── 标签切换 ──────────────────────────────── -->
    <el-tabs v-model="activeTab" class="users-tabs">
      <!-- ① 用户管理 -->
      <el-tab-pane name="users">
        <template #label>
          <span class="tab-label">
            <el-icon><User /></el-icon>
            用户管理
          </span>
        </template>

        <div class="panel-header">
          <h2 class="panel-title">用户管理</h2>
          <el-button type="primary" @click="openCreate">
            <el-icon><Plus /></el-icon> 新增用户
          </el-button>
        </div>

        <el-card class="data-card">
          <el-table :data="users" stripe v-loading="loading" empty-text="暂无用户">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="username" label="用户名" min-width="180" />
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
      </el-tab-pane>

      <!-- ② 密码重置申请 -->
      <el-tab-pane name="resets">
        <template #label>
          <span class="tab-label">
            <el-icon><Key /></el-icon>
            密码重置申请
            <el-badge
              v-if="pendingCount > 0"
              :value="pendingCount"
              :max="99"
              class="tab-badge"
            />
          </span>
        </template>

        <div class="panel-header">
          <h2 class="panel-title">密码重置申请</h2>
          <div class="panel-header-actions">
            <el-radio-group v-model="resetFilter" size="small" @change="loadResets">
              <el-radio-button value="">全部</el-radio-button>
              <el-radio-button value="pending">待处理</el-radio-button>
              <el-radio-button value="completed">已完成</el-radio-button>
              <el-radio-button value="cancelled">已取消</el-radio-button>
            </el-radio-group>
            <el-button size="small" :icon="Refresh" circle @click="loadResets" />
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!resetsLoading && resetList.length === 0" class="empty-resets">
          <el-icon size="48" color="#cbd5e1"><CircleCheck /></el-icon>
          <p>暂无{{ resetFilter === 'pending' ? '待处理的' : '' }}密码重置申请</p>
        </div>

        <div v-else class="reset-list" v-loading="resetsLoading">
          <el-card
            v-for="req in resetList"
            :key="req.id"
            class="reset-card"
            :class="'reset-card--' + req.status"
          >
            <div class="reset-card-body">
              <!-- 左侧信息 -->
              <div class="reset-card-info">
                <div class="reset-card-top">
                  <span class="reset-card-username">
                    <el-icon><User /></el-icon>
                    {{ req.username }}
                  </span>
                  <el-tag
                    :type="statusTag(req.status)"
                    size="small"
                    class="reset-status-tag"
                  >
                    {{ statusLabel(req.status) }}
                  </el-tag>
                </div>
                <div class="reset-card-meta">
                  <span><el-icon><Clock /></el-icon> 申请时间：{{ formatTime(req.requested_at) }}</span>
                  <span v-if="req.ip_address"><el-icon><Location /></el-icon> IP：{{ req.ip_address }}</span>
                  <span v-if="req.processed_by">
                    <el-icon><UserFilled /></el-icon>
                    处理人：{{ req.processed_by }}（{{ formatTime(req.processed_at) }}）
                  </span>
                </div>
              </div>

              <!-- 右侧操作 -->
              <div class="reset-card-actions" v-if="req.status === 'pending'">
                <el-button
                  type="primary"
                  size="small"
                  @click="openResetDialog(req)"
                >
                  <el-icon><Key /></el-icon>
                  重置密码
                </el-button>
                <el-button
                  type="info"
                  size="small"
                  plain
                  @click="cancelReset(req.id)"
                >
                  忽略
                </el-button>
              </div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- ── 新增/编辑用户弹窗 ─────────────────────── -->
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

    <!-- ── 密码重置处理弹窗 ─────────────────────── -->
    <el-dialog
      v-model="resetDialogVisible"
      title="重置用户密码"
      width="460px"
      :close-on-click-modal="false"
      @closed="resetDialogClosed"
    >
      <!-- 输入新密码 -->
      <div v-if="!resetResult">
        <div class="reset-dialog-tip">
          <el-icon size="18" color="#f59e0b"><WarningFilled /></el-icon>
          <span>
            即将重置用户 <strong>{{ currentReset?.username }}</strong> 的密码。<br/>
            可自定义新密码，留空则系统自动生成随机密码。
          </span>
        </div>
        <el-form :model="resetForm" ref="resetFormRef" label-width="80px" style="margin-top:16px;">
          <el-form-item label="新密码">
            <el-input
              v-model="resetForm.new_password"
              type="password"
              show-password
              placeholder="留空自动生成随机密码"
              clearable
            />
            <div class="reset-input-tip">至少 6 位，支持字母、数字、特殊字符</div>
          </el-form-item>
        </el-form>
      </div>

      <!-- 重置成功展示新密码 -->
      <div v-else class="reset-success-wrap">
        <el-icon size="40" color="#22c55e"><CircleCheck /></el-icon>
        <h3 class="reset-success-title">密码重置成功</h3>
        <p class="reset-success-sub">用户 <strong>{{ currentReset?.username }}</strong> 的新密码为：</p>
        <div class="reset-new-password">
          <span class="reset-password-text">{{ resetResult }}</span>
          <el-button
            link
            type="primary"
            size="small"
            @click="copyPassword"
            style="margin-left:8px;"
          >
            <el-icon><CopyDocument /></el-icon>
            复制
          </el-button>
        </div>
        <p class="reset-success-note">
          <el-icon><InfoFilled /></el-icon>
          请将新密码告知用户，用户首次登录后建议修改密码。
        </p>
      </div>

      <template #footer>
        <div v-if="!resetResult">
          <el-button @click="resetDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="resetSaving" @click="confirmReset">
            {{ resetSaving ? '处理中...' : '确认重置' }}
          </el-button>
        </div>
        <div v-else>
          <el-button type="primary" @click="resetDialogVisible = false" style="min-width:120px;">
            完成
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import {
  Plus, User, Key, Refresh, CircleCheck, Clock,
  Location, UserFilled, WarningFilled, InfoFilled, CopyDocument
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listUsers, createUser, updateUser, deleteUser } from '../api/users'
import api from '../api/auth'

export default {
  components: {
    Plus, User, Key, Refresh, CircleCheck, Clock,
    Location, UserFilled, WarningFilled, InfoFilled, CopyDocument
  },
  setup() {
    // ── 标签 ───────────────────
    const activeTab = ref('users')

    // ── 用户管理 ───────────────────
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
      try { users.value = await listUsers() }
      catch { ElMessage.error('加载用户列表失败') }
      finally { loading.value = false }
    }

    const openCreate = () => { resetForm(); dialogVisible.value = true }
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
        const payload = { username: form.username, password: form.password, role: form.role }
        if (isEdit.value) {
          if (!form.password) payload.password = '__KEEP__'
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
      } catch { /* cancelled */ }
    }

    // ── 密码重置申请 ───────────────────
    const resetList = ref([])
    const resetsLoading = ref(false)
    const resetFilter = ref('pending')
    const currentReset = ref(null)
    const resetDialogVisible = ref(false)
    const resetSaving = ref(false)
    const resetResult = ref('')    // 重置成功后存放新密码
    const resetFormRef = ref(null)
    const resetFormData = reactive({ new_password: '' })

    const pendingCount = computed(() =>
      resetList.value.filter(r => r.status === 'pending').length
    )

    const loadResets = async () => {
      resetsLoading.value = true
      try {
        const params = resetFilter.value ? { status: resetFilter.value } : {}
        const res = await api.get('/api/v1/password/resets', { params })
        resetList.value = res.data
      } catch {
        ElMessage.error('加载密码重置申请失败')
      } finally {
        resetsLoading.value = false
      }
    }

    const statusLabel = (s) => ({ pending: '待处理', completed: '已完成', cancelled: '已取消', expired: '已过期' }[s] || s)
    const statusTag = (s) => ({ pending: 'warning', completed: 'success', cancelled: 'info', expired: 'danger' }[s] || '')

    const formatTime = (t) => {
      if (!t) return '—'
      try {
        return new Date(t).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
      } catch { return t }
    }

    const openResetDialog = (req) => {
      currentReset.value = req
      resetFormData.new_password = ''
      resetResult.value = ''
      resetDialogVisible.value = true
    }

    const resetDialogClosed = () => {
      resetResult.value = ''
      resetFormData.new_password = ''
    }

    const confirmReset = async () => {
      if (resetFormData.new_password && resetFormData.new_password.length < 6) {
        ElMessage.warning('密码至少 6 位')
        return
      }
      resetSaving.value = true
      try {
        const payload = { new_password: resetFormData.new_password || null }
        const res = await api.post(
          `/api/v1/password/resets/${currentReset.value.id}/reset`,
          payload
        )
        resetResult.value = res.data.new_password
        ElMessage.success('密码重置成功')
        await loadResets()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '重置失败')
      } finally {
        resetSaving.value = false
      }
    }

    const cancelReset = async (id) => {
      try {
        await ElMessageBox.confirm('确认忽略（取消）该密码重置申请？', '提示', { type: 'warning' })
        await api.post(`/api/v1/password/resets/${id}/cancel`)
        ElMessage.success('已取消该申请')
        await loadResets()
      } catch { /* cancelled */ }
    }

    const copyPassword = () => {
      navigator.clipboard?.writeText(resetResult.value)
        .then(() => ElMessage.success('已复制到剪贴板'))
        .catch(() => ElMessage.info('请手动复制密码'))
    }

    onMounted(() => {
      load()
      // loadResets 仅 admin 才有权限，路由守卫已拦截非 admin 访问此页面
      // 但作为双重保护，此处也加角色判断
      try {
        const token = localStorage.getItem('access_token')
        const payload = JSON.parse(atob(token.split('.')[1]))
        if (payload.role === 'admin') loadResets()
      } catch {
        // token 解析失败时跳过
      }
    })

    return {
      // tab
      activeTab,
      // users
      users, loading, saving, dialogVisible, isEdit, formRef, form, rules,
      load, openCreate, openEdit, submit, del, roleLabel, roleTag,
      // resets
      resetList, resetsLoading, resetFilter, pendingCount,
      currentReset, resetDialogVisible, resetSaving, resetResult,
      resetFormRef, resetForm: resetFormData,
      loadResets, statusLabel, statusTag, formatTime,
      openResetDialog, resetDialogClosed, confirmReset, cancelReset, copyPassword,
      // icons
      Plus, User, Key, Refresh, CircleCheck, Clock,
      Location, UserFilled, WarningFilled, InfoFilled, CopyDocument,
    }
  },
}
</script>

<style scoped>
.users-page {}

/* ── 标签页 ─────────────────────── */
:deep(.users-tabs .el-tabs__header) {
  margin-bottom: 0;
}

:deep(.users-tabs .el-tabs__content) {
  padding-top: 16px;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.tab-badge {
  margin-left: 2px;
}

:deep(.tab-badge .el-badge__content) {
  font-size: 10px !important;
  padding: 0 4px !important;
  height: 16px !important;
  line-height: 16px !important;
}

/* ── 面板头 ─────────────────────── */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.panel-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.data-card {
  border-radius: 8px;
}

/* ── 空状态 ─────────────────────── */
.empty-resets {
  text-align: center;
  padding: 48px 0;
  color: #94a3b8;
}
.empty-resets p {
  margin-top: 12px;
  font-size: 14px;
}

/* ── 申请列表卡片 ─────────────────── */
.reset-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 80px;
}

.reset-card {
  border-radius: 8px;
  border-left: 4px solid transparent;
  transition: box-shadow 0.15s;
}
.reset-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.reset-card--pending {
  border-left-color: #f59e0b;
}
.reset-card--completed {
  border-left-color: #22c55e;
}
.reset-card--cancelled {
  border-left-color: #94a3b8;
}

.reset-card-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.reset-card-info {
  flex: 1;
  min-width: 0;
}

.reset-card-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.reset-card-username {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.reset-status-tag {
  flex-shrink: 0;
}

.reset-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #64748b;
}

.reset-card-meta span {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.reset-card-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* ── 重置弹窗 ─────────────────────── */
.reset-dialog-tip {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 13.5px;
  color: #92400e;
  line-height: 1.7;
}

.reset-input-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}

/* 成功展示 */
.reset-success-wrap {
  text-align: center;
  padding: 8px 0 4px;
}

.reset-success-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 12px 0 8px;
}

.reset-success-sub {
  font-size: 14px;
  color: #475569;
  margin-bottom: 12px;
}

.reset-new-password {
  display: inline-flex;
  align-items: center;
  background: #f1f5f9;
  border-radius: 8px;
  padding: 8px 16px;
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
}

.reset-password-text {
  font-size: 20px;
  font-weight: 700;
  color: #1a56db;
  letter-spacing: 2px;
  font-family: 'Courier New', monospace;
}

.reset-success-note {
  font-size: 12px;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
</style>
