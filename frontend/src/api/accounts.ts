import { getJson } from './client'

/** `GET /api/accounts` — configured Gmail accounts in order (index matches `/mail/u/N/`). */
export async function fetchAccounts(): Promise<string[]> {
  return getJson<string[]>('/api/accounts')
}
