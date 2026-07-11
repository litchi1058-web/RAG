import request from './request'

export const diagnosisApi = {
  history: (page = 1, limit = 20) => request.get(`/detection/history?page=${page}&limit=${limit}`),
  detail: (id) => request.get(`/detection/${id}`),
  create: (data) => request.post('/detection', data),
  remove: (id) => request.delete(`/detection/${id}`)
}
