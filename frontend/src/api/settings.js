import api from './auth'

export async function getSettings() {
  const res = await api.get('/api/v1/settings')
  return res.data
}

export async function updateSetting(key, data) {
  const res = await api.put(`/api/v1/settings/${key}`, data)
  return res.data
}
