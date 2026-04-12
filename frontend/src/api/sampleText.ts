import { getJson, postJson } from './client'

export type SampleTextResponse = {
  text: string
}

/** `POST /api/sample-text` — verifies the POST flow end-to-end. */
export async function postSampleText(): Promise<SampleTextResponse> {
  const data = await postJson<unknown>('/api/sample-text')
  if (!data || typeof data !== 'object' || !('text' in data) || typeof (data as SampleTextResponse).text !== 'string') {
    throw new Error('Invalid sample-text response')
  }
  return data as SampleTextResponse
}

/** `GET /api/sample-text` — overall summary from the latest digest. */
export async function fetchSampleText(): Promise<SampleTextResponse> {
  const data = await getJson<unknown>('/api/sample-text')
  if (
    !data ||
    typeof data !== 'object' ||
    !('text' in data) ||
    typeof (data as SampleTextResponse).text !== 'string'
  ) {
    throw new Error('Invalid sample-text response')
  }
  return data as SampleTextResponse
}
