import api from './auth'

export async function listAuditLogs(params) {
  const res = await api.get('/api/v1/audit-logs', { params })
  return res.data
}

export async function listSettings() {
  const res = await api.get('/api/v1/settings')
  return res.data
}

export async function updateSetting(key, value) {
  const res = await api.put(`/api/v1/settings/${key}`, { setting_value: value })
  return res.data
}

export async function search(q, type) {
  const res = await api.get('/api/v1/search', { params: { q, type } })
  return res.data
}
