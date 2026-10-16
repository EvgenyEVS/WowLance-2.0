import { useCallback, useEffect, useState } from 'react'
import type { RoomRead } from '../types'
import LeadsPanel from './LeadsPanel'
import PendingStrategyPanel from './PendingStrategyPanel'
import RosterPanel from './RosterPanel'
import SlotsPanel from './SlotsPanel'
import TasksPanel from './TasksPanel'

type LoadState =
  | { kind: 'loading' }
  | { kind: 'ok'; room: RoomRead }
  | { kind: 'not_found' }
  | { kind: 'error'; message: string }

export default function RoomPage({ roomId }: { roomId: string }) {
  const [state, setState] = useState<LoadState>({ kind: 'loading' })

  const loadRoom = useCallback(() => {
    const controller = new AbortController()
    setState({ kind: 'loading' })
    fetch(`/api/v1/rooms/${encodeURIComponent(roomId)}`, {
      signal: controller.signal,
    })
      .then(async (res) => {
        if (res.status === 404) {
          setState({ kind: 'not_found' })
          return
        }
        if (!res.ok) {
          setState({ kind: 'error', message: `HTTP ${res.status}` })
          return
        }
        const room = (await res.json()) as RoomRead
        setState({ kind: 'ok', room })
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
    return loadRoom()
  }, [loadRoom])

  return (
    <main className="shell">
      <p className="brand">WowLance 2.0</p>
      <p className="back">
        <a href="/">← Home</a>
      </p>
      {state.kind === 'loading' && <p className="hint">Loading room…</p>}
      {state.kind === 'not_found' && (
        <p className="error">Room not found (404). Check the id from handoff.</p>
      )}
      {state.kind === 'error' && <p className="error">{state.message}</p>}
      {state.kind === 'ok' && (
        <RoomView room={state.room} onReload={() => loadRoom()} />
      )}
    </main>
  )
}

function RoomView({
  room,
  onReload,
}: {
  room: RoomRead
  onReload: () => void
}) {
  const [rosterVersion, setRosterVersion] = useState(0)
  const badge = room.staffing_unlocked ? 'Staffing unlocked' : 'Staffing locked'
  const docs = room.strategy.documents ?? []
  return (
    <>
      <h1>{room.name}</h1>
      <p className={room.staffing_unlocked ? 'badge unlocked' : 'badge locked'}>
        {badge}
      </p>
      <dl className="meta">
        <dt>Type</dt>
        <dd>{room.room_type}</dd>
        <dt>Timezone</dt>
        <dd>{room.timezone}</dd>
        <dt>Founder</dt>
        <dd>{room.founder_sub}</dd>
      </dl>
      <section className="block">
        <h2>Strategy</h2>
        <p>
          <strong>Offer.</strong> {room.strategy.offer}
        </p>
        <p>
          <strong>Audience.</strong> {room.strategy.audience}
        </p>
        <p>
          <strong>Hot criteria.</strong> {room.strategy.hot_criteria}
        </p>
        {room.strategy.utp ? (
          <p>
            <strong>UTP.</strong> {room.strategy.utp}
          </p>
        ) : null}
        <p className="hint">Version {room.strategy.strategy_version}</p>
      </section>
      <PendingStrategyPanel room={room} onDecided={onReload} />
      <RosterPanel onChanged={() => setRosterVersion((v) => v + 1)} />
      <SlotsPanel
        roomId={room.id}
        staffingUnlocked={room.staffing_unlocked}
        rosterVersion={rosterVersion}
      />
      <TasksPanel roomId={room.id} />
      <LeadsPanel roomId={room.id} />
      <section className="block">
        <h2>Documents</h2>
        {docs.length === 0 ? (
          <p className="hint">No documents in snapshot.</p>
        ) : (
          <ul className="docs">
            {docs.map((doc) => (
              <li key={`${doc.role}:${doc.uri}`}>
                <span className="doc-role">{doc.role}</span>{' '}
                <code>{doc.uri}</code>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}
