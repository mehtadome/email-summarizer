import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { fetchSampleText, postSampleText, type SampleTextGetResponse } from '../api'

const PLACEHOLDER =
  'Recommendations will show here when a digest has been inferenced. Click the arrow to begin.'

function HomeDigestPreview({
  data,
  loading,
}: {
  data: SampleTextGetResponse | null
  loading: boolean
}) {
  if (loading) {
    return (
      <p className="lead home-summary--muted" role="status">
        Loading…
      </p>
    )
  }
  if (!data) {
    return <p className="lead">{PLACEHOLDER}</p>
  }

  const legacy = data.legacy_text?.trim()
  if (legacy) {
    return (
      <p className="lead" role="status">
        {legacy}
      </p>
    )
  }

  const title = data.title?.trim() ?? ''
  const hasRecs = data.recommendations.length > 0
  const hasStructured = title.length > 0 || hasRecs

  if (hasStructured) {
    return (
      <section className="home-summary" aria-label="Digest recommendations">
        {title ? <h2 className="home-summary__title">{title}</h2> : null}
        {hasRecs ? (
          <>
            <ol className="home-recommendations">
              {data.recommendations.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ol>
            <p className="home-recommendations-footnote">
              All remaining emails are marketing, promotional, or automated notifications —
              none require a response or action.
            </p>
          </>
        ) : null}
      </section>
    )
  }

  if (data.message) {
    return (
      <p className="lead" role="status">
        {data.message}
      </p>
    )
  }

  return <p className="lead">{PLACEHOLDER}</p>
}

export function HomePage() {
  const [preview, setPreview] = useState<SampleTextGetResponse | null>(null)
  const [previewLoading, setPreviewLoading] = useState(true)
  const [backendInfo, setBackendInfo] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [requestError, setRequestError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    ;(async () => {
      try {
        const data = await fetchSampleText()
        if (!cancelled) {
          setPreview(data)
        }
      } catch {
        if (!cancelled) {
          setPreview(null)
        }
      } finally {
        if (!cancelled) {
          setPreviewLoading(false)
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [])

  async function handleFetchFromBackend() {
    setLoading(true)
    setRequestError(null)
    try {
      const { text } = await postSampleText()
      setBackendInfo(text)
    } catch {
      setRequestError('Could not reach the backend. Is the API running on port 8000?')
      setBackendInfo(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell title="Email Summarizer" titleLarge>
      <div className="home-top">
        <div className="home-top__main">
          <HomeDigestPreview data={preview} loading={previewLoading} />
        </div>
        <Link
          to="/digest"
          className="digest-arrow-btn"
          title="View full digest"
          aria-label="View full digest"
        >
          →
        </Link>
      </div>
      <div className="actions">
        <button
          type="button"
          className="btn"
          disabled={loading}
          onClick={() => void handleFetchFromBackend()}
        >
          {loading ? 'Loading…' : 'Fetch digest info from backend'}
        </button>
      </div>
      {requestError ? <p className="request-error">{requestError}</p> : null}
      {backendInfo ? (
        <pre className="backend-info" role="status">
          {backendInfo}
        </pre>
      ) : null}
    </AppShell>
  )
}
