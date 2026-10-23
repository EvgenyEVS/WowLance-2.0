import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type {
  FunctionSlot,
  MatchCandidate,
  MaterializeResult,
  RosterMember,
  RematerializeResult,
  SlotAssignResult,
  SlotMatchResult,
  SlotReassignResult,
  SlotUnassignResult,
  SlotsList,
} from '../types'

/** Fallback actor for AUTH_DISABLED=true; ignored by the backend when a JWT is sent. */
const ACTOR_SUB = 'teamlead-demo-sub'

type StaffErrKind =
  | 'assign'
  | 'unassign'
  | 'reassign'
  | 'terminate'
  | 'match'
  | 'materialize'

function staffHttpError(status: number, kind?: StaffErrKind): string {
  if (status === 403) return 'Forbidden (403). Staffing locked or role.'
  if (status === 404)
    return 'Not found (404). Slot or freelancer missing — upsert roster first.'
  if (status === 409) {
    if (kind === 'assign')
      return 'Slot already filled or freelancer already seated (409).'
    if (kind === 'unassign') return 'Slot is not filled (409).'
    if (kind === 'reassign')
      return 'Slot not filled or freelancer already seated (409).'
    if (kind === 'terminate') return 'Slot not filled (409). Reload the list.'
    if (kind === 'materialize') return 'Slot is not open (409).'
    return 'Conflict (409). Slot state changed — refresh the list.'
  }
  if (status === 422)
    return 'Validation (422). Check actor header and payload.'
  return `HTTP ${status}`
}

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
  canStaff = true,
}: {
  roomId: string
  staffingUnlocked: boolean
  rosterVersion?: number
  canStaff?: boolean
}) {
  const [state, setState] = useState<SlotsState>({ kind: 'loading' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [roster, setRoster] = useState<RosterMember[]>([])
  const [picked, setPicked] = useState<Record<string, string>>({})
  const [orphanedFilled, setOrphanedFilled] = useState<FunctionSlot[]>([])
  const [matchResults, setMatchResults] = useState<Record<string, { candidates: MatchCandidate[] }>>({})
  const [highlightedSlotId, setHighlightedSlotId] = useState<string | null>(null)

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
        setState({
          kind: 'error',
          message: staffHttpError(res.status, 'materialize'),
        })
        return
      }
      const body = (await res.json()) as MaterializeResult
      setState({ kind: 'ok', slots: body.slots })
    } finally {
      setBusy(false)
    }
  }

  async function rematerialize() {
    setBusy(true)
    setError(null)
    setOrphanedFilled([])
    try {
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(roomId)}/slots/rematerialize`,
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
        setState({
          kind: 'error',
          message: staffHttpError(res.status, 'materialize'),
        })
        return
      }
      const body = (await res.json()) as RematerializeResult
      setState({ kind: 'ok', slots: body.slots })
      if (body.orphaned_filled && body.orphaned_filled.length > 0) {
        setOrphanedFilled(body.orphaned_filled)
      }
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
      if (!res.ok) {
        setError(staffHttpError(res.status, 'match'))
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
      if (!res.ok) {
        setError(staffHttpError(res.status, 'assign'))
        if (res.status === 409) loadSlots()
        return
      }
      const body = (await res.json()) as SlotAssignResult
      patchSlot(body)
      loadSlots()
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
      if (!res.ok) {
        setError(staffHttpError(res.status, 'unassign'))
        if (res.status === 409) loadSlots()
        return
      }
      const body = (await res.json()) as SlotUnassignResult
      patchSlot(body)
      loadSlots()
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
      if (!res.ok) {
        setError(staffHttpError(res.status, 'reassign'))
        if (res.status === 409) loadSlots()
        return
      }
      const body = (await res.json()) as SlotReassignResult
      patchSlot(body)
      setHighlightedSlotId(body.slot.id)
      loadSlots()
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
      if (!res.ok) {
        setError(staffHttpError(res.status, 'terminate'))
        if (res.status === 404 || res.status === 409) loadSlots()
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
      <h2>
        Slots
        {state.kind === 'ok' && state.slots.length > 0
          ? ` · ${state.slots.filter((s) => s.status === 'filled').length}/${state.slots.length} занято`
          : null}
      </h2>
      {!staffingUnlocked ? (
        <p className="hint">Slots locked until entitlement</p>
      ) : (
        <>
          {canStaff ? (
            <>
          <button
            type="button"
            className="slot-action"
            onClick={() => void materialize()}
            disabled={busy}
          >
            Materialize slots
          </button>
          <button
            type="button"
            className="slot-action"
            onClick={() => void rematerialize()}
            disabled={busy}
          >
            Rematerialize
          </button>
          <p className="hint">
            Rematerialize after Accept strategy / смена functions в snapshot.
            Occupied seats that fall out of the new plan stay as orphaned — unassign or
            terminate them manually.
          </p>
            </>
          ) : null}
          {state.kind === 'loading' && <p className="hint">Loading slots…</p>}
          {state.kind === 'forbidden' && (
            <p className="error">Slots locked (403).</p>
          )}
          {state.kind === 'not_found' && (
            <p className="error">Room not found (404).</p>
          )}
          {state.kind === 'error' && <p className="error">{state.message}</p>}
          {state.kind === 'ok' && state.slots.length === 0 && (
            <p className="hint">
              No seats yet. Click Materialize after entitlement, then Assign from roster.
            </p>
          )}
          {state.kind === 'ok' && state.slots.length > 0 && (
            <ul className="slot-list">
              {state.slots.map((slot) => (
                <li
                  key={slot.id}
                  className={
                    highlightedSlotId === slot.id ? 'slot-item highlight' : 'slot-item'
                  }
                >
                  <strong>{slot.role_key}</strong> #{slot.seat_index}{' '}
                  <span className="hint">{slot.status}</span>
                  {slot.status === 'open' ? (
                    <>
                      <span className="badge unlocked">свободен</span>
                    {canStaff ? (
                    <>
                      <button
                        type="button"
                        className="slot-action"
                        disabled={busy}
                        onClick={() => void suggest(slot)}
                      >
                        Suggest
                      </button>
                      {roster.length === 0 ? (
                        <span className="hint">
                          Roster empty — upsert a freelancer first, then Suggest/Pick.
                        </span>
                      ) : null}
                      {matchResults[slot.id] && (
                        <ul className="slot-list">
                          {matchResults[slot.id].candidates.length === 0 ? (
                            <li className="hint">No candidates. Upsert roster first.</li>
                          ) : null}
                          {matchResults[slot.id].candidates.map((c) => (
                            <li key={c.freelancer_sub}>
                              {c.display_name} ({c.freelancer_sub}) — score {c.score}{' '}
                              {c.skills?.join(', ') ?? ''}
                              <button
                                type="button"
                                className="slot-action"
                                disabled={busy}
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
                    ) : null}
                    </>
                  ) : slot.status === 'filled' ? (
                    <>
                      <span className="hint"> → {slot.freelancer_sub}</span>
                      {canStaff ? (
                      <>
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
                    </>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
          {orphanedFilled.length > 0 && (
            <div className="hint orphaned-hint">
              <strong>Orphaned filled seats</strong> — вне нового плана, слот не
              удалён. Unassign или Terminate вручную:{' '}
              {orphanedFilled.map((s) => (
                <span key={s.id} className="badge locked">
                  {s.role_key} #{s.seat_index}
                </span>
              ))}
            </div>
          )}
          {roster.length === 0 ? (
            <p className="hint">
              Roster empty — upsert a freelancer in Roster, then Suggest → Pick → Assign.
            </p>
          ) : null}
          {error ? <p className="error">{error}</p> : null}
        </>
      )}
    </section>
  )
}
