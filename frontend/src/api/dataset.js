import request from './request'

export const datasetApi = {
  stats: () => request.get('/dataset/stats'),
  distribution: () => request.get('/dataset/distribution'),
  upload: (formData) => request.post('/dataset/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
