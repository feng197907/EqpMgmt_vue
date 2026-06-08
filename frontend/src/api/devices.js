import api from './auth'

export async function listDevices(params) {
  const res = await api.get('/api/v1/devices/', { params })
  return res.data
}

export default { listDevices }
