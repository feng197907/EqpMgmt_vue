<template>
  <div>
    <h2 style="margin:0 0 16px;">审计日志</h2>

    <!-- Filter -->
    <el-card style="margin-bottom:16px;">
      <el-form :inline="true">
        <el-form-item label="用户">
          <el-input v-model="filters.user" placeholder="用户名" clearable style="width:160px;" @keyup.enter="load" />
        </el-form-item>
        <el-form-item label="操作">
          <el-input v-model="filters.action" placeholder="操作类型" clearable style="width:160px;" @keyup.enter="load" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="logs" stripe v-loading="loading" empty-text="暂无审计日志">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="log_time" label="时间" width="170" />
        <el-table-column prop="user" label="用户" width="120" />
        <el-table-column prop="action" label="操作" width="160" />
        <el-table-column prop="target_type" label="目标类型" width="120" />
        <el-table-column prop="target_id" label="目标ID" width="80" />
        <el-table-column prop="details" label="详情" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP" width="140" />
      </el-table>
      <div style="margin-top:16px;text-align:right;">
        <el-pagination
          v-model:current-page="page"
          :page-size="50"
          layout="prev, pager, next"
          :total="total"
          @current-change="load"
        />
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listAuditLogs } from '../api/audit'

export default {
  setup() {
    const logs = ref([])
    const loading = ref(false)
    const page = ref(1)
    const total = ref(0)
    const filters = reactive({ user: '', action: '' })

    const load = async () => {
      loading.value = true
      try {
        const params = { page: page.value, page_size: 50 }
        if (filters.user) params.user = filters.user
        if (filters.action) params.action = filters.action
        const data = await listAuditLogs(params)
        logs.value = data
        total.value = data.length >= 50 ? page.value * 50 + 1 : page.value * 50  // approximate
      } catch (e) {
        ElMessage.error('加载审计日志失败')
      } finally {
        loading.value = false
      }
    }

    onMounted(load)
    return { logs, loading, page, total, filters, load }
  },
}
</script>
