import axios from 'axios'
import { getClientId } from '../hooks/useClientId.js'
import { getToken, setToken, TOKEN_REJECTED_EVENT } from '../utils/authToken.js'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  config.headers['X-Client-Id'] = getClientId()
  const token = getToken()
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

api.interceptors.response.use(undefined, (error) => {
  const sentToken = error.config?.headers?.Authorization
  if (error.response?.status === 401 && sentToken) {
    setToken(null)
    window.dispatchEvent(new Event(TOKEN_REJECTED_EVENT))
  }
  return Promise.reject(error)
})

export default api
