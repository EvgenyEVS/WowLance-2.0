import HomePage from './pages/HomePage'
import RoomPage from './pages/RoomPage'

function roomIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/rooms\/([^/]+)\/?$/)
  if (!match) return null
  try {
    return decodeURIComponent(match[1])
  } catch {
    return match[1]
  }
}

export default function App() {
  const roomId = roomIdFromPath(window.location.pathname)
  if (roomId) {
    return <RoomPage roomId={roomId} />
  }
  return <HomePage />
}
