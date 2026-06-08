<template>
  <div>
    <h2>Documents</h2>
    <div style="margin-bottom:10px">
      <router-link to="/documents/upload">上传文档</router-link>
      <router-link to="/approvals" style="margin-left:12px">审批任务</router-link>
    </div>

    <div style="margin-bottom:8px">
      <label>类型筛选：</label>
      <select v-model="filters.type">
        <option value="">全部</option>
        <option value="manual">手册</option>
        <option value="calibration">校准记录</option>
        <option value="certificate">证书</option>
      </select>
      <label style="margin-left:8px">关键字：</label>
      <input v-model="filters.q" @keyup.enter="applyFilters" />
      <button @click="applyFilters">查询</button>
    </div>

    <table>
      <thead><tr><th>ID</th><th>名称</th><th>类型</th><th>版本</th><th>状态</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="doc in pageDocs" :key="doc.id">
          <td>{{ doc.id }}</td>
          <td>{{ doc.doc_name }}</td>
          <td>{{ doc.doc_type }}</td>
          <td>{{ doc.version }}</td>
          <td>{{ doc.status }}</td>
          <td>
            <a :href="downloadUrl(doc.id)" target="_blank">下载</a>
            <button @click="submit(doc.id)" :disabled="doc.status !== 'draft'">提交审批</button>
            <button @click="del(doc.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div style="margin-top:8px">
      <button @click="prevPage" :disabled="page===1">上一页</button>
      <span> 第 {{ page }} / {{ totalPages }} 页 </span>
      <button @click="nextPage" :disabled="page===totalPages">下一页</button>
      <select v-model.number="pageSize" style="margin-left:8px" @change="onPageSizeChange">
        <option :value="5">5</option>
        <option :value="10">10</option>
        <option :value="20">20</option>
      </select>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { listDocuments, downloadUrl, submitDocument, deleteDocument } from '../api/documents'

export default {
  setup() {
    const docs = ref([])
    const page = ref(1)
    const pageSize = ref(10)
    const filters = ref({ q: '', type: '' })

    const load = async () => {
      try {
        docs.value = await listDocuments({ q: filters.value.q, doc_type: filters.value.type })
      } catch (e) {
        alert('加载文档失败')
      }
    }

    const downloadUrlFn = (id) => downloadUrl(id)

    const submit = async (id) => {
      if (!confirm('确认提交审批？')) return
      await submitDocument(id)
      alert('已提交审批')
      await load()
    }

    const del = async (id) => {
      if (!confirm('确认删除？')) return
      await deleteDocument(id)
      alert('已删除')
      await load()
    }

    onMounted(load)

    const totalPages = computed(() => Math.max(1, Math.ceil((docs.value || []).length / pageSize.value)))
    const pageDocs = computed(() => {
      const start = (page.value - 1) * pageSize.value
      return (docs.value || []).slice(start, start + pageSize.value)
    })
    const prevPage = () => { if (page.value>1) page.value-- }
    const nextPage = () => { if (page.value<totalPages.value) page.value++ }
    const onPageSizeChange = () => { page.value = 1 }
    const applyFilters = () => { page.value = 1; load() }

    return { docs, downloadUrl: downloadUrlFn, submit, del, page, pageSize, pageDocs, totalPages, prevPage, nextPage, onPageSizeChange, filters, applyFilters }
  }
}
</script>
