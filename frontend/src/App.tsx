import { useEffect, useState } from 'react'
import { AppShell } from './components/AppShell'
import { fetchSampleText, postSampleText } from './api'
import './App.css'

const PLACEHOLDER =
  'Main content goes here. Connect this UI to your backend when you are ready.'


function App() {
  const [mainText, setMainText] = useState(PLACEHOLDER)
  const [backendInfo, setBackendInfo] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [requestError, setRequestError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    ;(async () => {
      try {
        const { text } = await fetchSampleText()
        if (!cancelled && text.length > 0) {
          setMainText(text)
        }
      } catch {
        /* keep PLACEHOLDER */
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
    <AppShell>
      <p className="lead">{mainText}</p>
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

export default App
