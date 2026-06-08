import api from './auth'

export async function listSpareParts(params) {
  const res = await api.get('/api/v1/spare-parts/', { params })
  return res.data
}

export async function getSparePart(id) {
  const res = await api.get(`/api/v1/spare-parts/${id}`)
  return res.data
}

export async function createSparePart(data) {
  const res = await api.post('/api/v1/spare-parts/', data)
  return res.data
}

export async function updateSparePart(id, data) {
  const res = await api.put(`/api/v1/spare-parts/${id}`, data)
  return res.data
}

export async function deleteSparePart(id) {
  const res = await api.delete(`/api/v1/spare-parts/${id}`)
  return res.data
}

export async function listInbounds(partId) {
  const res = await api.get(`/api/v1/spare-parts/${partId}/inbounds`)
  return res.data
}

export async function inboundSparePart(partId, data) {
  const res = await api.post(`/api/v1/spare-parts/${partId}/inbound`, data)
  return res.data
}

export async function listConsumptions(partId) {
  const res = await api.get(`/api/v1/spare-parts/${partId}/consumptions`)
  return res.data
}

export async function consumeSparePart(partId, data) {
  const res = await api.post(`/api/v1/spare-parts/${partId}/consumption`, data)
  return res.data
}

export async function resolveAlert(alertId) {
  const res = await api.post(`/api/v1/spare-parts/alerts/${alertId}/resolve`)
  return res.data
}
