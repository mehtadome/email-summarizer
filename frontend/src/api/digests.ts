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

/** `GET /api/digests/latest` — full latest digest JSON from disk (no pipeline run). */
export async function fetchLatestDigest(): Promise<Digest> {
  const data = await getJson<unknown>('/api/digests/latest')
  if (!isDigest(data)) {
    throw new Error('Invalid digest response from server.')
  }
  return data
}

/** Response from `GET /api/digests/refresh` (202 — job started in background). */
export type RefreshDigestResponse = { status: 'started' }

/** `GET /api/digests/refresh` — start re-fetch from Gmail; returns 202 with `{ status: "started" }`. */
export async function refreshDigest(): Promise<RefreshDigestResponse> {
  const data = await getJson<{ status?: string }>('/api/digests/refresh')
  if (data?.status === 'started') {
    return { status: 'started' }
  }
  throw new Error('Unexpected refresh response from server.')
}

/** `GET /api/digests/status` — whether the background digest job is running. */
export type DigestJobStatus = {
  running: boolean
  last_run_at: string | null
  error: string | null
}

export async function fetchDigestJobStatus(): Promise<DigestJobStatus> {
  return getJson<DigestJobStatus>('/api/digests/status')
}

/**
 * Poll until the digest job is no longer running, then resolve.
 * Throws if the job recorded an error or `timeoutMs` elapses.
 */
export async function waitForDigestJobComplete(options?: {
  pollIntervalMs?: number
  timeoutMs?: number
}): Promise<void> {
  const pollIntervalMs = options?.pollIntervalMs ?? 500
  const timeoutMs = options?.timeoutMs ?? 10 * 60 * 1000
  const started = Date.now()

  while (Date.now() - started < timeoutMs) {
    const s = await fetchDigestJobStatus()
    if (!s.running) {
      if (s.error) {
        throw new Error(s.error)
      }
      return
    }
    await new Promise((r) => setTimeout(r, pollIntervalMs))
  }
  throw new Error('Digest job timed out.')
}
