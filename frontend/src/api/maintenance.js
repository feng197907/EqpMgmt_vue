import api from './auth'

export async function listMaintenancePlans(deviceId) {
  const res = await api.get(`/api/v1/devices/${deviceId}/maintenance/plans`)
  return res.data
}

export async function createMaintenancePlan(deviceId, payload) {
  const res = await api.post(`/api/v1/devices/${deviceId}/maintenance/plans`, payload)
  return res.data
}

export async function createMaintenanceRecord(deviceId, planId, payload) {
  const res = await api.post(`/api/v1/devices/${deviceId}/maintenance/plans/${planId}/records`, payload)
  return res.data
}

export async function listMaintenanceRecords(deviceId, planId) {
  const res = await api.get(`/api/v1/devices/${deviceId}/maintenance/plans/${planId}/records`)
  return res.data
}

export async function createRepairRecord(deviceId, payload) {
  const res = await api.post(`/api/v1/devices/${deviceId}/maintenance/repair-records`, payload)
  return res.data
}

export async function listRepairRecords(deviceId) {
  const res = await api.get(`/api/v1/devices/${deviceId}/maintenance/repair-records`)
  return res.data
}
