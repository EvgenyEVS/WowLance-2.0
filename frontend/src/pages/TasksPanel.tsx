import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { RosterMember, RoomTask, TasksList } from '../types'

/** Fallback actor for AUTH_DISABLED=true; ignored by the backend when a JWT is sent. */
const ACTOR_SUB = 'freelancer-demo-sub'

type TasksState =
  | { kind: 'loading' }
  | { kind: 'ok'; tasks: RoomTask[] }
  | { kind: 'not_found' }
  | { kind: 'error'; message: string }

type MutateResult =
  | { ok: true }
  | { ok: false; status: number; message: string }

export default function TasksPanel({
  roomId,
  canStaff = true,
}: {
  roomId: string
  canStaff?: boolean
}) {
  const [state, setState] = useState<TasksState>({ kind: 'loading' })
  const [title, setTitle] = useState('')
  const [assigneeSub, setAssigneeSub] = useState<string | null>(null)
  const [roster, setRoster] = useState<RosterMember[]>([])
  const [rosterBusy, setRosterBusy] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadTasks = useCallback(() => {
    const controller = new AbortController()
    setState({ kind: 'loading' })
    apiFetch(`/api/v1/rooms/${encodeURIComponent(roomId)}/tasks`, {
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
        const body = (await res.json()) as TasksList
        setState({ kind: 'ok', tasks: body.tasks })
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
    setRosterBusy(true)
    apiFetch(`/api/v1/roster`, { signal: new AbortController().signal })
      .then(async (res) => {
        if (!res.ok) return
        const body = (await res.json()) as { members: RosterMember[] }
        setRoster(body.members ?? [])
      })
      .catch(() => {
        // roster load is non-fatal; tasks still work without assignee
      })
      .finally(() => setRosterBusy(false))
  }, [])

  useEffect(() => {
    return loadTasks()
  }, [loadTasks])

  useEffect(() => {
    loadRoster()
  }, [loadRoster])

  async function mutate(
    path: string,
    body?: unknown,
  ): Promise<MutateResult> {
    setBusy(true)
    setError(null)
    try {
      const headers: Record<string, string> = { 'X-Actor-Sub': ACTOR_SUB }
      let payload: string | undefined
      if (body !== undefined) {
        headers['Content-Type'] = 'application/json'
        payload = JSON.stringify(body)
      }
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(roomId)}/tasks${path}`,
        { method: 'POST', headers, body: payload },
      )
      if (res.status === 404) {
        const message = 'Room or task not found (404).'
        setError(message)
        loadTasks()
        return { ok: false, status: res.status, message }
      }
      if (res.status === 409) {
        const message = 'Illegal status transition (409). Reload the list.'
        setError(message)
        loadTasks()
        return { ok: false, status: res.status, message }
      }
      if (res.status === 422) {
        const message = 'Missing proof URI or actor (422).'
        setError(message)
        return { ok: false, status: res.status, message }
      }
      if (!res.ok) {
        const message = `HTTP ${res.status}`
        setError(message)
        return { ok: false, status: res.status, message }
      }
      loadTasks()
      return { ok: true }
    } finally {
      setBusy(false)
    }
  }

  async function addTask(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = title.trim()
    if (!trimmed) return
    const result = await mutate('', {
      title: trimmed,
      ...(assigneeSub ? { assignee_sub: assigneeSub } : {}),
    })
    if (result.ok) {
      setTitle('')
      setAssigneeSub(null)
    }
  }

  async function assignTask(taskId: string, sub: string) {
    const result = await mutate(`/${taskId}/assign`, { assignee_sub: sub })
    if (result.ok) setAssigneeSub(null)
  }

  return (
    <section className="block tasks-block">
      <h2>Tasks</h2>
      {canStaff ? (
      <form className="task-form" onSubmit={addTask}>
        <input
          type="text"
          value={title}
          placeholder="New task title"
          onChange={(e) => setTitle(e.target.value)}
          disabled={busy}
        />
        <select
          value={assigneeSub ?? ''}
          onChange={(e) => setAssigneeSub(e.target.value || null)}
          disabled={busy || rosterBusy}
        >
          <option value="">— не назначен —</option>
          {roster.map((m) => (
            <option key={m.freelancer_sub} value={m.freelancer_sub}>
              {m.display_name} ({m.freelancer_sub})
            </option>
          ))}
        </select>
        {roster.length === 0 && !rosterBusy && (
          <span className="hint">ростер пуст — assignee будет null</span>
        )}
        <button type="submit" className="slot-action" disabled={busy || !title.trim()}>
          Add
        </button>
      </form>
      ) : null}
      {state.kind === 'loading' && <p className="hint">Loading tasks…</p>}
      {state.kind === 'not_found' && <p className="error">Room not found (404).</p>}
      {state.kind === 'error' && <p className="error">{state.message}</p>}
      {state.kind === 'ok' && state.tasks.length === 0 && (
        <p className="hint">No tasks yet.</p>
      )}
      {state.kind === 'ok' && state.tasks.length > 0 && (
        <ul className="task-list">
          {state.tasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              busy={busy}
              roster={roster}
              onStart={() => void mutate(`/${task.id}/start`)}
              onComplete={(proofUri, proofNote) =>
                mutate(`/${task.id}/complete`, {
                  proof_uri: proofUri,
                  ...(proofNote ? { proof_note: proofNote } : {}),
                })
              }
              onAccept={() => void mutate(`/${task.id}/accept`)}
              onReject={(reviewNote) =>
                mutate(
                  `/${task.id}/reject`,
                  reviewNote ? { review_note: reviewNote } : undefined,
                )
              }
              onAssign={(sub) => void assignTask(task.id, sub)}
              canStaff={canStaff}
            />
          ))}
        </ul>
      )}
      {error ? <p className="error">{error}</p> : null}
    </section>
  )
}

type TaskItemProps = {
  task: RoomTask
  busy: boolean
  roster: RosterMember[]
  onStart: () => void
  onComplete: (proofUri: string, proofNote: string) => Promise<MutateResult>
  onAccept: () => void
  onReject: (reviewNote: string) => Promise<MutateResult>
  onAssign: (sub: string) => void
  canStaff: boolean
}

function TaskItem({
  task,
  busy,
  roster,
  onStart,
  onComplete,
  onAccept,
  onReject,
  onAssign,
  canStaff,
}: TaskItemProps) {
  const [proofUri, setProofUri] = useState('')
  const [proofNote, setProofNote] = useState('')
  const [rejectNote, setRejectNote] = useState('')
  const [assignSub, setAssignSub] = useState<string | null>(null)

  const assignOptions = roster.filter(
    (m) => m.freelancer_sub !== task.assignee_sub
  )

  async function submitProof(event: React.FormEvent) {
    event.preventDefault()
    const uri = proofUri.trim()
    if (!uri) return
    const result = await onComplete(uri, proofNote.trim())
    if (result.ok) {
      setProofUri('')
      setProofNote('')
    }
  }

  async function submitReject() {
    const result = await onReject(rejectNote.trim())
    if (result.ok) setRejectNote('')
  }

  async function submitAssign() {
    if (!assignSub) return
    onAssign(assignSub)
    setAssignSub(null)
  }

  return (
    <li className="task-item">
      <div className="task-row">
        <span className="task-title">{task.title}</span>
        <span className="hint task-status">{task.status}</span>
        {task.assignee_sub ? (
          <span className="hint task-assignee">{task.assignee_sub}</span>
        ) : null}
        {task.status === 'todo' && (
          <button type="button" className="slot-action" disabled={busy} onClick={onStart}>
            Start
          </button>
        )}
        {canStaff && (task.status === 'todo' || task.status === 'in_progress') && (
          <>
            <select>
              value={assignSub ?? ''}
              onChange={(e) => setAssignSub(e.target.value || null)}
              disabled={busy}
            >
              <option value="">назначить</option>
              {assignOptions.map((m) => (
                <option key={m.freelancer_sub} value={m.freelancer_sub}>
                  {m.display_name}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="slot-action"
              disabled={busy || !assignSub}
              onClick={submitAssign}
            >
              Assign
            </button>
          </>
        )}
        {canStaff && task.status === 'submitted' && (
          <>
            <button
              type="button"
              className="slot-action"
              disabled={busy}
              onClick={onAccept}
            >
              Accept
            </button>
            <button
              type="button"
              className="slot-action"
              disabled={busy}
              onClick={() => void submitReject()}
            >
              Reject
            </button>
          </>
        )}
      </div>

      {task.status === 'in_progress' && (
        <form className="task-proof-form" onSubmit={submitProof}>
          <input
            type="text"
            value={proofUri}
            placeholder="Proof URI (required)"
            onChange={(e) => setProofUri(e.target.value)}
            disabled={busy}
          />
          <input
            type="text"
            value={proofNote}
            placeholder="Note (optional)"
            onChange={(e) => setProofNote(e.target.value)}
            disabled={busy}
          />
          <button
            type="submit"
            className="slot-action"
            disabled={busy || !proofUri.trim()}
          >
            Submit
          </button>
        </form>
      )}

      {(task.status === 'submitted' || task.status === 'done') && task.proof_uri ? (
        <p className="hint task-proof">
          Proof: <a href={task.proof_uri}>{task.proof_uri}</a>
          {task.proof_note ? <> — {task.proof_note}</> : null}
          {task.reviewed_by_sub ? <> (reviewed by {task.reviewed_by_sub})</> : null}
          {task.review_note ? <> — reason: {task.review_note}</> : null}
        </p>
      ) : null}

      {task.status === 'in_progress' && task.review_note ? (
        <p className="hint task-review">Last reject reason: {task.review_note}</p>
      ) : null}

      {canStaff && task.status === 'submitted' ? (
        <input
          type="text"
          value={rejectNote}
          placeholder="Reject reason (optional)"
          onChange={(e) => setRejectNote(e.target.value)}
          disabled={busy}
        />
      ) : null}
    </li>
  )
}
