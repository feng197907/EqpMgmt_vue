<template>
  <div>
    <h2 style="margin:0 0 16px;">审批任务</h2>

    <el-card>
      <el-table :data="requests" stripe v-loading="loading" empty-text="暂无待审批任务">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="doc_id" label="文档ID" width="80" />
        <el-table-column prop="doc_name" label="文档名称" min-width="200" />
        <el-table-column prop="created_by" label="提交者" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'pending' ? 'warning' : 'info'" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" type="success" @click="approve(row.id)">
              通过
            </el-button>
            <el-button size="small" type="danger" @click="reject(row.id)">
              拒绝
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/auth'

export default {
  setup() {
    const requests = ref([])
    const loading = ref(false)

    const load = async () => {
      loading.value = true
      try {
        const res = await api.get('/api/v1/approvals/')
        requests.value = res.data
      } catch (e) {
        ElMessage.error('加载审批列表失败')
      } finally {
        loading.value = false
      }
    }

    const approve = async (id) => {
      try {
        await ElMessageBox.confirm('确认通过该审批？', '提示', { type: 'success' })
        await api.post(`/api/v1/approvals/${id}/approve`)
        ElMessage.success('审批已通过')
        await load()
      } catch (e) { /* cancelled */ }
    }

    const reject = async (id) => {
      try {
        await ElMessageBox.confirm('确认拒绝该审批？', '警告', { type: 'error' })
        await api.post(`/api/v1/approvals/${id}/reject`)
        ElMessage.success('已拒绝')
        await load()
      } catch (e) { /* cancelled */ }
    }

    const statusLabel = (s) => ({ pending: '待审批', approved: '已通过', rejected: '已拒绝' }[s] || s)

    onMounted(load)

    return { requests, loading, approve, reject, statusLabel }
  },
}
</script>
