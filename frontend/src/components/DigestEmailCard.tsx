import { Link } from 'react-router-dom'
import type { DigestEmail } from '../types/digest'
import { formatReceivedAtPacific } from '../utils/formatReceivedAtPt'
import { parseSenderParts } from '../utils/parseSender'

type Props = {
  email: DigestEmail
  /** When true, omit the link to the single-email route (e.g. already on detail view). */
  hideDetailLink?: boolean
}

function importanceClass(importance: string): string {
  const n = importance.trim().toLowerCase()
  if (n === 'high') return 'digest-email-card--high'
  if (n === 'medium') return 'digest-email-card--medium'
  if (n === 'low') return 'digest-email-card--low'
  return 'digest-email-card--medium'
}

export function DigestEmailCard({ email, hideDetailLink }: Props) {
  const imp = importanceClass(email.importance)
  const timeLabel = formatReceivedAtPacific(email.received_at)
  const headingId = `email-heading-${email.id}`
  const { display: senderDisplay, address: senderAddress } = parseSenderParts(
    email.sender,
  )

  return (
    <article
      className={`digest-email-card ${imp}`}
      aria-labelledby={headingId}
    >
      <header className="digest-email-card__header">
        <div className="digest-email-card__titles">
          <h2 className="digest-email-card__sender" id={headingId}>
            {senderDisplay}
          </h2>
          <h3 className="digest-email-card__subject">{email.subject}</h3>
        </div>
        {!hideDetailLink ? (
          <Link
            to={`/digest/${encodeURIComponent(email.id)}`}
            className="digest-email-card__link"
          >
            Open
          </Link>
        ) : null}
      </header>
      <div className="digest-email-card__body">
        <p className="digest-email-card__summary">{email.summary}</p>
      </div>
      <footer className="digest-email-card__footer">
        <div className="digest-email-card__mailto-wrap">
          {senderAddress ? (
            <a
              href={`mailto:${senderAddress}`}
              className="digest-email-card__mailto"
            >
              {senderAddress}
            </a>
          ) : null}
        </div>
        <time
          className="digest-email-card__time"
          dateTime={email.received_at}
          title={email.received_at}
        >
          {timeLabel}
        </time>
      </footer>
    </article>
  )
}
