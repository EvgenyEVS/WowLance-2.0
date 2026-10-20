import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { MessagesList, RoomMessage } from '../types'

/** Fallback actor for AUTH_DISABLED=true; ignored when a JWT Bearer is sent. */
const ACTOR_SUB = 'founder-demo-sub'

type MessagesState =
  | { kind: 'loading' }
  | { kind: 'ok'; messages: RoomMessage[] }
  | { kind: 'not_found' }
  | { kind: 'error'; message: string }

export default function ChatPanel({ roomId }: { roomId: string }) {
  const [state, setState] = useState<MessagesState>({ kind: 'loading' })
  const [body, setBody] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadMessages = useCallback(() => {
    const controller = new AbortController()
    setState({ kind: 'loading' })
    apiFetch(`/api/v1/rooms/${encodeURIComponent(roomId)}/messages`, {
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
        const data = (await res.json()) as MessagesList
        setState({ kind: 'ok', messages: data.messages })
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
    return loadMessages()
  }, [loadMessages])

  async function sendMessage(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = body.trim()
    if (!trimmed) return
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/api/v1/rooms/${encodeURIComponent(roomId)}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Actor-Sub': ACTOR_SUB,
          },
          body: JSON.stringify({ body: trimmed }),
        },
      )
      if (res.status === 404) {
        setError('Room not found (404).')
        return
      }
      if (res.status === 422) {
        setError('Invalid message (422). Body must be 1–2000 characters.')
        return
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      setBody('')
      loadMessages()
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="block chat-block">
      <h2>Chat</h2>
      <form className="task-form" onSubmit={sendMessage}>
        <input
          type="text"
          value={body}
          placeholder="New message"
          onChange={(e) => setBody(e.target.value)}
          disabled={busy}
        />
        <button
          type="submit"
          className="slot-action"
          disabled={busy || !body.trim()}
        >
          Send
        </button>
        <button
          type="button"
          className="slot-action"
          disabled={busy}
          onClick={() => void loadMessages()}
        >
          Refresh
        </button>
      </form>
      {state.kind === 'loading' && <p className="hint">Loading messages…</p>}
      {state.kind === 'not_found' && <p className="error">Room not found (404).</p>}
      {state.kind === 'error' && <p className="error">{state.message}</p>}
      {state.kind === 'ok' && state.messages.length === 0 && (
        <p className="hint">No messages yet. Start the conversation.</p>
      )}
      {state.kind === 'ok' && state.messages.length > 0 && (
        <ul className="task-list">
          {state.messages.map((msg) => (
            <li key={msg.id} className="task-item">
              <span className="task-title">{msg.author_sub}</span>
              <span className="hint task-status">{msg.body}</span>
              <span className="hint task-assignee">{msg.created_at}</span>
            </li>
          ))}
        </ul>
      )}
      {error ? <p className="error">{error}</p> : null}
    </section>
  )
}
