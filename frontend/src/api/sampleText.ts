import { getJson, postJson } from './client'

/** Response from `GET /api/sample-text` — digest headline + recommendations. */
export type SampleTextGetResponse = {
  title: string | null
  recommendations: string[]
  /** Shown when there is no digest or no structured summary. */
  message?: string
  /** Old digests with a plain-string overall_summary only. */
  legacy_text?: string
}

export type SampleTextPostResponse = {
  text: string
}

function parseGetResponse(data: unknown): SampleTextGetResponse {
  if (!data || typeof data !== 'object') {
    throw new Error('Invalid sample-text response')
  }
  const o = data as Record<string, unknown>
  if ('text' in o && typeof o.text === 'string' && !('recommendations' in o)) {
    return {
      title: null,
      recommendations: [],
      legacy_text: o.text,
    }
  }

  const title =
    o.title === undefined || o.title === null
      ? null
      : typeof o.title === 'string'
        ? o.title
        : null
  if (o.title !== undefined && o.title !== null && typeof o.title !== 'string') {
    throw new Error('Invalid sample-text response')
  }

  const recsRaw = o.recommendations
  const recs = Array.isArray(recsRaw)
    ? recsRaw.filter((x): x is string => typeof x === 'string')
    : []

  const message = o.message
  const legacyText = o.legacy_text
  if (message !== undefined && typeof message !== 'string') {
    throw new Error('Invalid sample-text response')
  }
  if (legacyText !== undefined && typeof legacyText !== 'string') {
    throw new Error('Invalid sample-text response')
  }

  return {
    title,
    recommendations: recs,
    message: typeof message === 'string' ? message : undefined,
    legacy_text: typeof legacyText === 'string' ? legacyText : undefined,
  }
}

/** `POST /api/sample-text` — verifies the POST flow end-to-end. */
export async function postSampleText(): Promise<SampleTextPostResponse> {
  const data = await postJson<unknown>('/api/sample-text')
  if (
    !data ||
    typeof data !== 'object' ||
    !('text' in data) ||
    typeof (data as SampleTextPostResponse).text !== 'string'
  ) {
    throw new Error('Invalid sample-text response')
  }
  return data as SampleTextPostResponse
}

/** `GET /api/sample-text` — headline + recommendations from the latest digest. */
export async function fetchSampleText(): Promise<SampleTextGetResponse> {
  const data = await getJson<unknown>('/api/sample-text')
  return parseGetResponse(data)
}
