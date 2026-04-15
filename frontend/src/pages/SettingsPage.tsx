import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { fetchLatestDigest } from '../api'
import { ALL_INBOXES_TAB_KEY } from '../constants/digestInbox'
import { useTabLabels } from '../contexts/TabLabelsContext'
import type { DigestEmail } from '../types/digest'
import { accountTabLabel } from '../utils/accountTabLabel'
import type { TabLabelMap } from '../utils/digestTabLabels'
import { uniqueNonEmptyAccounts } from '../utils/inboxAccounts'

export function SettingsPage() {
  const { labels, setLabels } = useTabLabels()
  const [accounts, setAccounts] = useState<string[]>([])
  const [digestError, setDigestError] = useState<string | null>(null)
  const [draft, setDraft] = useState<TabLabelMap>(() => ({ ...labels }))

  useEffect(() => {
    setDraft({ ...labels })
  }, [labels])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const digest = await fetchLatestDigest()
        if (cancelled) return
        const emails: DigestEmail[] = digest.emails.filter(
          (e) => e.account.trim() !== '',
        )
        setAccounts(uniqueNonEmptyAccounts(emails))
        setDigestError(null)
      } catch {
        if (!cancelled) {
          setDigestError('Could not load the latest digest. Inbox list may be incomplete.')
          setAccounts([])
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const defaultAll = 'All inboxes'

  function updateDraft(key: string, value: string) {
    setDraft((prev) => {
      const next = { ...prev }
      if (value.trim() === '') delete next[key]
      else next[key] = value
      return next
    })
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const next: TabLabelMap = { ...labels }
    const formKeys = [ALL_INBOXES_TAB_KEY, ...accounts]
    for (const k of formKeys) {
      const v = draft[k]
      if (v === undefined || v.trim() === '') delete next[k]
      else next[k] = v.trim()
    }
    setLabels(next)
  }

  const accountRows = useMemo(() => accounts, [accounts])

  return (
    <AppShell title="Settings" titleLarge>
      <p className="settings-lead">
        Custom names for digest inbox tabs. Leave a field blank to use the default label.
      </p>
      {digestError ? <p className="request-error">{digestError}</p> : null}
      <form className="settings-form" onSubmit={handleSubmit}>
        <label className="settings-field">
          <span className="settings-field__label">All inboxes</span>
          <input
            type="text"
            className="settings-input"
            value={draft[ALL_INBOXES_TAB_KEY] ?? ''}
            placeholder={defaultAll}
            onChange={(e) => updateDraft(ALL_INBOXES_TAB_KEY, e.target.value)}
            autoComplete="off"
          />
        </label>
        {accountRows.map((acc) => {
          const def = accountTabLabel(acc)
          return (
            <label key={acc} className="settings-field">
              <span className="settings-field__label">
                Inbox <code className="digest-inline-code">{acc}</code>
              </span>
              <input
                type="text"
                className="settings-input"
                value={draft[acc] ?? ''}
                placeholder={def}
                onChange={(e) => updateDraft(acc, e.target.value)}
                autoComplete="off"
              />
            </label>
          )
        })}
        <div className="settings-actions">
          <button type="submit" className="btn">
            Save
          </button>
          <Link to="/" className="digest-back-link settings-back">
            Back to home
          </Link>
        </div>
      </form>
    </AppShell>
  )
}
