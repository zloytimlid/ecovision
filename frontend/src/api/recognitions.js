import api from './client.js'

export async function recognize(imageBlob) {
  const form = new FormData()
  form.append('image', imageBlob, 'photo.jpg')
  const { data } = await api.post('/recognize/', form)
  return data
}

export async function getRecognition(id) {
  const { data } = await api.get(`/recognitions/${id}/`)
  return data
}

export async function listRecognitions(page = 1) {
  const { data } = await api.get('/recognitions/', { params: { page } })
  return data
}

export async function deleteRecognition(id) {
  await api.delete(`/recognitions/${id}/`)
}

export async function sendFeedback(id, payload) {
  const { data } = await api.post(`/recognitions/${id}/feedback/`, payload)
  return data
}
