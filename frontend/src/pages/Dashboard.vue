<template>
  <div>
    <h2 style="margin:0 0 16px;">仪表盘</h2>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card>
          <template #header><span>设备统计</span></template>
          <div style="text-align:center;padding:20px 0;">
            <div style="font-size:36px;color:#409EFF;font-weight:bold;">{{ deviceCount }}</div>
            <div style="color:#999;margin-top:8px;">活跃设备</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>文档统计</span></template>
          <div style="text-align:center;padding:20px 0;">
            <div style="font-size:36px;color:#67C23A;font-weight:bold;">{{ docCount }}</div>
            <div style="color:#999;margin-top:8px;">文档总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>待审批</span></template>
          <div style="text-align:center;padding:20px 0;">
            <div style="font-size:36px;color:#E6A23C;font-weight:bold;">{{ pendingCount }}</div>
            <div style="color:#999;margin-top:8px;">审批任务</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top:16px;">
      <template #header><span>快捷导航</span></template>
      <el-space wrap>
        <el-button type="primary" @click="$router.push('/documents')">文档管理</el-button>
        <el-button type="success" @click="$router.push('/documents/upload')">上传文档</el-button>
        <el-button type="warning" @click="$router.push('/approvals')">审批任务</el-button>
        <el-button type="info" @click="$router.push('/maintenance')">维护管理</el-button>
      </el-space>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { listDevices } from '../api/devices'
import { listDocuments } from '../api/documents'
import api from '../api/auth'

export default {
  setup() {
    const deviceCount = ref(0)
    const docCount = ref(0)
    const pendingCount = ref(0)

    onMounted(async () => {
      try {
        const devices = await listDevices()
        deviceCount.value = devices.length
      } catch (e) { /* ignore */ }

      try {
        const docs = await listDocuments()
        docCount.value = docs.length
      } catch (e) { /* ignore */ }

      try {
        const approvals = await api.get('/api/v1/approvals/')
        pendingCount.value = (approvals.data || []).length
      } catch (e) { /* ignore */ }
    })

    return { deviceCount, docCount, pendingCount }
  },
}
</script>
