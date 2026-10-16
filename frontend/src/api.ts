/** C8: access token storage (memory + sessionStorage) + Bearer on API calls. */

const STORAGE_KEY = 'wowlance_access_token'

let memoryToken: string | null = null

export function getToken(): string | null {
  if (memoryToken !== null) return memoryToken
  try {
    memoryToken = window.sessionStorage.getItem(STORAGE_KEY)
  } catch {
    memoryToken = null
  }
  return memoryToken
}

export function setToken(token: string): void {
  const value = token.trim()
  memoryToken = value
  try {
    window.sessionStorage.setItem(STORAGE_KEY, value)
  } catch {
    // sessionStorage unavailable (private mode) — token lives in memory only
  }
}

export function clearToken(): void {
  memoryToken = null
  try {
    window.sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}

/** Decode JWT payload for display only — no signature verification here. */
export function tokenInfo(token: string | null = getToken()): {
  sub: string | null
  expired: boolean
} {
  if (!token) return { sub: null, expired: false }
  try {
    const payload = token.split('.')[1]
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0))
    const claims = JSON.parse(new TextDecoder().decode(bytes)) as Record<string, unknown>
    const sub = typeof claims.sub === 'string' ? claims.sub : null
    const expired =
      typeof claims.exp === 'number' ? claims.exp * 1000 < Date.now() : false
    return { sub, expired }
  } catch {
    return { sub: null, expired: false }
  }
}

/**
 * All API calls go through here: adds `Authorization: Bearer` when a token
 * is stored. On 401 dispatches `wowlance:unauthorized` (App switches to
 * Login). With AUTH_DISABLED=true on the backend the header is simply
 * unused — local demo keeps working without any token.
 */
export async function apiFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers)
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(input, { ...init, headers })
  if (res.status === 401) {
    window.dispatchEvent(new CustomEvent('wowlance:unauthorized'))
  }
  return res
}
