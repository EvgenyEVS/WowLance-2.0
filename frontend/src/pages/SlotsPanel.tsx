import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type {
  FunctionSlot,
  MatchCandidate,
  MaterializeResult,
  RosterMember,
  SlotAssignResult,
  SlotMatchResult,
  SlotReassignResult,
  SlotUnassignResult,
  SlotsList,
} from '../types'

/** Fallback actor for AUTH_DISABLED=true; ignored by the backend when a JWT is sent. */
const ACTOR_SUB = 'teamlead-demo-sub'

type SlotsState =
  | { kind: 'loading' }
  | { kind: 'ok'; slots: FunctionSlot[] }
  | { kind: 'forbidden' }
  | { kind: 'not_found' }
  | { kind: 'error'; message: string }

export default function SlotsPanel({
  roomId,
  staffingUnlocked,
  rosterVersion = 0,
}: {
  roomId: string
  staffingUnlocked: boolean
  rosterVersion?: number
}) {
  const [state, setState] = useState<SlotsState>({ kind: 'loading' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [roster, setRoster] = useState<RosterMember[]>([])
  const [picked, setPicked] = useState<Record<string, string>>({})
  const [matchResults, setMatchResults] = useState<Record<string, { candidates: MatchCandidate[] }>>({})

  const loadSlots = useCallback(() => {
    const controller = new AbortController()
    setState({ kind: 'loading' })
    setMatchResults({})
    apiFetch(`/api/v1/rooms/${encodeURIComponent(roomId)}/slots`, {
      signal: controller.signal,
    })
      .then(async (res) => {
        if (res.status === 403) {
          setState({ kind: 'forbidden' })
          return
        }
        if (res.status === 404) {
          setState({ kind: 'not_found' })
          return
        }
        if (!res.ok) {
          setState({ kind: 'error', message: `HTTP ${res.status}` })
          return
        }
        const body = (await res.json()) as SlotsList
        setState({ kind: 'ok', slots: body.slots })
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        setState({
          kind: 'error',
          message: err instanceof Error ? err.message : 'Request failed',
        })
      })
    return () => controller.abort()
  }, [roomId])

  const loadRoster = useCallback(() => {
    apiFetch('/api/v1/roster')
      .then(async (res) => {
        if (!res.ok) return
        const body = (await res.json()) as { members: RosterMember[] }
        setRoster(body.members)
      })
      .catch(() => undefined)
  }, [])

  useEffect(() => {
    if (!staffingUnlocked) return
    loadRoster()
    return loadSlots()
  }, [staffingUnlocked, loadSlots, loadRoster, rosterVersion])

  async function materialize() {
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(roomId)}/slots/materialize`,
        { method: 'POST' },
      )
      if (res.status === 403) {
        setState({ kind: 'forbidden' })
        return
      }
      if (res.status === 404) {
        setState({ kind: 'not_found' })
        return
      }
      if (!res.ok) {
        setState({ kind: 'error', message: `HTTP ${res.status}` })
        return
      }
      const body = (await res.json()) as MaterializeResult
      setState({ kind: 'ok', slots: body.slots })
    } finally {
      setBusy(false)
    }
  }

  async function suggest(slot: FunctionSlot) {
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(roomId)}/slots/${encodeURIComponent(
          slot.id,
        )}/match`,
      )
      if (res.status === 403) {
        setError('Staffing locked (403).')
        return
      }
      if (res.status === 404) {
        setError('Slot not found (404).')
        return
      }
      if (res.status === 409) {
        setError('Slot is not open (409).')
        return
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const body = (await res.json()) as SlotMatchResult
      setMatchResults((prev) => ({ ...prev, [slot.id]: { candidates: body.candidates } }))
    } finally {
      setBusy(false)
    }
  }

  function patchSlot(body: { slot: FunctionSlot }) {
    setState((prev) =>
      prev.kind === 'ok'
        ? {
            kind: 'ok',
            slots: prev.slots.map((s) => (s.id === body.slot.id ? body.slot : s)),
          }
        : prev,
    )
  }

  async function assign(slot: FunctionSlot) {
    const freelancerSub = (picked[slot.id] ?? '').trim()
    if (!freelancerSub) return
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(roomId)}/slots/${encodeURIComponent(
          slot.id,
        )}/assign`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Actor-Sub': ACTOR_SUB,
          },
          body: JSON.stringify({ freelancer_sub: freelancerSub }),
        },
      )
      if (res.status === 403) {
        setError('Staffing locked (403).')
        return
      }
      if (res.status === 404) {
        setError('Slot or freelancer not found (404). Upsert into roster first.')
        return
      }
      if (res.status === 409) {
        setError('Slot already filled or freelancer already seated (409).')
        loadSlots()
        return
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const body = (await res.json()) as SlotAssignResult
      patchSlot(body)
    } finally {
      setBusy(false)
    }
  }

  async function unassign(slot: FunctionSlot) {
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(roomId)}/slots/${encodeURIComponent(
          slot.id,
        )}/unassign`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Actor-Sub': ACTOR_SUB,
          },
        },
      )
      if (res.status === 403) {
        setError('Staffing locked (403).')
        return
      }
      if (res.status === 404) {
        setError('Slot not found (404).')
        return
      }
      if (res.status === 409) {
        setError('Slot is not filled (409).')
        loadSlots()
        return
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const body = (await res.json()) as SlotUnassignResult
      patchSlot(body)
    } finally {
      setBusy(false)
    }
  }

  async function reassign(slot: FunctionSlot) {
    const freelancerSub = (picked[slot.id] ?? '').trim()
    if (!freelancerSub) return
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(roomId)}/slots/${encodeURIComponent(
          slot.id,
        )}/reassign`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Actor-Sub': ACTOR_SUB,
          },
          body: JSON.stringify({ freelancer_sub: freelancerSub }),
        },
      )
      if (res.status === 403) {
        setError('Staffing locked (403).')
        return
      }
      if (res.status === 404) {
        setError('Slot or freelancer not found (404). Upsert into roster first.')
        return
      }
      if (res.status === 409) {
        setError('Slot not filled or freelancer already seated (409).')
        loadSlots()
        return
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const body = (await res.json()) as SlotReassignResult
      patchSlot(body)
    } finally {
      setBusy(false)
    }
  }

  async function terminate(slot: FunctionSlot) {
    const reason = window.prompt('Причина расторжения (обязательно):')
    if (reason === null || !reason.trim()) return
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(roomId)}/members/${encodeURIComponent(
          slot.freelancer_sub ?? ''
        )}/terminate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Actor-Sub': ACTOR_SUB,
          },
          body: JSON.stringify({ reason: reason.trim() }),
        },
      )
      if (res.status === 404) {
        setError('Member not seated (404). Reload the list.')
        loadSlots()
        return
      }
      if (res.status === 409) {
        setError('Slot not filled (409). Reload the list.')
        loadSlots()
        return
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      patchSlot({ slot: { ...slot, status: 'open', freelancer_sub: null } })
      loadSlots()
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="block">
      <h2>Slots</h2>
      {!staffingUnlocked ? (
        <p className="hint">Slots locked until entitlement</p>
      ) : (
        <>
          <button
            type="button"
            className="slot-action"
            onClick={() => void materialize()}
            disabled={busy}
          >
            Materialize slots
          </button>
          {state.kind === 'loading' && <p className="hint">Loading slots…</p>}
          {state.kind === 'forbidden' && (
            <p className="error">Slots locked (403).</p>
          )}
          {state.kind === 'not_found' && (
            <p className="error">Room not found (404).</p>
          )}
          {state.kind === 'error' && <p className="error">{state.message}</p>}
          {state.kind === 'ok' && state.slots.length === 0 && (
            <p className="hint">No seats in staffing intent.</p>
          )}
          {state.kind === 'ok' && state.slots.length > 0 && (
            <ul className="slot-list">
              {state.slots.map((slot) => (
                <li key={slot.id}>
                  <strong>{slot.role_key}</strong> #{slot.seat_index}{' '}
                  <span className="hint">{slot.status}</span>
                  {slot.status === 'open' ? (
                    <>
                      <button
                        type="button"
                        className="slot-action"
                        disabled={busy}
                        onClick={() => void suggest(slot)}
                      >
                        Suggest
                      </button>
                      {matchResults[slot.id] && (
                        <ul className="slot-list">
                          {matchResults[slot.id].candidates.map((c) => (
                            <li key={c.freelancer_sub}>
                              {c.display_name} ({c.freelancer_sub}) — score {c.score}{' '}
                              {c.skills?.join(', ') ?? ''}
                              <button
                                type="button"
                                className="slot-action"
                                disabled={busy || !(picked[slot.id] ?? '').trim()}
                                onClick={() => {
                                  setPicked((prev) => ({ ...prev, [slot.id]: c.freelancer_sub }))
                                }}
                              >
                                Pick
                              </button>
                            </li>
                          ))}
                        </ul>
                      )}
                      <select
                        value={picked[slot.id] ?? ''}
                        onChange={(e) =>
                          setPicked((prev) => ({ ...prev, [slot.id]: e.target.value }))
                        }
                        disabled={busy}
                      >
                        <option value="">Pick freelancer…</option>
                        {roster.map((m) => (
                          <option key={m.freelancer_sub} value={m.freelancer_sub}>
                            {m.display_name} ({m.freelancer_sub})
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        className="slot-action"
                        disabled={busy || !(picked[slot.id] ?? '').trim()}
                        onClick={() => void assign(slot)}
                      >
                        Assign
                      </button>
                    </>
                  ) : slot.status === 'filled' ? (
                    <>
                      <span className="hint"> → {slot.freelancer_sub}</span>
                      <button
                        type="button"
                        className="slot-action"
                        disabled={busy}
                        onClick={() => void unassign(slot)}
                      >
                        Unassign
                      </button>
                      <button
                        type="button"
                        className="slot-action"
                        disabled={busy}
                        onClick={() => void terminate(slot)}
                      >
                        Terminate
                      </button>
                      <select
                        value={picked[slot.id] ?? ''}
                        onChange={(e) =>
                          setPicked((prev) => ({ ...prev, [slot.id]: e.target.value }))
                        }
                        disabled={busy}
                      >
                        <option value="">Reassign to…</option>
                        {roster
                          .filter((m) => m.freelancer_sub !== slot.freelancer_sub)
                          .map((m) => (
                            <option key={m.freelancer_sub} value={m.freelancer_sub}>
                              {m.display_name} ({m.freelancer_sub})
                            </option>
                          ))}
                      </select>
                      <button
                        type="button"
                        className="slot-action"
                        disabled={busy || !(picked[slot.id] ?? '').trim()}
                        onClick={() => void reassign(slot)}
                      >
                        Reassign
                      </button>
                    </>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
          {roster.length === 0 ? (
            <p className="hint">Roster empty — add a freelancer above (or via curl).</p>
          ) : null}
          {error ? <p className="error">{error}</p> : null}
        </>
      )}
    </section>
  )
}
