import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// ─── JWT 拦截器：自动携带 token ───
request.interceptors.request.use(
  config => {
    const token = sessionStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// ─── 响应拦截器：统一处理 401 ───
request.interceptors.response.use(
  response => {
    const data = response.data
    if (!data.success && data.success !== undefined) {
      ElMessage.error(data.message || '请求失败')
    }
    return data
  },
  error => {
    if (error.response?.status === 401) {
      sessionStorage.clear()
      window.location.href = '/login'
      return Promise.reject(error)
    }
    ElMessage.error(error.response?.data?.detail || error.message || '网络错误')
    return Promise.reject(error)
  }
)

export default request
