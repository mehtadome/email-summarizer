import { getJson } from './client'
import type { Digest } from '../types/digest'
import { isDigest } from '../types/digest'

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
export async function fetchLatestDigest(): Promise<Digest> {
  const data = await getJson<unknown>('/api/digests/latest')
  if (!isDigest(data)) {
    throw new Error('Invalid digest response from server.')
  }
  return data
}
