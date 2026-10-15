import { useCallback, useEffect, useState } from 'react'
import type { FunctionSlot, MaterializeResult, SlotsList } from '../types'

type SlotsState =
  | { kind: 'loading' }
  | { kind: 'ok'; slots: FunctionSlot[] }
  | { kind: 'forbidden' }
  | { kind: 'not_found' }
  | { kind: 'error'; message: string }

export default function SlotsPanel({
  roomId,
  staffingUnlocked,
}: {
  roomId: string
  staffingUnlocked: boolean
}) {
  const [state, setState] = useState<SlotsState>({ kind: 'loading' })
  const [busy, setBusy] = useState(false)

  const loadSlots = useCallback(() => {
    const controller = new AbortController()
    setState({ kind: 'loading' })
    fetch(`/api/v1/rooms/${encodeURIComponent(roomId)}/slots`, {
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

  useEffect(() => {
    if (!staffingUnlocked) return
    return loadSlots()
  }, [staffingUnlocked, loadSlots])

  async function materialize() {
    setBusy(true)
    try {
      const res = await fetch(
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
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  )
}
