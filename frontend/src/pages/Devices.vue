<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h2 style="margin:0;">设备管理</h2>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon> 新增设备
      </el-button>
    </div>

    <!-- 筛选区 -->
    <el-card style="margin-bottom:16px;">
      <el-form :inline="true">
        <el-form-item label="关键字">
          <el-input v-model="filters.keyword" placeholder="设备编码/名称" clearable style="width:200px;" @keyup.enter="load" />
        </el-form-item>
        <el-form-item label="显示停用">
          <el-switch v-model="filters.showInactive" @change="load" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 设备表格 -->
    <el-card>
      <el-table :data="devices" stripe v-loading="loading" empty-text="暂无设备">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="device_code" label="设备编码" width="160" />
        <el-table-column prop="device_name" label="设备名称" min-width="200" />
        <el-table-column prop="model" label="型号" width="140" />
        <el-table-column prop="location" label="位置" width="160" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '活跃' : '停用' }}
            </el-tag>
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
      :title="isEdit ? '编辑设备' : '新增设备'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="设备编码" prop="device_code">
          <el-input v-model="form.device_code" placeholder="唯一编码" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="设备名称" prop="device_name">
          <el-input v-model="form.device_name" placeholder="设备名称" />
        </el-form-item>
        <el-form-item label="型号">
          <el-input v-model="form.model" placeholder="型号/规格" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" placeholder="存放位置" />
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态">
          <el-select v-model="form.status" style="width:100%;">
            <el-option label="活跃" value="active" />
            <el-option label="停用" value="inactive" />
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
import { listDevices, createDevice, updateDevice, deleteDevice } from '../api/devices'

export default {
  components: { Plus },
  setup() {
    const devices = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const dialogVisible = ref(false)
    const isEdit = ref(false)
    const editId = ref(null)
    const formRef = ref(null)

    const filters = reactive({ keyword: '', showInactive: false })

    const form = reactive({
      device_code: '',
      device_name: '',
      model: '',
      location: '',
      status: 'active',
    })

    const rules = {
      device_code: [{ required: true, message: '请输入设备编码', trigger: 'blur' }],
      device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
    }

    const resetForm = () => {
      form.device_code = ''
      form.device_name = ''
      form.model = ''
      form.location = ''
      form.status = 'active'
      editId.value = null
      isEdit.value = false
    }

    const load = async () => {
      loading.value = true
      try {
        const params = { show_inactive: filters.showInactive }
        let data = await listDevices(params)
        if (filters.keyword) {
          const kw = filters.keyword.toLowerCase()
          data = data.filter(
            (d) =>
              (d.device_code && d.device_code.toLowerCase().includes(kw)) ||
              (d.device_name && d.device_name.toLowerCase().includes(kw))
          )
        }
        devices.value = data
      } catch (e) {
        ElMessage.error('加载设备列表失败')
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
      form.device_code = row.device_code
      form.device_name = row.device_name
      form.model = row.model || ''
      form.location = row.location || ''
      form.status = row.status || 'active'
      dialogVisible.value = true
    }

    const submit = async () => {
      const valid = await formRef.value.validate().catch(() => false)
      if (!valid) return

      saving.value = true
      try {
        const payload = {
          device_code: form.device_code,
          device_name: form.device_name,
          model: form.model || null,
          location: form.location || null,
        }
        if (isEdit.value) {
          payload.status = form.status
          await updateDevice(editId.value, payload)
          ElMessage.success('设备已更新')
        } else {
          await createDevice(payload)
          ElMessage.success('设备已创建')
        }
        dialogVisible.value = false
        await load()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '操作失败')
      } finally {
        saving.value = false
      }
    }

    const del = async (id) => {
      try {
        await ElMessageBox.confirm('确认删除该设备？', '警告', { type: 'error' })
        await deleteDevice(id)
        ElMessage.success('已删除')
        await load()
      } catch (e) { /* cancelled */ }
    }

    onMounted(load)

    return {
      devices, loading, saving, filters,
      dialogVisible, isEdit, editId, formRef, form, rules,
      load, openCreate, openEdit, submit, del,
    }
  },
}
</script>
