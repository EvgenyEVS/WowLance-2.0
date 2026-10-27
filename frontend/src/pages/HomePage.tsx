import { FormEvent, useState } from 'react'
import { getToken, tokenInfo } from '../api'

export default function HomePage() {
  const [roomId, setRoomId] = useState('')
  const identity = tokenInfo(getToken())

  function onOpen(event: FormEvent) {
    event.preventDefault()
    const id = roomId.trim()
    if (!id) return
    window.location.assign(`/rooms/${encodeURIComponent(id)}`)
  }

  return (
    <div className="page">
      <section className="hero">
        <p className="kicker">B2B · WowLance 2.0</p>
        <h1>Room shell</h1>
        <p className="lede">
          FastAPI · React · PostgreSQL · OpenSpec · Superpowers
        </p>
        <p className="hint">
          Create a room with C1 FounderHandoff (
          <code>POST /internal/v1/handoffs</code> in Swagger or curl), then paste
          the <code>room_id</code> below.
        </p>
      </section>

      <section className="card form-card">
        <h2>Open a room</h2>
        <p className="hint">
          Paste the <code>room_id</code> from the handoff response.
        </p>
        <form className="open-form" onSubmit={onOpen}>
          <label htmlFor="room-id">Room id</label>
          <input
            id="room-id"
            name="roomId"
            type="text"
            value={roomId}
            onChange={(e) => setRoomId(e.target.value)}
            placeholder="uuid from handoff"
            autoComplete="off"
          />
          <button type="submit" className="btn btn-primary">
            Open
          </button>
        </form>
      </section>

      <p className="hint">
        {identity.sub ? (
          <>
            Signed in: <strong>{identity.sub}</strong>
          </>
        ) : (
          <>
            No token stored. <a href="/login">Login / token</a>
          </>
        )}
      </p>
    </div>
  )
}
