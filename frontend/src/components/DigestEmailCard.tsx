import { Link } from 'react-router-dom'
import type { DigestEmail } from '../types/digest'

type Props = {
  email: DigestEmail
  /** When true, omit the link to the single-email route (e.g. already on detail view). */
  hideDetailLink?: boolean
}

export function DigestEmailCard({ email, hideDetailLink }: Props) {
  const json = JSON.stringify(email, null, 2)

  return (
    <article className="digest-email-card" aria-labelledby={`email-heading-${email.id}`}>
      <header className="digest-email-card__header">
        <h2 className="digest-email-card__title" id={`email-heading-${email.id}`}>
          {email.id}
        </h2>
        {!hideDetailLink ? (
          <Link to={`/digest/${encodeURIComponent(email.id)}`} className="digest-email-card__link">
            Open
          </Link>
        ) : null}
      </header>
      <pre className="digest-json digest-email-card__pre" aria-label={`Raw JSON for email ${email.id}`}>
        {json}
      </pre>
    </article>
  )
}
