import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { DigestEmailCard } from '../components/DigestEmailCard'
import { fetchLatestDigest } from '../api'
import type { Digest, DigestEmail } from '../types/digest'
import { sortEmailsByImportance } from '../utils/sortByImportance'

type LoadState = 'loading' | 'success' | 'error'

export function DigestPage() {
  const { emailId } = useParams<{ emailId?: string }>()
  const decodedId = emailId ? decodeURIComponent(emailId) : undefined

  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [digest, setDigest] = useState<Digest | null>(null)
  const [error, setError] = useState<string | null>(null)

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

  const selectedEmail: DigestEmail | undefined = useMemo(() => {
    if (!digest || !decodedId) return undefined
    return digest.emails.find((e) => e.id === decodedId)
  }, [digest, decodedId])

  const listEmails: DigestEmail[] = useMemo(() => {
    if (!digest) return []
    return sortEmailsByImportance(digest.emails)
  }, [digest])

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
        <div className="digest-cards" role="feed" aria-label="Emails in this digest">
          {listEmails.map((email) => (
            <DigestEmailCard key={email.id} email={email} />
          ))}
        </div>
      ) : null}
      {loadState === 'success' && digest && decodedId ? (
        selectedEmail ? (
          <div className="digest-cards">
            <DigestEmailCard email={selectedEmail} hideDetailLink />
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
