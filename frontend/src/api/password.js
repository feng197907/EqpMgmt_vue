import api from './auth'

export async function getResetRequests(status) {
  const params = {}
  if (status) params.status = status
  const res = await api.get('/api/v1/password/resets', { params })
  return res.data
}

export async function createResetRequest(data) {
  const res = await api.post('/api/v1/password/resets', data)
  return res.data
}

export async function processReset(id, data) {
  const res = await api.post(`/api/v1/password/resets/${id}/reset`, data)
  return res.data
}

export async function cancelReset(id) {
  const res = await api.post(`/api/v1/password/resets/${id}/cancel`)
  return res.data
}
