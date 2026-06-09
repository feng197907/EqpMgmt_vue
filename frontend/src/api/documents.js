import api from './auth'

export async function listDocuments(params) {
  const res = await api.get('/api/v1/documents/', { params })
  return res.data
}

export async function uploadDocument(formData) {
  const res = await api.post('/api/v1/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

/**
 * 下载文档 — 通过 axios 携带 Authorization header 请求，拿到 Blob 后
 * 触发浏览器保存弹窗。不能用 window.open，因为浏览器直接打开 URL 不
 * 携带 Authorization header，会导致 401。
 */
export async function downloadDocument(docId, filename) {
  const res = await api.get(`/api/v1/documents/${docId}/download`, {
    responseType: 'blob',
  })
  const contentType = res.headers['content-type'] || 'application/octet-stream'
  const blob = new Blob([res.data], { type: contentType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename || `document_${docId}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export async function submitDocument(docId) {
  const res = await api.post(`/api/v1/documents/${docId}/submit`)
  return res.data
}

export async function deleteDocument(docId) {
  const res = await api.delete(`/api/v1/documents/${docId}`)
  return res.data
}

export async function exportDocuments(params) {
  const res = await api.get('/api/v1/documents/export', { params, responseType: 'blob' })
  return res.data
}
