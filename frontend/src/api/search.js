import api from './auth'

export async function globalSearch(keyword, type, page, pageSize) {
  const params = { keyword }
  if (type) params.type = type
  if (page) params.page = page
  if (pageSize) params.page_size = pageSize
  const res = await api.get('/api/v1/search/', { params })
  return res.data
}
