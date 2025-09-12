import axios from 'axios'

// Normalize base URL to avoid double slashes when joining with paths
const API_BASE = (import.meta.env.VITE_API_BASE || 'https://museum-anomaly-detection-backend.onrender.com').replace(/\/+$/, '')

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 45000,
})

export async function fetchSensors() {
  const { data } = await api.get('/sensors/data')
  return data
}

export async function checkAnomaly(payload) {
  const { data } = await api.post('/anomaly/check', payload || {})
  return data
}

export async function chat(question) {
  const { data } = await api.post('/chat', { question })
  return data
}

// New vision anomaly detection function
export async function checkVisionAnomaly(imageFile) {
  const formData = new FormData()
  formData.append('file', imageFile)
  
  const { data } = await api.post('/vision/check', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return data
}

// Enhanced anomaly check with individual sensor parameters
export async function checkAnomalyEnhanced(temperature_c, humidity_pct, vibration) {
  const payload = {}
  if (temperature_c !== undefined) payload.temperature_c = temperature_c
  if (humidity_pct !== undefined) payload.humidity_pct = humidity_pct  
  if (vibration !== undefined) payload.vibration = vibration
  
  const { data } = await api.post('/anomaly/check', payload)
  return data
}

export function getCameraStreamUrl(exhibitId) {
  return `${API_BASE}/camera/stream?exhibit=${exhibitId || 'default'}`
}

