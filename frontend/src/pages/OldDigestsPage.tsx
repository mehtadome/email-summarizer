import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { DigestEmailListBody } from '../components/DigestEmailListBody'
import {
  fetchDigestByFilename,
  fetchDigests,
  type DigestListItem,
} from '../api/digests'
import type { Digest } from '../types/digest'
import { formatDigestTabLabel } from '../utils/formatDigestTabLabel'

export function OldDigestsPage() {
  const { filename: filenameParam } = useParams<{ filename?: string }>()
  const navigate = useNavigate()

  const [list, setList] = useState<DigestListItem[] | null>(null)
  const [listError, setListError] = useState<string | null>(null)
  const [selectedFilename, setSelectedFilename] = useState<string | null>(null)
  const [digest, setDigest] = useState<Digest | null>(null)
  const [digestError, setDigestError] = useState<string | null>(null)
  const [digestLoading, setDigestLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const items = await fetchDigests()
        if (!cancelled) {
          setList(items)
          setListError(null)
        }
      } catch {
        if (!cancelled) {
          setList([])
          setListError(
            'Could not load digest list. Is the API running on port 8000?',
          )
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const decodedParam = useMemo(() => {
    if (!filenameParam) return null
    try {
      return decodeURIComponent(filenameParam)
    } catch {
      return null
    }
  }, [filenameParam])

  useEffect(() => {
    if (!list?.length) return

    const valid =
      decodedParam && list.some((x) => x.filename === decodedParam)
        ? decodedParam
        : null

    if (valid) {
      setSelectedFilename(valid)
      return
    }

    const first = list[0].filename
    setSelectedFilename(first)
    navigate(`/old-digests/${encodeURIComponent(first)}`, { replace: true })
  }, [list, decodedParam, navigate])

  useEffect(() => {
    if (!selectedFilename) return

    let cancelled = false
    setDigestLoading(true)
    setDigestError(null)
    setDigest(null)

    ;(async () => {
      try {
        const d = await fetchDigestByFilename(selectedFilename)
        if (!cancelled) {
          setDigest(d)
          setDigestError(null)
        }
      } catch {
        if (!cancelled) {
          setDigest(null)
          setDigestError('Could not load this digest file.')
        }
      } finally {
        if (!cancelled) {
          setDigestLoading(false)
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [selectedFilename])

  function selectDigest(filename: string) {
    setSelectedFilename(filename)
    navigate(`/old-digests/${encodeURIComponent(filename)}`)
  }

  return (
    <AppShell title="Old digests" titleLarge>
      <div className="digest-toolbar">
        <Link to="/" className="digest-back-link">
          ← Home
        </Link>
        <span className="digest-toolbar__sep" aria-hidden="true">
          ·
        </span>
        <Link to="/digest" className="digest-back-link">
          Latest digest
        </Link>
      </div>

      {listError ? <p className="request-error">{listError}</p> : null}

      {list === null ? (
        <p className="digest-grabbing" role="status" aria-live="polite">
          Loading digest list…
        </p>
      ) : null}

      {list && list.length === 0 && !listError ? (
        <p className="digest-grabbing" role="status">
          No saved digests yet. Run a digest (e.g. from the home page) to build
          history here.
        </p>
      ) : null}

      {list && list.length > 0 ? (
        <>
          <div
            className="digest-archive-tabs"
            role="tablist"
            aria-label="Saved digests by run time"
          >
            {list.map((item) => {
              const selected = item.filename === selectedFilename
              return (
                <button
                  key={item.filename}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  id={`digest-archive-tab-${encodeURIComponent(item.filename)}`}
                  tabIndex={selected ? 0 : -1}
                  className={
                    selected
                      ? 'digest-archive-tab digest-archive-tab--active'
                      : 'digest-archive-tab'
                  }
                  onClick={() => selectDigest(item.filename)}
                >
                  {formatDigestTabLabel(item)}
                </button>
              )
            })}
          </div>

          {digestLoading ? (
            <p className="digest-grabbing" role="status" aria-live="polite">
              Loading this digest…
            </p>
          ) : null}

          {digestError ? <p className="request-error">{digestError}</p> : null}

          {!digestLoading && digest ? (
            <DigestEmailListBody key={selectedFilename ?? 'digest'} digest={digest} />
          ) : null}
        </>
      ) : null}
    </AppShell>
  )
}
