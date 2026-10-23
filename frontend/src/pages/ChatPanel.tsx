import { useCallback, useEffect, useRef, useState } from 'react'
import { apiFetch } from '../api'
import type { MessagesList, RoomMessage } from '../types'

/** Fallback actor for AUTH_DISABLED=true; ignored when a JWT Bearer is sent. */
const ACTOR_SUB = 'founder-demo-sub'

/** Soft poll interval: fetch new messages without showing “Loading…”. */
const POLL_INTERVAL_MS = 7000

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
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadMessages = useCallback(() => {
    const controller = new AbortController()
    apiFetch(`/api/v1/rooms/${encodeURIComponent(roomId)}/messages`, {
      signal: controller.signal,
    })
      .then(async (res) => {
        if (res.status === 404) {
          setState({ kind: 'not_found' })
          return
        }
        if (!res.ok) {
          setState((prev) =>
            prev.kind === 'ok' ? prev : { kind: 'error', message: `HTTP ${res.status}` }
          )
          return
        }
        const data = (await res.json()) as MessagesList
        setState({ kind: 'ok', messages: data.messages })
      })
      .catch((_err: unknown) => {
        if (controller.signal.aborted) return
        setState((prev) =>
          prev.kind === 'ok' ? prev : { kind: 'error', message: 'Request failed' }
        )
      })
    return () => controller.abort()
  }, [roomId])

  useEffect(() => {
    return loadMessages()
  }, [loadMessages])

  // Soft poll: refresh messages periodically without blinking the panel.
  useEffect(() => {
    pollTimer.current = setInterval(loadMessages, POLL_INTERVAL_MS)
    return () => {
      if (pollTimer.current) clearInterval(pollTimer.current)
    }
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
        setError('Room not found.')
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

  function shortTime(iso: string) {
    try {
      return new Date(iso).toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return iso
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
      {state.kind === 'not_found' && <p className="error">Room not found.</p>}
      {state.kind === 'error' && <p className="error">{state.message}</p>}
      {state.kind === 'ok' && state.messages.length === 0 && (
        <p className="hint">
          No messages yet. Type below and Send — the list shows the latest messages.
        </p>
      )}
      {state.kind === 'ok' && state.messages.length > 0 && (
        <ul className="task-list">
          {state.messages.map((msg) => (
            <li key={msg.id} className="task-item">
              <span className="task-title">{msg.author_sub}</span>
              <span className="hint task-status">{msg.body}</span>
              <span className="hint task-assignee">
                {shortTime(msg.created_at)}
              </span>
            </li>
          ))}
        </ul>
      )}
      {error ? <p className="error">{error}</p> : null}
    </section>
  )
}
