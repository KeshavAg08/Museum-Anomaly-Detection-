import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

export async function fetchSensors() {
  const { data } = await api.get('/sensors/data')
  return data
}

export async function checkAnomaly(payload) {
  const { data } = await api.post('/anomaly/check', payload || {})
  return data
}

export async function chat(message) {
  const { data } = await api.post('/chat', { message })
  return data
}

export function getCameraStreamUrl(exhibitId) {
  return `${API_BASE}/camera/stream?exhibit=${exhibitId || 'default'}`
}

