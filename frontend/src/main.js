import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import axios from 'axios'
import api from './api/auth'

// Set baseURL and attach token if present
axios.defaults.baseURL = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
api.defaults.baseURL = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const token = localStorage.getItem('access_token')
if (token) {
	axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
	api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// axios interceptor: refresh access token when receiving 401
axios.interceptors.response.use(
	response => response,
	async error => {
		const originalRequest = error.config
		if (error.response && error.response.status === 401 && !originalRequest._retry) {
			originalRequest._retry = true
			const refresh = localStorage.getItem('refresh_token')
			if (refresh) {
				try {
					const { refreshToken } = await import('./api/auth')
					const data = await refreshToken(refresh)
					const tokenVal = data.access_token
					if (tokenVal) {
						localStorage.setItem('access_token', tokenVal)
						axios.defaults.headers.common['Authorization'] = `Bearer ${tokenVal}`
						api.defaults.headers.common['Authorization'] = `Bearer ${tokenVal}`
						originalRequest.headers['Authorization'] = `Bearer ${tokenVal}`
						return axios(originalRequest)
					}
				} catch (e) {
					// fallthrough to logout
				}
			}
			// no refresh or failed -> redirect to login
			localStorage.removeItem('access_token')
			localStorage.removeItem('refresh_token')
			window.location.href = '/login'
		}
		return Promise.reject(error)
	}
)

const app = createApp(App)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
