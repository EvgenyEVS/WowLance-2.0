import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { RoomHealth, RoomHealthPublishResult } from '../types'

/** C13: read-only health aggregate + stub publish to the Strategy outbox. */
export default function RoomHealthPanel({ roomId }: { roomId: string }) {
  const [health, setHealth] = useState<RoomHealth | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [lastOutboxId, setLastOutboxId] = useState<string | null>(null)

  const load = useCallback(() => {
    const controller = new AbortController()
    apiFetch(`/api/v1/rooms/${encodeURIComponent(roomId)}/health`, {
      signal: controller.signal,
    })
      .then(async (res) => {
        if (controller.signal.aborted) return
        if (!res.ok) {
          setError(`HTTP ${res.status}`)
          return
        }
        setHealth((await res.json()) as RoomHealth)
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        setError(err instanceof Error ? err.message : 'Request failed')
      })
    return () => controller.abort()
  }, [roomId])

  useEffect(() => {
    return load()
  }, [load])

  async function publish() {
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/internal/v1/rooms/${encodeURIComponent(roomId)}/health/publish`,
        { method: 'POST' },
      )
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const body = (await res.json()) as RoomHealthPublishResult
      setHealth(body.snapshot)
      setLastOutboxId(body.outbox_id)
    } finally {
      setBusy(false)
    }
  }

  if (!health) {
    return (
      <section className="block">
        <h2>Room health</h2>
        {error ? <p className="error">{error}</p> : <p className="hint">Loading health…</p>}
      </section>
    )
  }

  const { slots, tasks, leads } = health
  return (
    <section className="block">
      <h2>Room health</h2>
      <dl className="meta">
        <dt>Slots</dt>
        <dd>
          {slots.filled}/{slots.total} filled · {slots.open} open · {slots.cancelled}{' '}
          cancelled
        </dd>
        <dt>Tasks</dt>
        <dd>
          {tasks.todo} todo · {tasks.in_progress} in progress · {tasks.submitted}{' '}
          submitted · {tasks.done} done
        </dd>
        <dt>Leads</dt>
        <dd>
          {leads.total} total · {leads.hot} hot · {leads.handed_to_crm} handed
        </dd>
        <dt>Earned</dt>
        <dd>
          {health.earnings.total_amount} {health.earnings.currency} ·
          {health.earnings.entries_count} entries
        </dd>
        <dt>Captured</dt>
        <dd>{new Date(health.captured_at).toLocaleString()}</dd>
      </dl>
      <button type="button" className="slot-action" disabled={busy} onClick={() => void load()}>
        Refresh
      </button>{' '}
      <button
        type="button"
        className="slot-action"
        disabled={busy}
        onClick={() => void publish()}
      >
        Publish snapshot
      </button>
      {lastOutboxId ? (
        <p className="hint">Published to outbox: {lastOutboxId}</p>
      ) : null}
      {error ? <p className="error">{error}</p> : null}
    </section>
  )
}
