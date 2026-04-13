import type { DigestEmail } from '../types/digest'

const RANK: Record<string, number> = {
  high: 0,
  medium: 1,
  low: 2,
}

function rank(importance: string): number {
  return RANK[importance.trim().toLowerCase()] ?? 3
}

/** Newest array: high first, then medium, then low, then anything else. */
export function sortEmailsByImportance(emails: DigestEmail[]): DigestEmail[] {
  return [...emails].sort((a, b) => rank(a.importance) - rank(b.importance))
}
