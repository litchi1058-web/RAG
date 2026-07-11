import request from './request'

export const ragApi = {
  query: (data) => request.post('/rag/query', data),
  getStatus: () => request.get('/rag/status'),
  predictImage: (data) => request.post('/rag/hybrid-query', data)
}
