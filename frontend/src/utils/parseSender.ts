/** Split RFC-style `Name <addr@domain>` into display text and address, when possible. */
export function parseSenderParts(sender: string): {
  display: string
  /** Email inside angle brackets, if present. */
  address: string | null
} {
  const trimmed = sender.trim()
  const bracket = trimmed.match(/^(.*?)\s*<([^>]+)>\s*$/)
  if (bracket) {
    const display = bracket[1].trim()
    const address = bracket[2].trim()
    return {
      display: display.length > 0 ? display : address,
      address,
    }
  }
  return { display: trimmed, address: null }
}
