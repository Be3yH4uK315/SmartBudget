import axios from 'axios'

const baseURL = ''

export const api = axios.create({
  baseURL,
  timeout: 3 * 60 * 1000,
  withCredentials: true,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})

const getDataMsg = (data: any) => (typeof data === 'string' ? data : data.msg)
