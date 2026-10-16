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
    <main className="shell">
      <p className="brand">WowLance 2.0</p>
      <p className="back">
        <a href="/login">
          {identity.sub ? `Signed in: ${identity.sub}` : 'Login / token'}
        </a>
      </p>
      <h1>Room shell</h1>
      <p className="lede">
        FastAPI · React · PostgreSQL · OpenSpec · Superpowers
      </p>
      <p className="hint">
        Create a room with C1 FounderHandoff (
        <code>POST /internal/v1/handoffs</code> in Swagger or curl), then paste
        the <code>room_id</code> here.
      </p>
      <form className="open-form" onSubmit={onOpen}>
        <label htmlFor="room-id">Room id</label>
        <input
          id="room-id"
          name="roomId"
          value={roomId}
          onChange={(e) => setRoomId(e.target.value)}
          placeholder="uuid from handoff"
          autoComplete="off"
        />
        <button type="submit">Open</button>
      </form>
    </main>
  )
}
