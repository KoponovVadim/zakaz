const API_BASE = '/api'

function authHeaders() {
  const token = localStorage.getItem('zakaz_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(options.headers || {})
    }
  })
  if (!response.ok) {
    const contentType = response.headers.get('content-type') || ''
    const error = contentType.includes('application/json')
      ? await response.json().catch(() => ({ detail: response.statusText }))
      : { detail: await response.text().catch(() => response.statusText) }
    const detail = error.detail || response.statusText || 'API error'
    throw new Error(`HTTP ${response.status}: ${detail}`)
  }
  if (response.status === 204) return null
  return response.json()
}

export function downloadUrl(path) {
  return `${API_BASE}${path}`
}
