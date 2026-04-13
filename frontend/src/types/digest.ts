/** Mirrors `EmailEntry` / `Digest` in `backend/summarizer.py`. */

export type DigestEmail = {
  id: string
  sender: string
  subject: string
  received_at: string
  importance: string
  summary: string
}

export type OverallSummary = {
  title: string
  recommendations: string[]
}

export type Digest = {
  generated_at: string
  period_from: string
  period_to: string
  total_emails: number
  emails: DigestEmail[]
  /** Structured headline + list, or legacy plain string from old digests. */
  overall_summary: OverallSummary | string
}

export function isDigest(value: unknown): value is Digest {
  if (value === null || typeof value !== 'object') return false
  const v = value as Record<string, unknown>
  if (!Array.isArray(v.emails)) return false
  return v.emails.every(
    (e) =>
      e !== null &&
      typeof e === 'object' &&
      typeof (e as DigestEmail).id === 'string',
  )
}
