<template>
  <div>
    <h2 style="margin:0 0 16px;">上传文档</h2>

    <el-card style="max-width:600px;">
      <el-form :model="form" label-width="100px" @submit.prevent="onSubmit">
        <el-form-item label="所属设备" required>
          <el-select v-model="form.device_id" placeholder="请选择设备" style="width:100%"
            :loading="loadingDevices" filterable>
            <el-option
              v-for="d in devices"
              :key="d.id"
              :label="`${d.device_code} - ${d.device_name}`"
              :value="d.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="文档类型" required>
          <el-input v-model="form.doc_type" placeholder="如: manual, calibration, certificate" />
        </el-form-item>
        <el-form-item label="版本号" required>
          <el-input v-model="form.version" placeholder="如: 1.0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remarks" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="选择文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="10"
            :on-exceed="onExceed"
            drag
          >
            <el-icon style="font-size:40px;"><UploadFilled /></el-icon>
            <div style="margin-top:8px;">将文件拖到此处，或点击上传</div>
          </el-upload>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="uploading" @click="onSubmit">
            {{ uploading ? '上传中...' : '提交上传' }}
          </el-button>
          <el-button @click="$router.push('/documents')">返回</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { uploadDocument } from '../api/documents'
import { listDevices } from '../api/devices'

export default {
  components: { UploadFilled },
  setup() {
    const router = useRouter()
    const uploadRef = ref(null)
    const devices = ref([])
    const loadingDevices = ref(false)
    const uploading = ref(false)

    const form = reactive({
      device_id: null,
      doc_type: 'manual',
      version: '1.0',
      remarks: '',
    })

    const loadDevices = async () => {
      loadingDevices.value = true
      try {
        devices.value = await listDevices()
        if (devices.value.length) form.device_id = devices.value[0].id
      } catch (e) {
        ElMessage.warning('无法加载设备列表')
      } finally {
        loadingDevices.value = false
      }
    }

    const onExceed = () => {
      ElMessage.warning('最多上传 10 个文件')
    }

    const onSubmit = async () => {
      const files = uploadRef.value?.uploadFiles || []
      if (!files.length) {
        ElMessage.warning('请选择文件')
        return
      }
      if (!form.device_id) {
        ElMessage.warning('请选择设备')
        return
      }
      uploading.value = true
      try {
        for (const file of files) {
          const fd = new FormData()
          fd.append('device_id', form.device_id)
          fd.append('doc_type', form.doc_type)
          fd.append('version', form.version)
          fd.append('remarks', form.remarks)
          fd.append('file', file.raw)
          await uploadDocument(fd)
        }
        ElMessage.success('上传完成')
        router.push('/documents')
      } catch (err) {
        const msg = err?.response?.data?.detail || err?.message || '上传失败'
        ElMessage.error(msg)
      } finally {
        uploading.value = false
      }
    }

    onMounted(loadDevices)

    return { form, uploadRef, devices, loadingDevices, uploading, onExceed, onSubmit }
  },
}
</script>
