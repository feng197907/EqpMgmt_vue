<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <div>
        <h2 style="margin:0;">维护管理</h2>
        <p style="margin:4px 0 0;color:#666;">设备：{{ deviceLabel }}</p>
      </div>
    </div>

    <!-- 创建维护计划 -->
    <el-card style="margin-bottom:16px;">
      <template #header><strong>创建维护计划</strong></template>
      <el-form :inline="true">
        <el-form-item label="维护类型">
          <el-input v-model="form.maintenance_type" placeholder="如 preventive" />
        </el-form-item>
        <el-form-item label="周期(天)">
          <el-input-number v-model="form.interval_days" :min="1" :max="365" />
        </el-form-item>
        <el-form-item label="下次到期">
          <el-input v-model="form.next_due_date" placeholder="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="savingPlan" @click="createPlan">
            创建计划
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 维护计划列表 -->
    <el-card style="margin-bottom:16px;">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <strong>维护计划</strong>
          <el-button size="small" @click="loadAll">刷新</el-button>
        </div>
      </template>
      <el-table :data="plans" stripe empty-text="暂无维护计划">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="maintenance_type" label="类型">
          <template #default="{ row }">{{ maintTypeLabel(row.maintenance_type) }}</template>
        </el-table-column>
        <el-table-column prop="interval_days" label="周期(天)" width="100" />
        <el-table-column prop="next_due_date" label="下次到期" width="120" />
        <el-table-column prop="urgency" label="紧迫度" width="90">
          <template #default="{ row }">
            <el-tag
              :type="row.urgency === 'success' ? 'success' : row.urgency === 'warning' ? 'warning' : 'danger'"
              size="small"
            >{{ urgencyLabel(row.urgency) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260">
          <template #default="{ row }">
            <el-button size="small" @click="loadPlanRecords(row.id)">记录</el-button>
            <el-button size="small" type="primary" @click="fillRecordPlan(row.id)">
              新建记录
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 提交维护记录 -->
    <el-card style="margin-bottom:16px;">
      <template #header>
        <strong>提交维护记录</strong>
        <span style="margin-left:12px;color:#999;">当前计划：{{ currentPlanId || '未选择' }}</span>
      </template>
      <el-form :inline="true">
        <el-form-item label="维护内容">
          <el-input v-model="recordForm.content" placeholder="维护内容" />
        </el-form-item>
        <el-form-item label="结果">
          <el-select v-model="recordForm.result" style="width:160px;">
            <el-option label="合格" value="qualified" />
            <el-option label="待处理" value="pending" />
            <el-option label="不合格" value="unqualified" />
          </el-select>
        </el-form-item>
        <el-form-item label="备件">
          <el-input v-model="recordForm.parts_used" placeholder="可选" />
        </el-form-item>
        <el-form-item>
          <el-button type="success" :loading="savingRecord" @click="createRecord">
            提交记录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 维护记录列表 -->
    <el-card style="margin-bottom:16px;">
      <template #header><strong>维护记录</strong></template>
      <el-table :data="records" stripe empty-text="暂无维护记录">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="content" label="内容" />
        <el-table-column prop="result" label="结果" width="100">
          <template #default="{ row }">{{ resultLabel(row.result) }}</template>
        </el-table-column>
        <el-table-column prop="performed_by" label="执行人" width="120" />
        <el-table-column prop="performed_at" label="时间" width="120" />
      </el-table>
    </el-card>

    <!-- 维修记录 -->
    <el-card>
      <template #header><strong>维修记录</strong></template>
      <el-form :inline="true" style="margin-bottom:8px;">
        <el-form-item label="维修内容">
          <el-input v-model="repairForm.content" placeholder="维修内容" />
        </el-form-item>
        <el-form-item label="结果">
          <el-select v-model="repairForm.result" style="width:160px;">
            <el-option label="已修复" value="fixed" />
            <el-option label="待处理" value="pending" />
          </el-select>
        </el-form-item>
        <el-form-item label="备件">
          <el-input v-model="repairForm.parts_used" placeholder="可选" />
        </el-form-item>
        <el-form-item>
          <el-button type="warning" :loading="savingRepair" @click="createRepair">
            提交维修记录
          </el-button>
        </el-form-item>
      </el-form>
      <el-table :data="repairRecords" stripe empty-text="暂无维修记录">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="content" label="内容" />
        <el-table-column prop="result" label="结果" width="100">
          <template #default="{ row }">{{ resultLabel(row.result) }}</template>
        </el-table-column>
        <el-table-column prop="performed_by" label="执行人" width="120" />
        <el-table-column prop="performed_at" label="时间" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listDevices } from '../api/devices'
import {
  listMaintenancePlans,
  createMaintenancePlan,
  createMaintenanceRecord,
  listMaintenanceRecords,
  createRepairRecord,
  listRepairRecords,
} from '../api/maintenance'

export default {
  setup() {
    const route = useRoute()
    const devices = ref([])
    const plans = ref([])
    const records = ref([])
    const repairRecords = ref([])
    const currentPlanId = ref(null)
    const savingPlan = ref(false)
    const savingRecord = ref(false)
    const savingRepair = ref(false)
    const form = reactive({
      maintenance_type: 'preventive',
      interval_days: 30,
      next_due_date: '',
    })
    const recordForm = reactive({ content: '', result: 'qualified', parts_used: '' })
    const repairForm = reactive({ content: '', result: 'fixed', parts_used: '' })

    const deviceId = computed(() =>
      Number(route.params.deviceId || devices.value[0]?.id || 0)
    )
    const deviceLabel = computed(() => {
      const item = devices.value.find((d) => d.id === deviceId.value)
      return item ? `${item.device_code} - ${item.device_name}` : '未选择'
    })

    const maintTypeLabel = (t) => ({ preventive: '预防性维护', corrective: '故障维修', inspection: '定期检查' }[t] || t)
    const urgencyLabel = (u) => ({ success: '正常', warning: '即将到期', danger: '已过期' }[u] || u)
    const resultLabel = (r) => ({ qualified: '合格', pending: '待处理', unqualified: '不合格', fixed: '已修复' }[r] || r)

    const loadDevices = async () => {
      devices.value = await listDevices()
    }

    const loadAll = async () => {
      if (!deviceId.value) return
      plans.value = await listMaintenancePlans(deviceId.value)
      repairRecords.value = await listRepairRecords(deviceId.value)
      if (currentPlanId.value) {
        records.value = await listMaintenanceRecords(deviceId.value, currentPlanId.value)
      }
    }

    const createPlan = async () => {
      if (!deviceId.value) {
        ElMessage.warning('请选择设备')
        return
      }
      savingPlan.value = true
      try {
        await createMaintenancePlan(deviceId.value, {
          device_id: deviceId.value,
          ...form,
        })
        await loadAll()
        ElMessage.success('维护计划已创建')
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '创建失败')
      } finally {
        savingPlan.value = false
      }
    }

    const fillRecordPlan = (planId) => {
      currentPlanId.value = planId
      recordForm.content = recordForm.content || ''
    }

    const loadPlanRecords = async (planId) => {
      currentPlanId.value = planId
      records.value = await listMaintenanceRecords(deviceId.value, planId)
    }

    const createRecord = async () => {
      if (!currentPlanId.value) {
        ElMessage.warning('请选择维护计划')
        return
      }
      savingRecord.value = true
      try {
        await createMaintenanceRecord(deviceId.value, currentPlanId.value, { ...recordForm })
        await loadPlanRecords(currentPlanId.value)
        await loadAll()
        ElMessage.success('维护记录已提交')
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '提交失败')
      } finally {
        savingRecord.value = false
      }
    }

    const createRepair = async () => {
      savingRepair.value = true
      try {
        await createRepairRecord(deviceId.value, { ...repairForm })
        repairRecords.value = await listRepairRecords(deviceId.value)
        ElMessage.success('维修记录已提交')
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '提交失败')
      } finally {
        savingRepair.value = false
      }
    }

    onMounted(async () => {
      // 设置默认日期为明天
      const tomorrow = new Date()
      tomorrow.setDate(tomorrow.getDate() + 1)
      form.next_due_date = tomorrow.toISOString().split('T')[0]
      await loadDevices()
      await loadAll()
    })

    return {
      deviceLabel, plans, records, repairRecords, currentPlanId,
      form, recordForm, repairForm,
      savingPlan, savingRecord, savingRepair,
      maintTypeLabel, urgencyLabel, resultLabel,
      createPlan, fillRecordPlan, loadPlanRecords, createRecord,
      createRepair, loadAll,
    }
  },
}
</script>
