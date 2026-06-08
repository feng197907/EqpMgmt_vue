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

export function downloadUrl(docId) {
  return `${api.defaults.baseURL}/api/v1/documents/${docId}/download`
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
