import api from './auth'

export async function listUsers() {
  const res = await api.get('/api/v1/users/')
  return res.data
}

export async function createUser(data) {
  const res = await api.post('/api/v1/users/', data)
  return res.data
}

export async function updateUser(id, data) {
  const res = await api.put(`/api/v1/users/${id}`, data)
  return res.data
}

export async function deleteUser(id) {
  await api.delete(`/api/v1/users/${id}`)
}
