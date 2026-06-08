import api from './auth'

export async function getPendingApprovals(page, pageSize) {
  const params = {}
  if (page) params.page = page
  if (pageSize) params.page_size = pageSize
  const res = await api.get('/api/v1/approvals/pending', { params })
  return res.data
}

export async function approveRequest(id, data) {
  const res = await api.post(`/api/v1/approvals/${id}/approve`, data)
  return res.data
}

export async function rejectRequest(id, data) {
  const res = await api.post(`/api/v1/approvals/${id}/reject`, data)
  return res.data
}
