import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { RosterMember, RosterUpsertResult } from '../types'

type RosterState =
  | { kind: 'loading' }
  | { kind: 'ok'; members: RosterMember[] }
  | { kind: 'error'; message: string }

/** Local roster (C6): stub upsert a freelancer, list for the Slot assign picker. */
export default function RosterPanel({ onChanged }: { onChanged?: () => void }) {
  const [state, setState] = useState<RosterState>({ kind: 'loading' })
  const [sub, setSub] = useState('')
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadRoster = useCallback(() => {
    const controller = new AbortController()
    setState({ kind: 'loading' })
    apiFetch('/api/v1/roster', { signal: controller.signal })
      .then(async (res) => {
        if (!res.ok) {
          setState({ kind: 'error', message: `HTTP ${res.status}` })
          return
        }
        const body = (await res.json()) as { members: RosterMember[] }
        setState({ kind: 'ok', members: body.members })
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        setState({
          kind: 'error',
          message: err instanceof Error ? err.message : 'Request failed',
        })
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    return loadRoster()
  }, [loadRoster])

  async function upsert(event: React.FormEvent) {
    event.preventDefault()
    const trimmedSub = sub.trim()
    const trimmedName = name.trim()
    if (!trimmedSub || !trimmedName) return
    setBusy(true)
    setError(null)
    setMessage(null)
    try {
      const res = await apiFetch('/internal/v1/roster', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          freelancer_sub: trimmedSub,
          display_name: trimmedName,
        }),
      })
      if (res.status === 422) {
        setError('Validation failed (422).')
        return
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const body = (await res.json()) as RosterUpsertResult
      setMessage(
        body.status === 'already_exists'
          ? `Already in roster: ${body.freelancer_sub}`
          : `Upserted: ${body.freelancer_sub}`,
      )
      setSub('')
      setName('')
      loadRoster()
      onChanged?.()
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="block roster-block">
      <h2>Roster</h2>
      <form className="roster-form" onSubmit={upsert}>
        <input
          type="text"
          value={sub}
          placeholder="freelancer_sub"
          onChange={(e) => setSub(e.target.value)}
          disabled={busy}
        />
        <input
          type="text"
          value={name}
          placeholder="Display name"
          onChange={(e) => setName(e.target.value)}
          disabled={busy}
        />
        <button type="submit" className="slot-action" disabled={busy || !sub.trim() || !name.trim()}>
          Upsert
        </button>
        <button
          type="button"
          className="slot-action"
          onClick={loadRoster}
          disabled={busy}
        >
          Refresh
        </button>
      </form>
      {state.kind === 'loading' && <p className="hint">Loading roster…</p>}
      {state.kind === 'error' && <p className="error">{state.message}</p>}
      {state.kind === 'ok' && state.members.length === 0 && (
        <p className="hint">Roster empty.</p>
      )}
      {state.kind === 'ok' && state.members.length > 0 && (
        <ul className="roster-list">
          {state.members.map((m) => (
            <li key={m.freelancer_sub}>
              <strong>{m.display_name}</strong>{' '}
              <span className="hint">{m.freelancer_sub}</span>
            </li>
          ))}
        </ul>
      )}
      {message ? <p className="hint">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}
    </section>
  )
}
