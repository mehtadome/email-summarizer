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
