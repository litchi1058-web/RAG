import request from './request'

export const modelApi = {
  status: () => request.get('/model/status'),
  logs: (limit = 50) => request.get(`/model/logs?limit=${limit}`),
  metrics: () => request.get('/model/metrics'),
  predict: (formData) => request.post('/model/predict', formData),
  diagnose: (query) => request.post('/rag/query', { query }),
}
