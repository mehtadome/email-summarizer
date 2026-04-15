import type { DigestListItem } from '../api/digests'

/** Tab label from digest metadata (`generated_at` preferred, else filename stem). */
export function formatDigestTabLabel(item: DigestListItem): string {
  const raw = item.generated_at?.trim()
  if (raw) {
    const d = new Date(raw)
    if (!Number.isNaN(d.getTime())) {
      return d.toLocaleDateString(undefined, { dateStyle: 'medium' })
    }
  }
  return item.filename.replace(/\.json$/i, '')
}
