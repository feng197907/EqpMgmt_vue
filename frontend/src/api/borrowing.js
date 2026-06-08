import api from './auth'

export async function listBorrowRecords(params) {
  const res = await api.get('/api/v1/borrowing/', { params })
  return res.data
}

export async function myBorrowRecords() {
  const res = await api.get('/api/v1/borrowing/my')
  return res.data
}

export async function borrowDocument(data) {
  const res = await api.post('/api/v1/borrowing/', data)
  return res.data
}

export async function returnDocument(recordId) {
  const res = await api.post(`/api/v1/borrowing/${recordId}/return`)
  return res.data
}

export async function deleteBorrowRecord(recordId) {
  const res = await api.delete(`/api/v1/borrowing/${recordId}`)
  return res.data
}
