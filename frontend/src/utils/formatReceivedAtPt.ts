/** Format an email `received_at` string for display in America/Los_Angeles, 12-hour clock. */
export function formatReceivedAtPacific(receivedAt: string): string {
  const ms = Date.parse(receivedAt)
  if (Number.isNaN(ms)) {
    return receivedAt
  }
  const d = new Date(ms)
  const formatted = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Los_Angeles',
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(d)
  return `${formatted} PT`
}
