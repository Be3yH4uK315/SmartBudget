import axios from 'axios'

const baseURL = 'http://127.0.0.1:9000/api/'

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

let isRefreshing = false
let pending: Array<(ok: boolean) => void> = []

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const { response, config } = error || {}
    const original: any = config || {}
    const status = response?.status

    if (status !== 401 || original.__isRetryRequest) {
      return Promise.reject(error)
    }

    if (!isRefreshing) {
      isRefreshing = true
      try {
        await refreshApi.post('/refresh', {})
        pending.forEach((cb) => cb(true))
      } catch (e) {
        pending.forEach((cb) => cb(false))
        return Promise.reject(error)
      } finally {
        isRefreshing = false
        pending = []
      }
    }

    /** ждём, чем кончится общий refresh */
    return new Promise((resolve, reject) => {
      pending.push(async (ok) => {
        if (!ok) return reject(error)
        try {
          original.__isRetryRequest = true
          resolve(api.request(original))
        } catch (e) {
          reject(e)
        }
      })
    })
  },
)

export const getDataMsg = (data: any) =>
  typeof data === 'string' ? data : data?.msg || data?.detail

export const req = async <T>(p: Promise<{ data: T }>): Promise<T> => {
  try {
    const { data } = await p
    return data
  } catch (e: any) {
    throw new Error(getDataMsg(e?.response?.data) || e?.message)
  }
}
