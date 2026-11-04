import axios from 'axios'
import { authClient } from './auth'
import { getSessionToken } from './sessionToken'

const api = axios.create()
api.interceptors.request.use(async (config) => {
  const token = await getSessionToken(authClient)
  config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api
