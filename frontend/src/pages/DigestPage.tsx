import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { fetchLatestDigest } from '../api'

type LoadState = 'loading' | 'success' | 'error'

export function DigestPage() {
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [jsonText, setJsonText] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await fetchLatestDigest()
        if (!cancelled) {
          setJsonText(JSON.stringify(data, null, 2))
          setLoadState('success')
          setError(null)
        }
      } catch {
        if (!cancelled) {
          setJsonText(null)
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

  return (
    <AppShell title="Digest (JSON)">
      <div className="digest-toolbar">
        <Link to="/" className="digest-back-link">
          ← Home
        </Link>
      </div>
      {loadState === 'loading' ? (
        <p className="digest-grabbing" role="status" aria-live="polite">
          Grabbing your digest from the server. Hang tight — this usually only takes a
          moment.
        </p>
      ) : null}
      {loadState === 'error' && error ? <p className="request-error">{error}</p> : null}
      {loadState === 'success' && jsonText ? (
        <pre className="digest-json" role="region" aria-label="Latest digest JSON">
          {jsonText}
        </pre>
      ) : null}
    </AppShell>
  )
}
