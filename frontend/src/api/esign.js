import api from './auth'

export async function getSignatures(recordType, recordId) {
  const params = {}
  if (recordType) params.record_type = recordType
  if (recordId) params.record_id = recordId
  const res = await api.get('/api/v1/esign/', { params })
  return res.data
}

export async function createSignature(data) {
  const res = await api.post('/api/v1/esign/', data)
  return res.data
}

export async function deleteSignature(id) {
  const res = await api.delete(`/api/v1/esign/${id}`)
  return res.data
}
