import { useEffect, useMemo, useState } from 'react'
import { DigestEmailCard } from './DigestEmailCard'
import { ALL_INBOXES_TAB_KEY } from '../constants/digestInbox'
import { useTabLabels } from '../contexts/TabLabelsContext'
import type { Digest, DigestEmail } from '../types/digest'
import { accountTabLabel } from '../utils/accountTabLabel'
import { uniqueNonEmptyAccounts } from '../utils/inboxAccounts'
import { sortEmailsByImportance } from '../utils/sortByImportance'

type Props = {
  digest: Digest
}

export function DigestEmailListBody({ digest }: Props) {
  const { labels: tabLabels } = useTabLabels()
  const [activeInbox, setActiveInbox] = useState(ALL_INBOXES_TAB_KEY)

  const emailsWithInbox = useMemo(() => {
    if (!digest.emails.length) return []
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
            id="digest-list-tab-all-inboxes"
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
                id={`digest-list-tab-${encodeURIComponent(acc)}`}
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
  )
}
