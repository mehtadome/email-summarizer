/** Short label for a Gmail `account` selector in tab UI (`account` must be non-empty). */
export function accountTabLabel(account: string): string {
  const a = account.trim()
  if (!a) return 'Inbox'
  if (/^\d+$/.test(a)) return `Inbox ${Number(a) + 1}`
  return a
}
