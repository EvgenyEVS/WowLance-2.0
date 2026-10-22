import { useState } from 'react'
import { apiFetch } from '../api'
import type { RoomRead } from '../types'

/** Fallback actor for AUTH_DISABLED=true; ignored by the backend when a JWT is sent. */
const ACTOR_SUB = 'teamlead-demo-sub'

export default function PendingStrategyPanel({
  room,
  onDecided,
  canStaff = true,
}: {
  room: RoomRead
  onDecided: () => void
  canStaff?: boolean
}) {
  const pending = room.pending_strategy
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!pending) return null
  const proposalId = pending.proposal_id

  async function decide(kind: 'accept' | 'reject') {
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(room.id)}/strategy-proposals/${proposalId}/${kind}`,
        {
          method: 'POST',
          headers: { 'X-Actor-Sub': ACTOR_SUB },
        },
      )
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      onDecided()
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="block pending-block">
      <h2>Pending strategy v{pending.strategy_version}</h2>
      <p>
        <strong>Offer.</strong> {pending.offer}
      </p>
      <p>
        <strong>Audience.</strong> {pending.audience}
      </p>
      <p>
        <strong>Hot criteria.</strong> {pending.hot_criteria}
      </p>
      {canStaff ? (
      <div className="pending-actions">
        <button
          type="button"
          className="slot-action"
          disabled={busy}
          onClick={() => void decide('accept')}
        >
          Accept
        </button>
        <button
          type="button"
          className="ghost-action"
          disabled={busy}
          onClick={() => void decide('reject')}
        >
          Reject
        </button>
      </div>
      ) : (
        <p className="hint">Accept/Reject hidden for member role.</p>
      )}
      {error ? <p className="error">{error}</p> : null}
    </section>
  )
}
