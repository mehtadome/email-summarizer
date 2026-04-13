import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { DigestEmailCard } from '../components/DigestEmailCard'
import { fetchLatestDigest } from '../api'
import { ALL_INBOXES_TAB_KEY } from '../constants/digestInbox'
import { useTabLabels } from '../contexts/TabLabelsContext'
import type { Digest, DigestEmail } from '../types/digest'
import { accountTabLabel } from '../utils/accountTabLabel'
import { uniqueNonEmptyAccounts } from '../utils/inboxAccounts'
import { sortEmailsByImportance } from '../utils/sortByImportance'

type LoadState = 'loading' | 'success' | 'error'

export function DigestPage() {
  const { emailId } = useParams<{ emailId?: string }>()
  const decodedId = emailId ? decodeURIComponent(emailId) : undefined

  const { labels: tabLabels } = useTabLabels()

  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [digest, setDigest] = useState<Digest | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeInbox, setActiveInbox] = useState(ALL_INBOXES_TAB_KEY)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await fetchLatestDigest()
        if (!cancelled) {
          setDigest(data)
          setLoadState('success')
          setError(null)
        }
      } catch {
        if (!cancelled) {
          setDigest(null)
          setLoadState('error')
          setError(
            'We could not load a digest. Run one first (e.g. `python -m backend.main --now`) or confirm the API is running on port 8000.',
          )
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const emailsWithInbox = useMemo(() => {
    if (!digest?.emails.length) return []
    return digest.emails.filter((e) => e.account.trim() !== '')
  }, [digest])

  const inboxAccounts = useMemo(
    () => uniqueNonEmptyAccounts(emailsWithInbox),
    [emailsWithInbox],
  )

  useEffect(() => {
    if (inboxAccounts.length === 0) {
      setActiveInbox('')
      return
    }
    if (inboxAccounts.length === 1) {
      setActiveInbox('')
      return
    }
    const valid = new Set<string>([ALL_INBOXES_TAB_KEY, ...inboxAccounts])
    setActiveInbox((prev) =>
      prev !== '' && valid.has(prev) ? prev : ALL_INBOXES_TAB_KEY,
    )
  }, [inboxAccounts])

  const selectedEmail: DigestEmail | undefined = useMemo(() => {
    if (!digest || !decodedId) return undefined
    return digest.emails.find((e) => e.id === decodedId)
  }, [digest, decodedId])

  const listEmails: DigestEmail[] = useMemo(() => {
    const sorted = sortEmailsByImportance(emailsWithInbox)
    if (
      inboxAccounts.length <= 1 ||
      activeInbox === '' ||
      activeInbox === ALL_INBOXES_TAB_KEY
    ) {
      return sorted
    }
    return sorted.filter((e) => e.account.trim() === activeInbox)
  }, [emailsWithInbox, inboxAccounts, activeInbox])

  return (
    <AppShell title={decodedId ? `Digest · ${decodedId}` : 'Digest'} titleLarge>
      <div className="digest-toolbar">
        <Link to="/" className="digest-back-link">
          ← Home
        </Link>
        {decodedId ? (
          <>
            <span className="digest-toolbar__sep" aria-hidden="true">
              ·
            </span>
            <Link to="/digest" className="digest-back-link">
              All emails
            </Link>
          </>
        ) : null}
      </div>
      {loadState === 'loading' ? (
        <p className="digest-grabbing" role="status" aria-live="polite">
          Grabbing your digest from the server. Hang tight — this usually only takes a
          moment.
        </p>
      ) : null}
      {loadState === 'error' && error ? <p className="request-error">{error}</p> : null}
      {loadState === 'success' && digest && !decodedId ? (
        <>
          {inboxAccounts.length > 1 ? (
            <div
              className="digest-inbox-tabs"
              role="tablist"
              aria-label="Filter by inbox"
            >
              <button
                type="button"
                role="tab"
                aria-selected={activeInbox === ALL_INBOXES_TAB_KEY}
                id="digest-tab-all-inboxes"
                tabIndex={activeInbox === ALL_INBOXES_TAB_KEY ? 0 : -1}
                className={
                  activeInbox === ALL_INBOXES_TAB_KEY
                    ? 'digest-inbox-tab digest-inbox-tab--active'
                    : 'digest-inbox-tab'
                }
                onClick={() => setActiveInbox(ALL_INBOXES_TAB_KEY)}
              >
                {tabLabels[ALL_INBOXES_TAB_KEY] ?? 'All inboxes'}
              </button>
              {inboxAccounts.map((acc) => {
                const selected = activeInbox === acc
                const defaultLabel = accountTabLabel(acc)
                return (
                  <button
                    key={acc}
                    type="button"
                    role="tab"
                    aria-selected={selected}
                    id={`digest-tab-${encodeURIComponent(acc)}`}
                    tabIndex={selected ? 0 : -1}
                    className={
                      selected ? 'digest-inbox-tab digest-inbox-tab--active' : 'digest-inbox-tab'
                    }
                    onClick={() => setActiveInbox(acc)}
                  >
                    {tabLabels[acc] ?? defaultLabel}
                  </button>
                )
              })}
            </div>
          ) : null}
          <div className="digest-cards" role="feed" aria-label="Emails in this digest">
            {listEmails.map((email) => (
              <DigestEmailCard key={email.id} email={email} />
            ))}
          </div>
        </>
      ) : null}
      {loadState === 'success' && digest && decodedId ? (
        selectedEmail ? (
          <div className="digest-cards">
            <DigestEmailCard email={selectedEmail} />
          </div>
        ) : (
          <p className="request-error" role="status">
            No email with id <code className="digest-inline-code">{decodedId}</code> in the
            latest digest.
          </p>
        )
      ) : null}
    </AppShell>
  )
}
