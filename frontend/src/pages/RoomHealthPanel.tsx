import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { RoomHealth, RoomHealthPublishResult } from '../types'

/**
 * C13 + C36: read-only health aggregate + stub publish to the Strategy outbox.
 * `refreshKey` lets the room page re-read health after a task Accept so the
 * Earned total here never contradicts the Earned block.
 */
export default function RoomHealthPanel({
  roomId,
  refreshKey = 0,
}: {
  roomId: string
  refreshKey?: number
}) {
  const [health, setHealth] = useState<RoomHealth | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [lastOutboxId, setLastOutboxId] = useState<string | null>(null)

  const load = useCallback(() => {
    setError(null)
    setBusy(true)
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
      .finally(() => {
        if (!controller.signal.aborted) setBusy(false)
      })
    return () => controller.abort()
  }, [roomId])

  useEffect(() => {
    return load()
  }, [load, refreshKey])

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
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Publish failed')
    } finally {
      setBusy(false)
    }
  }

  if (!health) {
    return (
      <section className="block">
        <h2>Room health</h2>
        {error ? (
          <>
            <p className="error">{error}</p>
            <button
              type="button"
              className="slot-action"
              disabled={busy}
              onClick={() => void load()}
            >
              Retry
            </button>
          </>
        ) : (
          <p className="hint">Loading health…</p>
        )}
      </section>
    )
  }

  const { slots, tasks, leads, earnings } = health
  return (
    <section className="block">
      <h2>Room health</h2>
      <div className="health-grid">
        <div className="health-stat">
          <span className="health-label">Slots</span>
          <span className="health-value">
            {slots.filled}/{slots.total} filled
          </span>
          <span className="health-sub">
            {slots.open} open · {slots.cancelled} cancelled
          </span>
        </div>
        <div className="health-stat">
          <span className="health-label">Tasks</span>
          <span className="health-value">{tasks.done} done</span>
          <span className="health-sub">
            {tasks.todo} todo · {tasks.in_progress} in progress · {tasks.submitted}{' '}
            submitted
          </span>
        </div>
        <div className="health-stat">
          <span className="health-label">Leads</span>
          <span className="health-value">{leads.total} total</span>
          <span className="health-sub">
            {leads.hot} hot · {leads.handed_to_crm} handed
          </span>
        </div>
        <div className="health-stat">
          <span className="health-label">Earned</span>
          <span className="health-value">
            {earnings.total_amount} {earnings.currency}
          </span>
          <span className="health-sub">{earnings.entries_count} entries</span>
        </div>
      </div>
      <p className="hint health-captured">
        Snapshot: {new Date(health.captured_at).toLocaleString()}
      </p>
      <div className="health-actions">
        <button
          type="button"
          className="slot-action"
          disabled={busy}
          onClick={() => void load()}
        >
          {busy ? 'Refreshing…' : 'Refresh'}
        </button>
        <button
          type="button"
          className="slot-action"
          disabled={busy}
          onClick={() => void publish()}
        >
          Publish snapshot
        </button>
      </div>
      {lastOutboxId ? (
        <p className="hint">
          outbox stub → Strategy (не live) · outbox_id: <code>{lastOutboxId}</code>
        </p>
      ) : (
        <p className="hint">
          Publish пишет outbox stub → Strategy (не live), без live-витрины.
        </p>
      )}
      {error ? <p className="error">{error}</p> : null}
    </section>
  )
}
