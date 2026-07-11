import request from './request'

export const knowledgeApi = {
  list: () => request.get('/knowledge'),
  get: (key) => request.get(`/knowledge/${key}`),
  create: (data) => request.post('/knowledge', data),
  update: (key, data) => request.put(`/knowledge/${key}`, data),
  remove: (key) => request.delete(`/knowledge/${key}`),
  getGraph: () => request.get('/knowledge-graph'),
  rebuildGraph: () => request.post('/knowledge-graph/rebuild'),
  getGraphStats: () => request.get('/knowledge-graph/stats'),
  searchGraph: (q) => request.get(`/knowledge-graph/search?q=${encodeURIComponent(q)}`),
  findPath: (source, target) => request.get(`/knowledge-graph/path?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}`),
}
