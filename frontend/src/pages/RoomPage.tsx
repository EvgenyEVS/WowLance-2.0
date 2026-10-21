import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { EarningsList, RoomRead } from '../types'
import LeadsPanel from './LeadsPanel'
import PendingStrategyPanel from './PendingStrategyPanel'
import RosterPanel from './RosterPanel'
import RoomHealthPanel from './RoomHealthPanel'
import SlotsPanel from './SlotsPanel'
import TasksPanel from './TasksPanel'
import ChatPanel from './ChatPanel'

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
    apiFetch(`/api/v1/rooms/${encodeURIComponent(roomId)}`, {
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
  const [meetBusy, setMeetBusy] = useState(false)
  const [meetError, setMeetError] = useState<string | null>(null)
  const [earnings, setEarnings] = useState<EarningsList | null>(null)
  const [earningsBusy, setEarningsBusy] = useState(false)
  const [earningsError, setEarningsError] = useState<string | null>(null)
  const badge = room.staffing_unlocked ? 'Staffing unlocked' : 'Staffing locked'
  const docs = room.strategy.documents ?? []

  async function ensureMeet() {
    setMeetBusy(true)
    setMeetError(null)
    try {
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(room.id)}/meet/ensure`,
        { method: 'POST', headers: { 'X-Actor-Sub': 'founder-demo-sub' } },
      )
      if (!res.ok) {
        setMeetError(`HTTP ${res.status}`)
        return
      }
      onReload()
    } finally {
      setMeetBusy(false)
    }
  }

  async function loadEarnings() {
    setEarningsBusy(true)
    setEarningsError(null)
    try {
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(room.id)}/earnings`
      )
      if (!res.ok) {
        setEarningsError(`HTTP ${res.status}`)
        return
      }
      setEarnings((await res.json()) as EarningsList)
    } finally {
      setEarningsBusy(false)
    }
  }

  useEffect(() => {
    loadEarnings()
  }, [room.id])

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
        <h2>Meet (Jitsi stub)</h2>
        {room.meeting_url ? (
          <>
            <p>
              <strong>Ссылка на звонок:</strong>{' '}
              <a href={room.meeting_url} target="_blank" rel="noopener noreferrer">
                {room.meeting_url}
              </a>
            </p>
            <p className="hint">Ссылка уже создана (идемпотентно).</p>
          </>
        ) : (
          <>
            <button
              type="button"
              className="slot-action"
              disabled={meetBusy}
              onClick={() => void ensureMeet()}
            >
              Ensure meeting / Создать ссылку
            </button>
            {meetError ? <p className="error">{meetError}</p> : null}
          </>
        )}
      </section>
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
      <ChatPanel roomId={room.id} />
      <RoomHealthPanel roomId={room.id} />
      <section className="block">
        <h2>Earned (stub)</h2>
        {earningsBusy ? (
          <p className="hint">Loading earned…</p>
        ) : earningsError ? (
          <p className="error">{earningsError}</p>
        ) : (
          <>
            <p>
              <strong>Total:</strong> {earnings?.total_amount} {earnings?.currency}
            </p>
            {earnings?.entries.length === 0 ? (
              <p className="hint">No earnings yet. Accept a task with an assignee to accrue.</p>
            ) : (
              <ul className="task-list">
                {earnings?.entries.map((e) => (
                  <li key={e.id} className="task-item">
                    <span className="task-title">{e.freelancer_sub}</span>
                    <span className="hint task-assignee">{e.amount} {e.currency}</span>
                    <span className="hint task-status">{e.source}</span>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </section>
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
