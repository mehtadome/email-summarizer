import { pruneRedundantTabLabels } from './tabLabelDefaults'

const STORAGE_KEY = 'email-summarizer.digest_inbox_tab_labels'

export type TabLabelMap = Record<string, string>

export function loadTabLabels(): TabLabelMap {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const p = JSON.parse(raw) as unknown
    if (p === null || typeof p !== 'object' || Array.isArray(p)) return {}
    const out: TabLabelMap = {}
    for (const [k, v] of Object.entries(p)) {
      if (typeof v === 'string' && v.trim() !== '') out[k] = v.trim()
    }
    const pruned = pruneRedundantTabLabels(out)
    if (Object.keys(pruned).length !== Object.keys(out).length) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(pruned))
      } catch {
        /* ignore */
      }
    }
    return pruned
  } catch {
    return {}
  }
}

export function saveTabLabels(map: TabLabelMap): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map))
  } catch {
    /* quota / private mode */
  }
}
