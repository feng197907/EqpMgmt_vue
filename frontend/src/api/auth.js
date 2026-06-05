import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000' })

export async function login(username, password) {
  const res = await api.post('/api/v1/auth/login', { username, password })
  return res.data
}

export async function refreshToken(refresh_token) {
  const res = await api.post('/api/v1/auth/refresh', { refresh_token })
  return res.data
}

export default api
