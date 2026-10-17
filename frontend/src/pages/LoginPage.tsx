import { FormEvent, useState } from 'react'
import { clearToken, getToken, setToken, tokenInfo } from '../api'

/**
 * C8 MVP login: paste an access token (OIDC code flow is out of scope for
 * this ticket — see docs/261016 - задание C8 Keycloak JWT.md, §4.7).
 */
export default function LoginPage({ needsLogin }: { needsLogin?: boolean }) {
  const [draft, setDraft] = useState('')
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const current = tokenInfo(getToken())

  function onSave(event: FormEvent) {
    event.preventDefault()
    const value = draft.trim()
    if (!value) {
      setError('Paste an access token.')
      return
    }
    if (value.split('.').length !== 3) {
      setError('Not a JWT: expected three dot-separated parts.')
      return
    }
    setToken(value)
    setDraft('')
    setSaved(true)
    setError(null)
  }

  function onClear() {
    clearToken()
    setSaved(false)
  }

  return (
    <main className="shell">
      <p className="brand">WowLance 2.0</p>
      <p className="back">
        <a href="/">← Home</a>
      </p>
      <h1>Login</h1>
      {needsLogin && (
        <p className="error">Session required: the API answered 401 (нужен login).</p>
      )}
      {current.sub ? (
        <section className="block">
          <p>
            <strong>Signed in as</strong> {current.sub}
            {current.expired ? <span className="error"> (token expired)</span> : null}
          </p>
          <button type="button" className="slot-action" onClick={onClear}>
            Sign out
          </button>
        </section>
      ) : (
        <p className="hint">No token stored yet.</p>
      )}

      <section className="block">
        <h2>Set access token</h2>
        <p className="hint">
          Paste a Keycloak access token (JWT). It is kept in memory +
          sessionStorage and sent as <code>Authorization: Bearer</code> on every
          API call.
        </p>
        <form className="open-form" onSubmit={onSave}>
          <label htmlFor="access-token">Access token</label>
          <textarea
            id="access-token"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9…"
            rows={4}
            spellCheck={false}
          />
          <button type="submit" disabled={!draft.trim()}>
            Save token
          </button>
        </form>
        {saved && !error ? (
          <p className="hint">Token saved.</p>
        ) : null}
        {error ? <p className="error">{error}</p> : null}
        <p className="hint">
          No Keycloak yet? With <code>AUTH_STUB_JWKS=true</code> on the backend,
          mint a demo token: <code>POST /auth/stub-token</code> (Swagger at{' '}
          <code>/docs</code>).
        </p>
      </section>
    </main>
  )
}
