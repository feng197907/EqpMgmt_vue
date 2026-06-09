<template>
  <div class="documents-page">
    <!-- 页面头 -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">文档管理</h1>
        <p class="page-subtitle">共 <strong>{{ docs.length }}</strong> 份文档</p>
      </div>
      <div class="page-header-right">
        <el-button @click="$router.push('/approvals')">
          <el-icon style="margin-right:4px;"><Check /></el-icon>审批任务
        </el-button>
        <el-button type="primary" @click="$router.push('/documents/upload')">
          <el-icon style="margin-right:4px;"><Upload /></el-icon>上传文档
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-bar-left">
        <el-input
          v-model="filters.q"
          placeholder="搜索文档名称..."
          clearable
          style="width: 240px;"
          :prefix-icon="Search"
          @keyup.enter="applyFilters"
          @clear="applyFilters"
        />
        <el-select v-model="filters.type" placeholder="文档类型" clearable style="width:140px;" @change="applyFilters">
          <el-option label="手册" value="manual" />
          <el-option label="校准记录" value="calibration" />
          <el-option label="证书" value="certificate" />
        </el-select>
        <el-button type="primary" @click="applyFilters">查询</el-button>
      </div>
      <div class="filter-bar-right">
        <el-button @click="load">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 文档表格 -->
    <el-card :body-style="{ padding: 0 }">
      <el-table
        :data="docs"
        v-loading="loading"
        empty-text="暂无文档"
        header-cell-class-name="table-header-cell"
        row-class-name="table-row"
      >
        <el-table-column prop="id" label="ID" width="72" align="center">
          <template #default="{ row }">
            <span class="row-id">#{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="doc_name" label="文档名称" min-width="200">
          <template #default="{ row }">
            <span class="doc-name">{{ row.doc_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="doc_type" label="类型" width="110" align="center">
          <template #default="{ row }">
            <span class="type-badge" :class="`type-badge--${row.doc_type}`">
              {{ docTypeLabel(row.doc_type) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" align="center">
          <template #default="{ row }">
            <span class="version-tag">v{{ row.version || '1.0' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <span class="status-badge" :class="`status-badge--${statusClass(row.status)}`">
              {{ statusLabel(row.status) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="uploaded_by" label="上传者" width="120" />
        <el-table-column prop="upload_time" label="上传时间" width="160">
          <template #default="{ row }">
            <span class="row-meta">{{ row.upload_time || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btn-group">
              <el-button size="small" @click="downloadDoc(row.id, row.doc_name)" style="padding:4px 8px;">
                下载
              </el-button>
              <el-button
                size="small"
                type="warning"
                plain
                :disabled="row.status !== 'draft'"
                @click="submitApproval(row.id)"
                style="padding:4px 8px;"
              >
                提交审批
              </el-button>
              <el-button size="small" type="danger" plain @click="del(row.id)" style="padding:4px 8px;">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { Upload, Check, Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listDocuments, downloadDocument, submitDocument, deleteDocument
} from '../api/documents'

export default {
  name: 'DocumentsPage',
  components: { Upload, Check, Search, Refresh },
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

    const downloadDoc = async (id, filename) => {
      try {
        await downloadDocument(id, filename)
      } catch (e) {
        ElMessage.error('下载失败，请稍后重试')
      }
    }

    const submitApproval = async (id) => {
      try {
        await ElMessageBox.confirm('确认提交该文档进行审批？', '提交审批', { type: 'warning' })
        await submitDocument(id)
        ElMessage.success('已提交审批')
        await load()
      } catch (e) { /* cancelled */ }
    }

    const del = async (id) => {
      try {
        await ElMessageBox.confirm('确认删除该文档？此操作不可恢复。', '删除确认', {
          type: 'warning',
          confirmButtonText: '确认删除',
          cancelButtonText: '取消',
        })
        await deleteDocument(id)
        ElMessage.success('文档已删除')
        await load()
      } catch (e) { /* cancelled */ }
    }

    const statusClass = (status) => {
      const map = { active: 'active', draft: 'inactive', pending: 'warning', archived: 'inactive' }
      return map[status] || 'inactive'
    }

    const statusLabel = (status) => {
      const map = { active: '已生效', draft: '草稿', pending: '待审批', archived: '已归档' }
      return map[status] || status
    }

    const docTypeLabel = (type) => {
      const map = { manual: '手册', calibration: '校准', certificate: '证书' }
      return map[type] || type
    }

    const applyFilters = () => load()
    onMounted(load)

    return {
      docs, loading, filters, Search,
      applyFilters, load, downloadDoc, submitApproval, del,
      statusClass, statusLabel, docTypeLabel
    }
  },
}
</script>

<style scoped>
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
  gap: 10px;
  flex-wrap: wrap;
}
.filter-bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.row-id {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.doc-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.type-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.type-badge--manual      { background: #dbeafe; color: #1d4ed8; }
.type-badge--calibration { background: #fef3c7; color: #92400e; }
.type-badge--certificate { background: #d1fae5; color: #065f46; }

.version-tag {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  padding: 1px 6px;
  border-radius: 4px;
  font-family: monospace;
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
}

:deep(.table-row:hover > td) {
  background: #f0f7ff !important;
}
</style>
