import { ALL_INBOXES_TAB_KEY } from '../constants/digestInbox'
import { accountTabLabel } from './accountTabLabel'

const DEFAULT_ALL_INBOXES = 'All inboxes'

/** Default label for a tab key (matches digest tabs + settings placeholders). */
export function defaultLabelForTabKey(key: string): string {
  if (key === ALL_INBOXES_TAB_KEY) return DEFAULT_ALL_INBOXES
  return accountTabLabel(key)
}

/**
 * True when a saved value is the same as the built-in default — treat as unset
 * so the input shows placeholder styling instead of a “fake” custom value.
 */
export function isRedundantTabLabel(key: string, value: string | undefined): boolean {
  if (value === undefined || value.trim() === '') return true
  const v = value.trim()
  if (v === defaultLabelForTabKey(key)) return true
  if (key !== ALL_INBOXES_TAB_KEY && v === key.trim()) return true
  return false
}

export function pruneRedundantTabLabels(
  labels: Record<string, string>,
): Record<string, string> {
  const out: Record<string, string> = {}
  for (const [k, v] of Object.entries(labels)) {
    if (!isRedundantTabLabel(k, v)) out[k] = v
  }
  return out
}
