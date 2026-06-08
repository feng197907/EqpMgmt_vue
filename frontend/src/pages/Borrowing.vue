<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h2 style="margin:0;">借阅管理</h2>
      <el-button type="primary" @click="openBorrow">
        <el-icon><Plus /></el-icon> 借阅文档
      </el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="load">
      <el-tab-pane label="全部借阅" name="all" />
      <el-tab-pane label="我的借阅" name="my" />
    </el-tabs>

    <el-card>
      <el-table :data="records" stripe v-loading="loading" empty-text="暂无借阅记录">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="doc_name" label="文档名称" min-width="200" />
        <el-table-column prop="doc_type" label="类型" width="100">
          <template #default="{ row }">{{ docTypeLabel(row.doc_type) }}</template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="70" />
        <el-table-column prop="borrower" label="借阅人" width="120" />
        <el-table-column prop="department" label="部门" width="120" />
        <el-table-column prop="borrow_date" label="借阅日期" width="120" />
        <el-table-column prop="expected_return_date" label="预计归还" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'borrowed' ? 'warning' : 'success'" size="small">
              {{ row.status === 'borrowed' ? '借出' : '已归还' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="actual_return_date" label="实际归还" width="120" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'borrowed'"
              size="small" type="success" @click="doReturn(row.id)"
            >归还</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Borrow Dialog -->
    <el-dialog v-model="borrowVisible" title="借阅文档" width="460px" :close-on-click-modal="false">
      <el-form ref="borrowFormRef" :model="borrowForm" :rules="borrowRules" label-width="100px">
        <el-form-item label="文档" prop="doc_id">
          <el-select v-model="borrowForm.doc_id" filterable placeholder="搜索选择文档" style="width:100%;">
            <el-option
              v-for="d in availableDocs"
              :key="d.id"
              :label="`${d.doc_name} (v${d.version}) - ${d.device_name || ''}`"
              :value="d.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="借阅人" prop="borrower">
          <el-input v-model="borrowForm.borrower" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="borrowForm.department" />
        </el-form-item>
        <el-form-item label="预计归还">
          <el-input v-model="borrowForm.expected_return_date" placeholder="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="borrowForm.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="borrowVisible = false">取消</el-button>
        <el-button type="primary" :loading="borrowing" @click="doBorrow">确认借阅</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listBorrowRecords, myBorrowRecords, borrowDocument, returnDocument, deleteBorrowRecord } from '../api/borrowing'
import { listDocuments } from '../api/documents'

export default {
  components: { Plus },
  setup() {
    const records = ref([])
    const loading = ref(false)
    const borrowing = ref(false)
    const activeTab = ref('all')
    const borrowVisible = ref(false)
    const availableDocs = ref([])
    const borrowFormRef = ref(null)

    const borrowForm = reactive({
      doc_id: null, borrower: '', department: '', expected_return_date: '', remarks: '',
    })

    const borrowRules = {
      doc_id: [{ required: true, message: '请选择文档', trigger: 'change' }],
      borrower: [{ required: true, message: '请输入借阅人', trigger: 'blur' }],
    }

    const docTypeLabel = (type) => ({ manual: '手册', calibration: '校准记录', certificate: '证书' }[type] || type)

    const load = async () => {
      loading.value = true
      try {
        if (activeTab.value === 'my') {
          records.value = await myBorrowRecords()
        } else {
          records.value = await listBorrowRecords()
        }
      } catch (e) {
        ElMessage.error('加载借阅记录失败')
      } finally {
        loading.value = false
      }
    }

    const openBorrow = async () => {
      borrowForm.doc_id = null
      borrowForm.borrower = ''
      borrowForm.department = ''
      borrowForm.expected_return_date = ''
      borrowForm.remarks = ''
      try {
        availableDocs.value = await listDocuments()
      } catch (e) {
        availableDocs.value = []
      }
      borrowVisible.value = true
    }

    const doBorrow = async () => {
      const valid = await borrowFormRef.value.validate().catch(() => false)
      if (!valid) return
      borrowing.value = true
      try {
        await borrowDocument({ ...borrowForm, doc_id: Number(borrowForm.doc_id) })
        ElMessage.success('借阅成功')
        borrowVisible.value = false
        await load()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '借阅失败')
      } finally {
        borrowing.value = false
      }
    }

    const doReturn = async (id) => {
      try {
        await ElMessageBox.confirm('确认归还？', '提示', { type: 'success' })
        await returnDocument(id)
        ElMessage.success('已归还')
        await load()
      } catch (e) { /* cancelled */ }
    }

    const del = async (id) => {
      try {
        await ElMessageBox.confirm('确认删除该借阅记录？', '警告', { type: 'error' })
        await deleteBorrowRecord(id)
        ElMessage.success('已删除')
        await load()
      } catch (e) { /* cancelled */ }
    }

    onMounted(load)

    return {
      records, loading, borrowing, activeTab, borrowVisible,
      availableDocs, borrowFormRef, borrowForm, borrowRules,
      load, openBorrow, doBorrow, doReturn, del, docTypeLabel,
    }
  },
}
</script>
