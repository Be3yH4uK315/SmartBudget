import axios, { AxiosError, AxiosRequestConfig } from 'axios'
import { authApi } from './auth'

const baseURL = 'http://127.0.0.1:8000/api/'

export const api = axios.create({
  baseURL,
  timeout: 3 * 60 * 1000,
  withCredentials: true,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})

const refreshApi = axios.create({
  baseURL,
  timeout: 30_000,
  withCredentials: true,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})

type RefreshResult = 'ok' | 'logout' | 'error'
let refreshPromise: Promise<RefreshResult> | null = null

function refreshSession(): Promise<RefreshResult> {
  if (!refreshPromise) {
    refreshPromise = refreshApi
      .post('/auth/refresh')
      .then((): RefreshResult => 'ok')
      .catch((err: AxiosError): RefreshResult => {
        const status = err.response?.status

        if (status === 401 || status === 403) {
          return 'logout'
        }

        return 'error'
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const response = error.response
    const config = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined

    if (!response || !config) {
      return Promise.reject(error)
    }

    const status = response.status
    const url = config.url ?? ''

    const isAuthEndpoint = url.startsWith('/auth/')

    if (isAuthEndpoint) {
      return Promise.reject(error)
    }

    if (status !== 401 || config._retry) {
      return Promise.reject(error)
    }

    const result = await refreshSession()

    if (result === 'ok') {
      config._retry = true
      return api.request(config)
    }

    if (result === 'logout') {
      await authApi.logout()
      return Promise.reject(error)
    }

    return Promise.reject(error)
  },
)
