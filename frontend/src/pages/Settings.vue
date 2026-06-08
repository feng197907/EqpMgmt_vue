<template>
  <div>
    <h2 style="margin:0 0 16px;">系统设置</h2>

    <el-card>
      <el-form label-width="200px" v-loading="loading">
        <el-form-item v-for="s in settings" :key="s.id" :label="settingLabel(s.setting_key)">
          <template v-if="isSwitch(s.setting_key)">
            <el-switch
              :model-value="s.setting_value === 'true'"
              @change="(val) => updateSwitch(s.setting_key, val)"
              :loading="savingKey === s.setting_key"
            />
          </template>
          <template v-else>
            <div style="display:flex;gap:8px;align-items:center;">
              <el-input v-model="editValues[s.setting_key]" style="width:300px;" />
              <el-button type="primary" size="small" :loading="savingKey === s.setting_key" @click="saveSetting(s.setting_key)">
                保存
              </el-button>
            </div>
          </template>
          <div style="color:#999;font-size:12px;margin-top:4px;">{{ s.description || '' }}</div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listSettings, updateSetting } from '../api/audit'

export default {
  setup() {
    const settings = ref([])
    const loading = ref(false)
    const savingKey = ref(null)
    const editValues = reactive({})

    const isSwitch = (key) => ['approval_enabled', 'auto_approve_document', 'borrowing_enabled', 'doc_auto_active'].includes(key)

    const settingLabel = (key) => ({
      approval_enabled: '审批流程开关',
      auto_approve_document: '文档自动生效',
      borrowing_enabled: '借阅功能开关',
      doc_auto_active: '文档自动激活',
    }[key] || key)

    const load = async () => {
      loading.value = true
      try {
        settings.value = await listSettings()
        settings.value.forEach((s) => {
          editValues[s.setting_key] = s.setting_value || ''
        })
      } catch (e) {
        ElMessage.error('加载设置失败')
      } finally {
        loading.value = false
      }
    }

    const saveSetting = async (key) => {
      savingKey.value = key
      try {
        await updateSetting(key, editValues[key] || '')
        ElMessage.success(`设置 ${key} 已保存`)
      } catch (e) {
        ElMessage.error('保存失败')
      } finally {
        savingKey.value = null
      }
    }

    const updateSwitch = async (key, val) => {
      savingKey.value = key
      try {
        await updateSetting(key, val ? 'true' : 'false')
        ElMessage.success(`设置 ${key} 已保存`)
        await load()
      } catch (e) {
        ElMessage.error('保存失败')
      } finally {
        savingKey.value = null
      }
    }

    onMounted(load)
    return { settings, loading, savingKey, editValues, saveSetting, updateSwitch, isSwitch, settingLabel }
  },
}
</script>
