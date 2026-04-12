/** Empty string uses same-origin `/api` (Vite dev proxy → backend). */
export const API_BASE = (
  import.meta.env.VITE_API_BASE_URL as string | undefined
)?.replace(/\/$/, '') ?? ''
