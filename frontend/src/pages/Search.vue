<template>
  <div>
    <h2 style="margin:0 0 16px;">全局搜索</h2>

    <el-card style="margin-bottom:16px;">
      <el-form :inline="true" @submit.prevent="doSearch">
        <el-form-item>
          <el-input
            v-model="q"
            placeholder="搜索设备编码、名称、文档名称、借阅人..."
            style="width:400px;"
            clearable
            @keyup.enter="doSearch"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-select v-model="type" placeholder="全部" clearable style="width:130px;">
            <el-option label="设备" value="devices" />
            <el-option label="文档" value="documents" />
            <el-option label="借阅" value="borrow_records" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doSearch" :loading="searching">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Results -->
    <div v-if="hasResults">
      <!-- Devices -->
      <el-card v-if="results.devices?.length" style="margin-bottom:16px;">
        <template #header><span style="font-weight:bold;">设备 ({{ results.devices.length }})</span></template>
        <el-table :data="results.devices" stripe size="small">
          <el-table-column prop="device_code" label="编码" width="160" />
          <el-table-column prop="device_name" label="名称" min-width="200" />
          <el-table-column prop="model" label="型号" width="140" />
          <el-table-column prop="location" label="位置" width="160" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- Documents -->
      <el-card v-if="results.documents?.length" style="margin-bottom:16px;">
        <template #header><span style="font-weight:bold;">文档 ({{ results.documents.length }})</span></template>
        <el-table :data="results.documents" stripe size="small">
          <el-table-column prop="doc_name" label="名称" min-width="200" />
          <el-table-column prop="doc_type" label="类型" width="120" />
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="uploaded_by" label="上传者" width="120" />
        </el-table>
      </el-card>

      <!-- Borrow Records -->
      <el-card v-if="results.borrow_records?.length">
        <template #header><span style="font-weight:bold;">借阅记录 ({{ results.borrow_records.length }})</span></template>
        <el-table :data="results.borrow_records" stripe size="small">
          <el-table-column prop="doc_id" label="文档ID" width="80" />
          <el-table-column prop="borrower" label="借阅人" width="120" />
          <el-table-column prop="department" label="部门" width="120" />
          <el-table-column prop="borrow_date" label="日期" width="120" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'borrowed' ? 'warning' : 'success'" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <el-empty v-else-if="searched && !hasResults" description="未找到结果" />
    <el-empty v-else description="输入关键词开始搜索" />
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { search as doSearchApi } from '../api/audit'

export default {
  components: { Search },
  setup() {
    const q = ref('')
    const type = ref('')
    const results = ref({ devices: [], documents: [], borrow_records: [] })
    const searched = ref(false)
    const searching = ref(false)

    const hasResults = computed(() => {
      const r = results.value
      return (r.devices?.length || 0) + (r.documents?.length || 0) + (r.borrow_records?.length || 0) > 0
    })

    const doSearch = async () => {
      if (!q.value.trim()) {
        ElMessage.warning('请输入搜索关键词')
        return
      }
      searching.value = true
      searched.value = true
      try {
        results.value = await doSearchApi(q.value.trim(), type.value || undefined)
      } catch (e) {
        ElMessage.error('搜索失败')
      } finally {
        searching.value = false
      }
    }

    return { q, type, results, searched, searching, hasResults, doSearch }
  },
}
</script>
