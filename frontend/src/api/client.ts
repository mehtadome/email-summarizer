import { API_BASE } from './config'

function resolveUrl(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const base = API_BASE
  const suffix = path.startsWith('/') ? path : `/${path}`
  return base ? `${base}${suffix}` : suffix
}

export async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(resolveUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    throw new Error(`POST ${path}: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(resolveUrl(path), {
    ...init,
    method: init?.method ?? 'GET',
    headers: {
      Accept: 'application/json',
      ...init?.headers,
    },
  })
  if (!res.ok) {
    throw new Error(`GET ${path}: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}
