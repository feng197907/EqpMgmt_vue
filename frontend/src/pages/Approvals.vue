<template>
  <div>
    <h2>审批任务</h2>
    <table>
      <thead><tr><th>ID</th><th>文档ID</th><th>文档名</th><th>状态</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="r in requests" :key="r.id">
          <td>{{ r.id }}</td>
          <td>{{ r.doc_id }}</td>
          <td>{{ r.doc_name }}</td>
          <td>{{ r.status }}</td>
          <td>
            <button @click="approve(r.id)">通过</button>
            <button @click="reject(r.id)">拒绝</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '../api/auth'

export default {
  setup(){
    const requests = ref([])
    const load = async ()=>{
      const res = await api.get('/api/v1/approvals/')
      requests.value = res.data
    }
    const approve = async (id)=>{ await api.post(`/api/v1/approvals/${id}/approve`); await load() }
    const reject = async (id)=>{ await api.post(`/api/v1/approvals/${id}/reject`); await load() }
    onMounted(load)
    return { requests, approve, reject }
  }
}
</script>
