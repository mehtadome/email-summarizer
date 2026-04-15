import type { DigestEmail } from '../types/digest'

/** Distinct non-empty inbox ids (trimmed), sorted. */
export function uniqueNonEmptyAccounts(emails: DigestEmail[]): string[] {
  const u = [...new Set(emails.map((e) => e.account.trim()).filter(Boolean))]
  u.sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))
  return u
}
