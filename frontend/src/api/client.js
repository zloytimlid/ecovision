import axios from 'axios'
import { getClientId } from '../hooks/useClientId.js'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  config.headers['X-Client-Id'] = getClientId()
  return config
})

export default api
