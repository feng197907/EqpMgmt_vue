import api from './auth'

export async function listDevices(params) {
  const res = await api.get('/api/v1/devices/', { params })
  return res.data
}

export async function getDevice(id) {
  const res = await api.get(`/api/v1/devices/${id}`)
  return res.data
}

export async function createDevice(data) {
  const res = await api.post('/api/v1/devices/', data)
  return res.data
}

export async function updateDevice(id, data) {
  const res = await api.put(`/api/v1/devices/${id}`, data)
  return res.data
}

export async function deleteDevice(id) {
  const res = await api.delete(`/api/v1/devices/${id}`)
  return res.data
}
