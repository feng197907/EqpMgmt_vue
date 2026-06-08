<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h2 style="margin:0;">文档管理</h2>
      <el-space>
        <el-button type="primary" @click="$router.push('/documents/upload')">
          <el-icon><Upload /></el-icon> 上传文档
        </el-button>
        <el-button @click="$router.push('/approvals')">审批任务</el-button>
      </el-space>
    </div>

    <!-- 筛选区 -->
    <el-card style="margin-bottom:16px;">
      <el-form :inline="true">
        <el-form-item label="关键字">
          <el-input v-model="filters.q" placeholder="文档名称" clearable @keyup.enter="applyFilters" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.type" placeholder="全部" clearable style="width:140px;">
            <el-option label="手册" value="manual" />
            <el-option label="校准记录" value="calibration" />
            <el-option label="证书" value="certificate" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="applyFilters">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 文档表格 -->
    <el-card>
      <el-table :data="docs" stripe style="width:100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="doc_name" label="文档名称" min-width="200" />
        <el-table-column prop="doc_type" label="类型" width="120" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="uploaded_by" label="上传者" width="120" />
        <el-table-column prop="upload_time" label="上传时间" width="160" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="downloadDoc(row.id)">下载</el-button>
            <el-button
              size="small"
              type="warning"
              :disabled="row.status !== 'draft'"
              @click="submit(row.id)"
            >提交审批</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listDocuments,
  downloadUrl,
  submitDocument,
  deleteDocument,
} from '../api/documents'

export default {
  components: { Upload },
  setup() {
    const docs = ref([])
    const loading = ref(false)
    const filters = ref({ q: '', type: '' })

    const load = async () => {
      loading.value = true
      try {
        const params = {}
        if (filters.value.q) params.q = filters.value.q
        if (filters.value.type) params.doc_type = filters.value.type
        docs.value = await listDocuments(params)
      } catch (e) {
        console.error('加载文档失败', e)
      } finally {
        loading.value = false
      }
    }

    const downloadDoc = (id) => {
      window.open(downloadUrl(id), '_blank')
    }

    const submit = async (id) => {
      try {
        await ElMessageBox.confirm('确认提交审批？', '提示', { type: 'warning' })
        await submitDocument(id)
        ElMessage.success('已提交审批')
        await load()
      } catch (e) { /* cancelled or error */ }
    }

    const del = async (id) => {
      try {
        await ElMessageBox.confirm('确认删除该文档？', '警告', { type: 'error' })
        await deleteDocument(id)
        ElMessage.success('已删除')
        await load()
      } catch (e) { /* cancelled */ }
    }

    const statusType = (status) => {
      const map = { active: 'success', draft: 'info', pending: 'warning', archived: '' }
      return map[status] || 'info'
    }

    const applyFilters = () => load()

    onMounted(load)

    return { docs, loading, filters, applyFilters, downloadDoc, submit, del, statusType }
  },
}
</script>
