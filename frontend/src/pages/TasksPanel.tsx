import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { RoomTask, TasksList } from '../types'

/** Fallback actor for AUTH_DISABLED=true; ignored by the backend when a JWT is sent. */
const ACTOR_SUB = 'freelancer-demo-sub'

type TasksState =
  | { kind: 'loading' }
  | { kind: 'ok'; tasks: RoomTask[] }
  | { kind: 'not_found' }
  | { kind: 'error'; message: string }

export default function TasksPanel({ roomId }: { roomId: string }) {
  const [state, setState] = useState<TasksState>({ kind: 'loading' })
  const [title, setTitle] = useState('')
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

  useEffect(() => {
    return loadTasks()
  }, [loadTasks])

  async function mutate(path: string, body?: unknown): Promise<boolean> {
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
        setError('Room or task not found (404).')
        return false
      }
      if (res.status === 409) {
        setError('Illegal status transition (409). Reload the list.')
        loadTasks()
        return false
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return false
      }
      loadTasks()
      return true
    } finally {
      setBusy(false)
    }
  }

  async function addTask(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = title.trim()
    if (!trimmed) return
    const ok = await mutate('', { title: trimmed })
    if (ok) setTitle('')
  }

  return (
    <section className="block tasks-block">
      <h2>Tasks</h2>
      <form className="task-form" onSubmit={addTask}>
        <input
          type="text"
          value={title}
          placeholder="New task title"
          onChange={(e) => setTitle(e.target.value)}
          disabled={busy}
        />
        <button type="submit" className="slot-action" disabled={busy || !title.trim()}>
          Add
        </button>
      </form>
      {state.kind === 'loading' && <p className="hint">Loading tasks…</p>}
      {state.kind === 'not_found' && <p className="error">Room not found (404).</p>}
      {state.kind === 'error' && <p className="error">{state.message}</p>}
      {state.kind === 'ok' && state.tasks.length === 0 && (
        <p className="hint">No tasks yet.</p>
      )}
      {state.kind === 'ok' && state.tasks.length > 0 && (
        <ul className="task-list">
          {state.tasks.map((task) => (
            <li key={task.id} className="task-item">
              <span className="task-title">{task.title}</span>
              <span className="hint task-status">{task.status}</span>
              {task.assignee_sub ? (
                <span className="hint task-assignee">{task.assignee_sub}</span>
              ) : null}
              {task.status === 'todo' && (
                <button
                  type="button"
                  className="slot-action"
                  disabled={busy}
                  onClick={() => void mutate(`/${task.id}/start`)}
                >
                  Start
                </button>
              )}
              {task.status === 'in_progress' && (
                <button
                  type="button"
                  className="slot-action"
                  disabled={busy}
                  onClick={() => void mutate(`/${task.id}/complete`)}
                >
                  Complete
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {error ? <p className="error">{error}</p> : null}
    </section>
  )
}
