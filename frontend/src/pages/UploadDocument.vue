<template>
  <div>
    <h2>Upload Document</h2>
    <form @submit.prevent="onSubmit">
      <div>
        <label>Device</label>
        <select v-model="device_id" required>
          <option v-if="loadingDevices" disabled>加载中...</option>
          <option v-for="d in devices" :key="d.id" :value="d.id">{{ d.device_code }} - {{ d.device_name }}</option>
        </select>
      </div>
      <div>
        <label>Doc Type</label>
        <input v-model="doc_type" required />
      </div>
      <div>
        <label>Version</label>
        <input v-model="version" required />
      </div>
      <div>
        <label>Remarks</label>
        <input v-model="remarks" />
      </div>
      <div>
        <label>File(s)</label>
        <input type="file" ref="fileInput" multiple />
      </div>
      <button type="submit" :disabled="uploading">{{ uploading ? '上传中...' : 'Upload' }}</button>
    </form>
  </div>
</template>

<script>
import { ref } from 'vue'
import { uploadDocument } from '../api/documents'
import { listDevices } from '../api/devices'
import { useRouter } from 'vue-router'

export default {
  setup() {
    const device_id = ref('1')
    const doc_type = ref('manual')
    const version = ref('1.0')
    const remarks = ref('')
    const fileInput = ref(null)
    const router = useRouter()

    const devices = ref([])
    const loadingDevices = ref(false)
    const loadDevices = async () => {
      loadingDevices.value = true
      try {
        devices.value = await listDevices()
      } catch (e) {
        console.warn('无法加载设备列表', e)
      } finally {
        loadingDevices.value = false
      }
    }

    const uploading = ref(false)
    const onSubmit = async () => {
      const files = fileInput.value.files
      if (!files || files.length === 0) return alert('请选择文件')
      uploading.value = true
      try {
        for (let i = 0; i < files.length; i++) {
          const fd = new FormData()
          fd.append('device_id', device_id.value)
          fd.append('doc_type', doc_type.value)
          fd.append('version', version.value)
          fd.append('remarks', remarks.value)
          fd.append('file', files[i])
          await uploadDocument(fd)
        }
        alert('上传完成')
        router.push('/documents')
      } catch (err) {
        console.error('上传失败', err)
        alert('上传失败: ' + (err?.response?.data || err?.message || err))
      } finally {
        uploading.value = false
      }
    }

    loadDevices()
    return { device_id, doc_type, version, remarks, fileInput, onSubmit, devices, loadingDevices, uploading }
  }
}
</script>
