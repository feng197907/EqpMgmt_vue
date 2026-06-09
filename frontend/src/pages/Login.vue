<template>
  <div class="login-shell">
    <!-- 左侧装饰区 -->
    <div class="login-brand">
      <div class="login-brand-inner">
        <div class="login-brand-logo">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
            <rect x="2" y="2" width="9" height="9" rx="1.5" fill="#60a5fa"/>
            <rect x="13" y="2" width="9" height="9" rx="1.5" fill="#60a5fa" opacity="0.6"/>
            <rect x="2" y="13" width="9" height="9" rx="1.5" fill="#60a5fa" opacity="0.6"/>
            <rect x="13" y="13" width="9" height="9" rx="1.5" fill="#60a5fa" opacity="0.3"/>
          </svg>
        </div>
        <h1 class="login-brand-name">设备管理系统</h1>
        <p class="login-brand-desc">Device Management System</p>

        <div class="login-features">
          <div class="login-feature-item" v-for="f in features" :key="f.text">
            <div class="login-feature-dot"></div>
            <span>{{ f.text }}</span>
          </div>
        </div>

        <!-- 装饰格栅 -->
        <div class="login-brand-grid" aria-hidden="true">
          <div v-for="i in 64" :key="i" class="grid-dot"></div>
        </div>
      </div>
    </div>

    <!-- 右侧登录区 -->
    <div class="login-form-area">
      <div class="login-form-card">
        <div class="login-form-header">
          <h2>欢迎登录</h2>
          <p>请输入账号和密码</p>
        </div>

        <el-form
          :model="form"
          ref="formRef"
          class="login-form"
          @keyup.enter="onSubmit"
        >
          <div class="login-field">
            <label class="login-label">用户名</label>
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              size="large"
              clearable
              :prefix-icon="User"
            />
          </div>

          <div class="login-field">
            <label class="login-label">密码</label>
            <el-input
              v-model="form.password"
              placeholder="请输入密码"
              size="large"
              show-password
              :prefix-icon="Lock"
            />
          </div>

          <el-alert
            v-if="error"
            :title="error"
            type="error"
            show-icon
            :closable="false"
            style="margin-bottom: 16px; border-radius: 8px;"
          />

          <el-button
            type="primary"
            size="large"
            class="login-submit-btn"
            :loading="loading"
            @click="onSubmit"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form>

        <!-- 忘记密码链接 -->
        <div class="login-forgot">
          <el-button link type="primary" class="forgot-link" @click="forgotVisible = true">
            <el-icon class="forgot-icon"><QuestionFilled /></el-icon>
            忘记密码？
          </el-button>
        </div>

        <div class="login-footer">
          <span>DMS v2.0</span>
          <span class="login-footer-dot">·</span>
          <span>工业设备管理平台</span>
        </div>
      </div>
    </div>

    <!-- ── 忘记密码弹窗 ────────────────────────────────── -->
    <el-dialog
      v-model="forgotVisible"
      title="忘记密码"
      width="420px"
      :close-on-click-modal="false"
      class="forgot-dialog"
      @closed="resetForgotForm"
    >
      <!-- 未提交状态 -->
      <div v-if="!forgotSubmitted" class="forgot-dialog-body">
        <div class="forgot-dialog-icon">
          <el-icon size="36" color="#1a56db"><Lock /></el-icon>
        </div>
        <p class="forgot-dialog-tip">
          请输入您的登录用户名，系统将通知管理员为您重置密码。<br/>
          重置完成后请联系管理员获取新密码。
        </p>

        <el-form ref="forgotFormRef" :model="forgotForm" :rules="forgotRules">
          <el-form-item prop="username">
            <el-input
              v-model="forgotForm.username"
              placeholder="请输入用户名"
              size="large"
              clearable
              :prefix-icon="User"
              @keyup.enter="submitForgot"
            />
          </el-form-item>
        </el-form>

        <el-alert
          v-if="forgotError"
          :title="forgotError"
          type="error"
          show-icon
          :closable="false"
          style="margin-bottom: 0; border-radius: 8px;"
        />
      </div>

      <!-- 提交成功状态 -->
      <div v-else class="forgot-success-body">
        <div class="forgot-success-icon">
          <el-icon size="48" color="#22c55e"><CircleCheck /></el-icon>
        </div>
        <h3 class="forgot-success-title">申请已提交</h3>
        <p class="forgot-success-tip">
          您的密码重置申请已成功提交。<br/>
          请联系系统管理员，告知其您的用户名：<br/>
          <strong class="forgot-success-username">{{ forgotForm.username }}</strong>
        </p>
        <p class="forgot-success-note">
          管理员处理后将为您提供新密码，请妥善保管。
        </p>
      </div>

      <!-- 统一 footer：根据 forgotSubmitted 状态切换按钮 -->
      <template #footer>
        <div v-if="!forgotSubmitted">
          <el-button @click="forgotVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="forgotLoading"
            @click="submitForgot"
            style="min-width: 100px;"
          >
            {{ forgotLoading ? '提交中...' : '提交申请' }}
          </el-button>
        </div>
        <div v-else>
          <el-button type="primary" @click="forgotVisible = false" style="min-width: 120px;">
            我知道了
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import api, { login } from '../api/auth'
import { User, Lock, QuestionFilled, CircleCheck } from '@element-plus/icons-vue'

export default {
  name: 'LoginPage',
  components: { User, Lock, QuestionFilled, CircleCheck },
  setup() {
    const form = ref({ username: '', password: '' })
    const error = ref('')
    const loading = ref(false)
    const router = useRouter()

    // 忘记密码相关
    const forgotVisible = ref(false)
    const forgotSubmitted = ref(false)
    const forgotLoading = ref(false)
    const forgotError = ref('')
    const forgotFormRef = ref(null)
    const forgotForm = reactive({ username: '' })
    const forgotRules = {
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    }

    const features = [
      { text: '设备全生命周期管理' },
      { text: '文档智能审批流程' },
      { text: '备件库存实时预警' },
      { text: '完整操作审计追踪' },
    ]

    const onSubmit = async () => {
      if (!form.value.username || !form.value.password) {
        error.value = '请输入用户名和密码'
        return
      }
      error.value = ''
      loading.value = true
      try {
        const res = await login(form.value.username, form.value.password)
        const token = res.access_token
        const refresh = res.refresh_token
        localStorage.setItem('access_token', token)
        if (refresh) localStorage.setItem('refresh_token', refresh)
        const authHeader = `Bearer ${token}`
        axios.defaults.headers.common['Authorization'] = authHeader
        api.defaults.headers.common['Authorization'] = authHeader
        router.push('/dashboard')
      } catch (e) {
        const detail = e.response?.data?.detail
        if (e.code === 'ERR_NETWORK' || !e.response) {
          error.value = '无法连接到后端服务，请确认后端已启动'
        } else {
          error.value = detail || '用户名或密码错误'
        }
      } finally {
        loading.value = false
      }
    }

    const resetForgotForm = () => {
      forgotForm.username = ''
      forgotError.value = ''
      forgotSubmitted.value = false
      forgotFormRef.value?.resetFields()
    }

    const submitForgot = async () => {
      const valid = await forgotFormRef.value?.validate().catch(() => false)
      if (!valid) return

      forgotError.value = ''
      forgotLoading.value = true
      try {
        await axios.post(
          `${import.meta.env.VITE_API_BASE || ''}/api/v1/password/request-reset`,
          { username: forgotForm.username }
        )
        forgotSubmitted.value = true
      } catch (e) {
        const detail = e.response?.data?.detail
        if (e.code === 'ERR_NETWORK' || !e.response) {
          forgotError.value = '无法连接服务器，请稍后重试'
        } else {
          forgotError.value = detail || '提交失败，请稍后重试'
        }
      } finally {
        forgotLoading.value = false
      }
    }

    return {
      form, error, loading, features, onSubmit,
      forgotVisible, forgotSubmitted, forgotLoading, forgotError,
      forgotFormRef, forgotForm, forgotRules,
      resetForgotForm, submitForgot,
      User, Lock, QuestionFilled, CircleCheck,
    }
  },
}
</script>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: flex;
  background: #f1f5f9;
}

/* ── 左侧品牌区 ──────────────────── */
.login-brand {
  flex: 1;
  background: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  min-height: 100vh;
}

@media (max-width: 768px) {
  .login-brand { display: none; }
  .login-form-area { flex: 1; }
}

.login-brand-inner {
  position: relative;
  z-index: 2;
  padding: 40px;
  max-width: 420px;
}

.login-brand-logo {
  width: 64px;
  height: 64px;
  background: rgba(26, 86, 219, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  border: 1px solid rgba(96, 165, 250, 0.2);
}

.login-brand-name {
  font-size: 28px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0 0 6px;
  letter-spacing: -0.5px;
}

.login-brand-desc {
  font-size: 14px;
  color: #475569;
  margin: 0 0 40px;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.login-features {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.login-feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #94a3b8;
}

.login-feature-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #1a56db;
  flex-shrink: 0;
}

/* 装饰格栅 */
.login-brand-grid {
  position: absolute;
  right: -10px;
  bottom: -10px;
  width: 200px;
  height: 200px;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
  z-index: 1;
  opacity: 0.15;
}

.grid-dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #60a5fa;
}

/* 左侧大圆圈装饰 */
.login-brand::before {
  content: '';
  position: absolute;
  top: -150px;
  right: -150px;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  border: 1px solid rgba(26, 86, 219, 0.2);
}
.login-brand::after {
  content: '';
  position: absolute;
  bottom: -100px;
  left: -100px;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  border: 1px solid rgba(26, 86, 219, 0.1);
}

/* ── 右侧表单区 ──────────────────── */
.login-form-area {
  width: 480px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fff;
}

.login-form-card {
  width: 100%;
  max-width: 360px;
}

.login-form-header {
  margin-bottom: 32px;
}

.login-form-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 6px;
  letter-spacing: -0.5px;
}

.login-form-header p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.login-field {
  margin-bottom: 18px;
}

.login-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 6px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px !important;
  padding: 0 12px !important;
}

:deep(.el-input--large .el-input__inner) {
  font-size: 14px;
}

.login-submit-btn {
  width: 100%;
  height: 44px;
  border-radius: 8px !important;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 2px;
  background: #1a56db !important;
  border-color: #1a56db !important;
  margin-top: 8px;
}

.login-submit-btn:hover {
  background: #1445b5 !important;
  border-color: #1445b5 !important;
}

/* 忘记密码链接 */
.login-forgot {
  margin-top: 16px;
  text-align: center;
}

.forgot-link {
  font-size: 13px;
  color: #64748b !important;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.forgot-link:hover {
  color: #1a56db !important;
}

.forgot-icon {
  font-size: 13px;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.login-footer-dot { color: #cbd5e1; }

/* ── 忘记密码弹窗内容 ───────────────── */
.forgot-dialog-body {
  padding: 8px 4px 0;
  text-align: center;
}

.forgot-dialog-icon {
  margin-bottom: 16px;
  display: flex;
  justify-content: center;
}

.forgot-dialog-tip {
  font-size: 14px;
  color: #475569;
  line-height: 1.7;
  margin-bottom: 20px;
  text-align: left;
}

/* 成功状态 */
.forgot-success-body {
  text-align: center;
  padding: 16px 4px 8px;
}

.forgot-success-icon {
  margin-bottom: 16px;
  display: flex;
  justify-content: center;
}

.forgot-success-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 12px;
}

.forgot-success-tip {
  font-size: 14px;
  color: #475569;
  line-height: 1.8;
  margin-bottom: 8px;
}

.forgot-success-username {
  display: inline-block;
  margin-top: 6px;
  font-size: 16px;
  color: #1a56db;
  background: #eff6ff;
  border-radius: 6px;
  padding: 2px 12px;
  letter-spacing: 1px;
}

.forgot-success-note {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
}
</style>
