import api from './auth'

export async function getDashboardStats() {
  const res = await api.get('/api/v1/dashboard/stats')
  return res.data
}
