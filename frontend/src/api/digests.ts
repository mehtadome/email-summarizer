import { getJson } from './client'

export type DigestListItem = {
  filename: string
  generated_at?: string
  total_emails?: number
  overall_summary?: string
}

/** `GET /api/digests` — metadata for all saved digests, newest first. */
export async function fetchDigests(): Promise<DigestListItem[]> {
  return getJson<DigestListItem[]>('/api/digests')
}

/** `GET /api/digests/latest` — full latest digest JSON. */
export async function fetchLatestDigest(): Promise<unknown> {
  return getJson<unknown>('/api/digests/latest')
}
