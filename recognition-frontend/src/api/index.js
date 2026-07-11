import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: '/api',
  timeout: 60000
})

service.interceptors.response.use(
  response => {
    const res = response.data
    if (res.success === false) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 识别
export const predictImage = (formData) =>
  service.post('/model/predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

// RAG 诊断
export const ragQuery = (query) =>
  service.get('/rag/query', { params: { query } })

export const ragStatus = () => service.get('/rag/status')

// 知识库
export const getKnowledgeList = () => service.get('/knowledge')

// 知识图谱
export const getKnowledgeGraph = () => service.get('/knowledge-graph')
export const getGraphStats = () => service.get('/knowledge-graph/stats')
export const searchGraph = (q) =>
  service.get('/knowledge-graph/search', { params: { q } })
export const findPath = (source, target) =>
  service.get('/knowledge-graph/path', { params: { source, target } })

// 模型
export const getModelStatus = () => service.get('/model/status')
export const getModelMetrics = () => service.get('/model/metrics')

export default service
