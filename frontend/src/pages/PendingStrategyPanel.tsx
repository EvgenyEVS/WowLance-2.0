import { useState } from 'react'
import type { RoomRead } from '../types'

/** Stub teamlead identity until Keycloak. */
const ACTOR_SUB = 'teamlead-demo-sub'

export default function PendingStrategyPanel({
  room,
  onDecided,
}: {
  room: RoomRead
  onDecided: () => void
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
      const res = await fetch(
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
      {error ? <p className="error">{error}</p> : null}
    </section>
  )
}
