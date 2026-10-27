import { useCallback, useEffect, useState } from 'react'
import { viewerSub } from '../actor'
import { apiFetch } from '../api'
import type { EarningsList, MeetEnsureResult, RoomRead } from '../types'
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
      headers: { 'X-Actor-Sub': viewerSub() },
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
    <div className="page">
      <p className="back">
        <a className="btn btn-secondary btn-sm" href="/">
          ← Home
        </a>
      </p>
      {state.kind === 'loading' && <p className="hint">Loading room…</p>}
      {state.kind === 'not_found' && (
        <p className="error">Room not found (404). Check the id from handoff.</p>
      )}
      {state.kind === 'error' && <p className="error">{state.message}</p>}
      {state.kind === 'ok' && (
        <RoomView room={state.room} onReload={() => loadRoom()} />
      )}
    </div>
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
  const [meetingUrl, setMeetingUrl] = useState<string | null>(
    room.meeting_url ?? null
  )
  const [earnings, setEarnings] = useState<EarningsList | null>(null)
  const [earningsBusy, setEarningsBusy] = useState(false)
  const [earningsError, setEarningsError] = useState<string | null>(null)
  const [healthVersion, setHealthVersion] = useState(0)
  const [earnedMine, setEarnedMine] = useState(false)
  const canStaff =
    !room.rbac_enforced ||
    room.viewer_role === 'founder' ||
    room.viewer_role === 'teamlead'
  const badge = room.staffing_unlocked ? 'Staffing unlocked' : 'Staffing locked'
  const docs = room.strategy.documents ?? []
  const mySub = viewerSub()
  const earnedEntries = earnings?.entries ?? []
  const visibleEarned = earnedMine
    ? earnedEntries.filter((e) => e.freelancer_sub === mySub)
    : earnedEntries

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
      const body = (await res.json()) as MeetEnsureResult
      setMeetingUrl(body.meeting_url)
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
        {meetingUrl ? (
          <>
            <p>
              <strong>Ссылка на звонок:</strong>{' '}
              <a href={meetingUrl} target="_blank" rel="noopener noreferrer">
                {meetingUrl}
              </a>
            </p>
            <button
              type="button"
              className="slot-action"
              disabled={meetBusy}
              onClick={() => void ensureMeet()}
            >
              Re-ensure
            </button>
            {meetError ? <p className="error">{meetError}</p> : null}
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
      <PendingStrategyPanel
        room={room}
        onDecided={onReload}
        canStaff={canStaff}
      />
      <RosterPanel onChanged={() => setRosterVersion((v) => v + 1)} />
      <SlotsPanel
        roomId={room.id}
        staffingUnlocked={room.staffing_unlocked}
        rosterVersion={rosterVersion}
        canStaff={canStaff}
      />
      <TasksPanel
        roomId={room.id}
        canStaff={canStaff}
        onAccepted={() => {
          void loadEarnings()
          setHealthVersion((v) => v + 1)
        }}
      />
      <LeadsPanel roomId={room.id} canStaff={canStaff} />
      <ChatPanel roomId={room.id} />
      <RoomHealthPanel roomId={room.id} refreshKey={healthVersion} />
      <section className="block">
        <div className="earned-head">
          <h2>Earned (stub)</h2>
          {room.rbac_enforced ? (
            <div className="earned-filter">
              <button
                type="button"
                className={earnedMine ? 'ghost-action' : 'slot-action'}
                onClick={() => setEarnedMine(false)}
              >
                Все
              </button>
              <button
                type="button"
                className={earnedMine ? 'slot-action' : 'ghost-action'}
                onClick={() => setEarnedMine(true)}
              >
                Мои
              </button>
            </div>
          ) : null}
        </div>
        {earningsBusy ? (
          <p className="hint">Loading earned…</p>
        ) : earningsError ? (
          <p className="error">{earningsError}</p>
        ) : (
          <>
            <p>
              <strong>Total:</strong> {earnings?.total_amount} {earnings?.currency}
            </p>
            {earnedMine ? (
              <p className="hint">Показаны только мои начисления.</p>
            ) : null}
            {visibleEarned.length === 0 ? (
              <p className="hint">
                {earnedMine
                  ? 'У вас пока нет начислений — Accept задачу.'
                  : 'Пока нет начислений — Accept задачу.'}
              </p>
            ) : (
              <ul className="task-list">
                {visibleEarned.map((e) => (
                  <li key={e.id} className="task-item">
                    <span className="task-title">{e.freelancer_sub}</span>
                    <span className="hint task-assignee">
                      {e.amount} {e.currency}
                    </span>
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
