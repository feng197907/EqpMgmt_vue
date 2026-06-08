<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h2 style="margin:0;">电子签名</h2>
      <el-button type="primary" @click="dialogVisible = true">
        创建签名
      </el-button>
    </div>

    <!-- Filter -->
    <el-card style="margin-bottom:16px;">
      <el-form :inline="true">
        <el-form-item label="记录类型">
          <el-select v-model="filters.record_type" placeholder="全部" clearable style="width:180px;">
            <el-option label="审批" value="approval" />
            <el-option label="维护计划" value="maintenance_plan" />
            <el-option label="文档" value="document" />
            <el-option label="设备变更" value="device_change" />
          </el-select>
        </el-form-item>
        <el-form-item label="记录ID">
          <el-input v-model="filters.record_id" placeholder="记录ID" clearable style="width:120px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="signatures" stripe v-loading="loading" empty-text="暂无签名记录">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="record_type" label="记录类型" width="140">
          <template #default="{ row }">
            <el-tag size="small">{{ recordTypeLabel(row.record_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="record_id" label="记录ID" width="90" />
        <el-table-column prop="signed_by_display" label="签名人" width="140" />
        <el-table-column prop="sign_meaning_label" label="签名含义" width="140" />
        <el-table-column prop="signed_at" label="签名时间" width="170" />
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 签名弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="创建电子签名"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="记录类型" prop="record_type">
          <el-select v-model="form.record_type" style="width:100%;">
            <el-option label="审批" value="approval" />
            <el-option label="维护计划" value="maintenance_plan" />
            <el-option label="文档" value="document" />
            <el-option label="设备变更" value="device_change" />
          </el-select>
        </el-form-item>
        <el-form-item label="记录ID" prop="record_id">
          <el-input-number v-model="form.record_id" :min="1" style="width:100%;" />
        </el-form-item>
        <el-form-item label="签名含义" prop="sign_meaning">
          <el-select v-model="form.sign_meaning" style="width:100%;" @change="onMeaningChange">
            <el-option label="审批通过" value="approved" />
            <el-option label="已审核" value="reviewed" />
            <el-option label="已执行" value="executed" />
            <el-option label="已放行" value="released" />
          </el-select>
        </el-form-item>
        <el-form-item label="确认密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入当前用户密码以确认签名"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">确认签名</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSignatures, createSignature, deleteSignature } from '../api/esign'

export default {
  setup() {
    const signatures = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const dialogVisible = ref(false)
    const formRef = ref(null)

    const filters = reactive({ record_type: '', record_id: '' })
    const form = reactive({
      record_type: '',
      record_id: null,
      sign_meaning: '',
      sign_meaning_label: '',
      password: '',
      remark: '',
    })

    const rules = {
      record_type: [{ required: true, message: '请选择记录类型', trigger: 'change' }],
      record_id: [{ required: true, message: '请输入记录ID', trigger: 'blur' }],
      sign_meaning: [{ required: true, message: '请选择签名含义', trigger: 'change' }],
      password: [{ required: true, message: '请输入确认密码', trigger: 'blur' }],
    }

    const meaningLabelMap = {
      approved: '审批通过',
      reviewed: '已审核',
      executed: '已执行',
      released: '已放行',
    }

    const recordTypeLabel = (type) => {
      const map = {
        approval: '审批',
        maintenance_plan: '维护计划',
        document: '文档',
        device_change: '设备变更',
      }
      return map[type] || type
    }

    const onMeaningChange = (val) => {
      form.sign_meaning_label = meaningLabelMap[val] || val
    }

    const load = async () => {
      loading.value = true
      try {
        const recordId = filters.record_id ? parseInt(filters.record_id, 10) : null
        signatures.value = await getSignatures(filters.record_type || null, recordId)
      } catch (e) {
        ElMessage.error('加载签名记录失败')
      } finally {
        loading.value = false
      }
    }

    const resetForm = () => {
      form.record_type = ''
      form.record_id = null
      form.sign_meaning = ''
      form.sign_meaning_label = ''
      form.password = ''
      form.remark = ''
      formRef.value?.resetFields()
    }

    const submit = async () => {
      const valid = await formRef.value.validate().catch(() => false)
      if (!valid) return

      saving.value = true
      try {
        await createSignature({
          record_type: form.record_type,
          record_id: form.record_id,
          sign_meaning: form.sign_meaning,
          sign_meaning_label: form.sign_meaning_label,
          password: form.password,
          remark: form.remark,
        })
        ElMessage.success('签名已创建')
        dialogVisible.value = false
        resetForm()
        await load()
      } catch (e) {
        const detail = e.response?.data?.detail
        ElMessage.error(detail || '签名创建失败')
      } finally {
        saving.value = false
      }
    }

    const del = async (id) => {
      try {
        await ElMessageBox.confirm('确认删除该签名记录？此操作不可撤销。', '警告', { type: 'error' })
        await deleteSignature(id)
        ElMessage.success('已删除')
        await load()
      } catch (e) { /* cancelled */ }
    }

    onMounted(load)

    return {
      signatures, loading, saving, dialogVisible, formRef,
      filters, form, rules,
      load, submit, del,
      recordTypeLabel, onMeaningChange,
    }
  },
}
</script>
