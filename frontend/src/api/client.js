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
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'API error')
  }
  if (response.status === 204) return null
  return response.json()
}

export function downloadUrl(path) {
  return `${API_BASE}${path}`
}
