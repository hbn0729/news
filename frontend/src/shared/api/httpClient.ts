import axios from 'axios'

const httpClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

httpClient.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default httpClient
