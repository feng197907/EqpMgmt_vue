import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/theme.css'
import axios from 'axios'
import api from './api/auth'
import { reportJsError } from './api/log'

// ── Global JS Error Capture ────────────────────────────────────────────────

// Layer 1: synchronous script errors (window.onerror)
window.onerror = function (message, source, lineno, colno, error) {
  reportJsError({
    message: String(message),
    source,
    lineno,
    colno,
    stack: error?.stack,
    type: 'onerror',
  })
  return false // don't suppress default browser console output
}

// Layer 2: unhandled Promise rejections
window.addEventListener('unhandledrejection', (event) => {
  const reason = event.reason
  reportJsError({
    message: reason?.message || String(reason) || 'Unhandled Promise rejection',
    source: null,
    lineno: null,
    colno: null,
    stack: reason?.stack || null,
    type: 'unhandledrejection',
  })
})

// ── Base URL & Auth Token ─────────────────────────────────────────────────
// In dev mode baseURL is empty so requests go through Vite proxy.
axios.defaults.baseURL = import.meta.env.VITE_API_BASE || ''
api.defaults.baseURL = import.meta.env.VITE_API_BASE || ''
const token = localStorage.getItem('access_token')
if (token) {
	axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
	api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// ── Axios Interceptor: refresh access token on 401 ────────────────────────
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

// ── Vue App ────────────────────────────────────────────────────────────────
const app = createApp(App)

// Layer 3: Vue component errors (renders, watchers, lifecycle hooks)
app.config.errorHandler = (err, instance, info) => {
  reportJsError({
    message: err?.message || String(err),
    source: info || null,
    lineno: null,
    colno: null,
    stack: err?.stack || null,
    type: 'vue_errorHandler',
  })
  // Re-throw so the browser console still shows the error
  console.error('[Vue Error]', err, info)
}

app.use(router)
app.use(ElementPlus)
app.mount('#app')
