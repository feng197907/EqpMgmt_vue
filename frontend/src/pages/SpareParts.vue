<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h2 style="margin:0;">备件管理</h2>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon> 新增备件
      </el-button>
    </div>

    <!-- Filter -->
    <el-card style="margin-bottom:16px;">
      <el-form :inline="true">
        <el-form-item label="关键字">
          <el-input v-model="filters.search" placeholder="名称/编码/规格/品牌" clearable style="width:200px;" @keyup.enter="load" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="filters.category" placeholder="全部" clearable style="width:140px;">
            <el-option v-for="c in categories" :key="c[0]" :label="c[1]" :value="c[0]" />
          </el-select>
        </el-form-item>
        <el-form-item label="库存">
          <el-select v-model="filters.stock" placeholder="全部" clearable style="width:130px;">
            <el-option label="正常" value="normal" />
            <el-option label="库存不足" value="low" />
            <el-option label="缺货" value="out" />
            <el-option label="超量" value="over" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Table -->
    <el-card>
      <el-table :data="parts" stripe v-loading="loading" empty-text="暂无备件">
        <el-table-column prop="code" label="编码" width="160" />
        <el-table-column prop="name" label="名称" min-width="180" />
        <el-table-column label="分类" width="100">
          <template #default="{ row }">{{ categoryLabel(row.category) }}</template>
        </el-table-column>
        <el-table-column prop="specification" label="规格" width="130" />
        <el-table-column prop="unit" label="单位" width="60" />
        <el-table-column label="当前库存" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.current_stock <= 0 ? '#F56C6C' : row.current_stock <= row.safety_stock_min ? '#E6A23C' : '#333', fontWeight: row.current_stock <= row.safety_stock_min ? 'bold' : 'normal' }">
              {{ row.current_stock }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="safety_stock_min" label="安全库存" width="110" />
        <el-table-column label="均价" width="90">
          <template #default="{ row }">{{ row.weighted_avg_price?.toFixed(2) || '0.00' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openInbound(row)">入库</el-button>
            <el-button size="small" type="warning" @click="openConsume(row)">消耗</el-button>
            <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑备件' : '新增备件'" width="600px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="名称" prop="name">
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-select v-model="form.category" style="width:100%;">
                <el-option v-for="c in categories" :key="c[0]" :label="c[1]" :value="c[0]" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="规格">
              <el-input v-model="form.specification" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单位">
              <el-input v-model="form.unit" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="品牌">
              <el-input v-model="form.brand" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="安全下限" label-width="80px">
              <el-input-number v-model="form.safety_stock_min" :min="0" style="width:100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="安全上限" label-width="80px">
              <el-input-number v-model="form.safety_stock_max" :min="0" style="width:100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="供应商">
          <el-input v-model="form.supplier_name" placeholder="供应商名称" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input v-model="form.supplier_contact" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="form.supplier_phone" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item v-if="isEdit" label="启用状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <!-- Inbound Dialog -->
    <el-dialog v-model="inboundVisible" title="备件入库" width="420px" :close-on-click-modal="false">
      <p style="color:#666;margin-top:0;">备件：{{ currentPart?.code }} {{ currentPart?.name }}</p>
      <el-form :model="inboundForm" label-width="80px">
        <el-form-item label="数量" required>
          <el-input-number v-model="inboundForm.quantity" :min="1" :max="99999" />
        </el-form-item>
        <el-form-item label="单价">
          <el-input-number v-model="inboundForm.unit_price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="批次号">
          <el-input v-model="inboundForm.batch_no" />
        </el-form-item>
        <el-form-item label="日期">
          <el-input v-model="inboundForm.inbound_date" placeholder="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="inboundForm.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inboundVisible = false">取消</el-button>
        <el-button type="primary" :loading="inbounding" @click="doInbound">确认入库</el-button>
      </template>
    </el-dialog>

    <!-- Consume Dialog -->
    <el-dialog v-model="consumeVisible" title="备件消耗" width="420px" :close-on-click-modal="false">
      <p style="color:#666;margin-top:0;">
        备件：{{ currentPart?.code }} {{ currentPart?.name }}
        <span style="color:#999;">（当前库存：{{ currentPart?.current_stock }}）</span>
      </p>
      <el-form :model="consumeForm" label-width="80px">
        <el-form-item label="数量" required>
          <el-input-number v-model="consumeForm.quantity" :min="1" :max="currentPart?.current_stock || 1" />
        </el-form-item>
        <el-form-item label="批次号">
          <el-input v-model="consumeForm.batch_no" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="consumeForm.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="consumeVisible = false">取消</el-button>
        <el-button type="warning" :loading="consuming" @click="doConsume">确认消耗</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listSpareParts, createSparePart, updateSparePart, deleteSparePart,
  inboundSparePart, consumeSparePart,
} from '../api/spare_parts'

const categories = [
  ['mechanical', '机械件'],
  ['electrical', '电气件'],
  ['seal', '密封件'],
  ['filter', '过滤耗材'],
  ['lubricant', '润滑油脂'],
  ['other', '其他'],
]

export default {
  components: { Plus },
  setup() {
    const parts = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const inbounding = ref(false)
    const consuming = ref(false)
    const dialogVisible = ref(false)
    const inboundVisible = ref(false)
    const consumeVisible = ref(false)
    const isEdit = ref(false)
    const editId = ref(null)
    const currentPart = ref(null)
    const formRef = ref(null)

    const filters = reactive({ search: '', category: '', stock: '' })

    const emptyForm = () => ({
      name: '', category: 'other', specification: '', unit: '个', brand: '',
      safety_stock_min: 0, safety_stock_max: 9999,
      supplier_name: '', supplier_contact: '', supplier_phone: '', remark: '',
      is_active: true,
    })
    const form = reactive(emptyForm())

    const inboundForm = reactive({ quantity: 1, unit_price: 0, batch_no: '', inbound_date: '', remark: '' })
    const consumeForm = reactive({ quantity: 1, batch_no: '', remark: '' })

    const rules = {
      name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
      category: [{ required: true, message: '请选择分类', trigger: 'change' }],
    }

    const categoryLabel = (v) => {
      const item = categories.find((c) => c[0] === v)
      return item ? item[1] : v
    }

    const resetForm = () => {
      Object.assign(form, emptyForm())
      editId.value = null
      isEdit.value = false
    }

    const load = async () => {
      loading.value = true
      try {
        const params = {}
        if (filters.search) params.search = filters.search
        if (filters.category) params.category = filters.category
        if (filters.stock) params.stock_filter = filters.stock
        parts.value = await listSpareParts(params)
      } catch (e) {
        ElMessage.error('加载备件列表失败')
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
      form.name = row.name
      form.category = row.category
      form.specification = row.specification || ''
      form.unit = row.unit || '个'
      form.brand = row.brand || ''
      form.safety_stock_min = row.safety_stock_min
      form.safety_stock_max = row.safety_stock_max
      form.supplier_name = row.supplier_name || ''
      form.supplier_contact = row.supplier_contact || ''
      form.supplier_phone = row.supplier_phone || ''
      form.remark = row.remark || ''
      form.is_active = row.is_active
      dialogVisible.value = true
    }

    const submit = async () => {
      const valid = await formRef.value.validate().catch(() => false)
      if (!valid) return
      saving.value = true
      try {
        const payload = { ...form }
        delete payload.is_active
        if (isEdit.value) {
          payload.is_active = form.is_active
          await updateSparePart(editId.value, payload)
          ElMessage.success('备件已更新')
        } else {
          await createSparePart(payload)
          ElMessage.success('备件已创建')
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
        await ElMessageBox.confirm('确认删除该备件？', '警告', { type: 'error' })
        await deleteSparePart(id)
        ElMessage.success('已删除')
        await load()
      } catch (e) { /* cancelled */ }
    }

    const openInbound = (row) => {
      currentPart.value = row
      inboundForm.quantity = 1
      inboundForm.unit_price = row.weighted_avg_price || 0
      inboundForm.batch_no = ''
      inboundForm.inbound_date = new Date().toISOString().split('T')[0]
      inboundForm.remark = ''
      inboundVisible.value = true
    }

    const doInbound = async () => {
      if (inboundForm.quantity <= 0) { ElMessage.warning('请输入数量'); return }
      inbounding.value = true
      try {
        await inboundSparePart(currentPart.value.id, { ...inboundForm })
        ElMessage.success('入库成功')
        inboundVisible.value = false
        await load()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '入库失败')
      } finally {
        inbounding.value = false
      }
    }

    const openConsume = (row) => {
      currentPart.value = row
      consumeForm.quantity = 1
      consumeForm.batch_no = ''
      consumeForm.remark = ''
      consumeVisible.value = true
    }

    const doConsume = async () => {
      if (consumeForm.quantity <= 0) { ElMessage.warning('请输入数量'); return }
      consuming.value = true
      try {
        await consumeSparePart(currentPart.value.id, { ...consumeForm })
        ElMessage.success('消耗记录已提交')
        consumeVisible.value = false
        await load()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '消耗失败')
      } finally {
        consuming.value = false
      }
    }

    onMounted(() => load())

    return {
      parts, loading, saving, inbounding, consuming, filters,
      dialogVisible, inboundVisible, consumeVisible, isEdit, editId,
      currentPart, formRef, form, inboundForm, consumeForm, rules,
      categories, categoryLabel,
      load, openCreate, openEdit, submit, del,
      openInbound, doInbound, openConsume, doConsume,
    }
  },
}
</script>
