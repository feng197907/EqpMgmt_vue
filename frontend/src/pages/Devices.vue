<template>
  <div class="devices-page">
    <!-- 页面头 -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">设备管理</h1>
        <p class="page-subtitle">共 <strong>{{ devices.length }}</strong> 台设备</p>
      </div>
      <div class="page-header-right">
        <el-button type="primary" @click="openCreate">
          <el-icon style="margin-right:4px;"><Plus /></el-icon>新增设备
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-bar-left">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索设备编码或名称..."
          clearable
          style="width: 260px;"
          :prefix-icon="Search"
          @keyup.enter="load"
          @clear="load"
        />
        <el-switch
          v-model="filters.showInactive"
          @change="load"
          inactive-text="仅活跃"
          active-text="含停用"
          style="margin-left:4px;"
        />
      </div>
      <div class="filter-bar-right">
        <el-button @click="load" :loading="loading">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 设备表格 -->
    <el-card class="table-card" :body-style="{ padding: 0 }">
      <el-table
        :data="devices"
        v-loading="loading"
        empty-text="暂无设备数据"
        row-class-name="table-row"
        style="width: 100%;"
        header-cell-class-name="table-header-cell"
      >
        <el-table-column prop="id" label="ID" width="72" align="center">
          <template #default="{ row }">
            <span class="row-id">#{{ row.id }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="device_code" label="设备编码" width="160">
          <template #default="{ row }">
            <span class="device-code">{{ row.device_code }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="device_name" label="设备名称" min-width="200">
          <template #default="{ row }">
            <span class="device-name">{{ row.device_name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="model" label="型号/规格" width="150">
          <template #default="{ row }">
            <span class="row-meta">{{ row.model || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="location" label="存放位置" width="160">
          <template #default="{ row }">
            <span class="row-meta">{{ row.location || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <span class="status-badge" :class="row.status === 'active' ? 'status-badge--active' : 'status-badge--inactive'">
              {{ row.status === 'active' ? '活跃' : '停用' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btn-group">
              <el-button size="small" @click="openEdit(row)" style="padding:4px 10px;">
                <el-icon style="margin-right:3px;"><Edit /></el-icon>编辑
              </el-button>
              <el-button size="small" type="danger" plain @click="del(row.id)" style="padding:4px 10px;">
                <el-icon style="margin-right:3px;"><Delete /></el-icon>删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑设备' : '新增设备'"
      width="480px"
      :close-on-click-modal="false"
      align-center
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="form-vertical">
        <el-row :gutter="16">
          <el-col :span="24">
            <el-form-item label="设备编码" prop="device_code">
              <el-input v-model="form.device_code" placeholder="请输入唯一编码" :disabled="isEdit" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="设备名称" prop="device_name">
              <el-input v-model="form.device_name" placeholder="请输入设备名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="型号/规格">
              <el-input v-model="form.model" placeholder="型号规格" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="存放位置">
              <el-input v-model="form.location" placeholder="存放位置" />
            </el-form-item>
          </el-col>
          <el-col :span="24" v-if="isEdit">
            <el-form-item label="运行状态">
              <el-radio-group v-model="form.status" style="width:100%;">
                <el-radio-button value="active">活跃</el-radio-button>
                <el-radio-button value="inactive">停用</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">
          {{ saving ? '保存中...' : '保 存' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Search, Refresh, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listDevices, createDevice, updateDevice, deleteDevice } from '../api/devices'

export default {
  name: 'DevicesPage',
  components: { Plus, Search, Refresh, Edit, Delete },
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
          data = data.filter(d =>
            (d.device_code?.toLowerCase().includes(kw)) ||
            (d.device_name?.toLowerCase().includes(kw))
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
          ElMessage.success('设备信息已更新')
        } else {
          await createDevice(payload)
          ElMessage.success('设备创建成功')
        }
        dialogVisible.value = false
        await load()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '操作失败，请重试')
      } finally {
        saving.value = false
      }
    }

    const del = async (id) => {
      try {
        await ElMessageBox.confirm('确认要删除该设备吗？此操作不可恢复。', '删除确认', {
          type: 'warning',
          confirmButtonText: '确认删除',
          cancelButtonText: '取消',
          confirmButtonClass: 'el-button--danger',
        })
        await deleteDevice(id)
        ElMessage.success('删除成功')
        await load()
      } catch (e) { /* cancelled */ }
    }

    onMounted(load)

    return {
      devices, loading, saving, filters,
      dialogVisible, isEdit, editId, formRef, form, rules,
      Search,
      load, openCreate, openEdit, submit, del,
    }
  },
}
</script>

<style scoped>
.devices-page {}

/* 筛选栏 */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
  gap: 12px;
}

.filter-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 表格卡片 */
.table-card {}

.row-id {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
}

.device-code {
  font-family: 'Courier New', monospace;
  font-size: 12.5px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  padding: 2px 7px;
  border-radius: 4px;
  font-weight: 600;
}

.device-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.row-meta {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

:deep(.table-header-cell) {
  background: #f8fafc !important;
  font-size: 11.5px !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--el-text-color-secondary) !important;
  border-bottom: 2px solid var(--el-border-color) !important;
}

:deep(.table-row) {
  transition: background 0.1s;
}

:deep(.table-row:hover > td) {
  background: #f0f7ff !important;
}

/* 表单垂直布局 */
.form-vertical :deep(.el-form-item__label) {
  font-weight: 600;
  font-size: 13px;
  color: var(--el-text-color-regular);
  padding-bottom: 4px;
}
</style>
