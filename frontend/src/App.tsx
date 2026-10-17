import { useEffect, useState } from 'react'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
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
  const [path, setPath] = useState(window.location.pathname)
  const [needsLogin, setNeedsLogin] = useState(false)

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname)
    // C8: any 401 from the API -> "нужен login"
    const onUnauthorized = () => {
      setNeedsLogin(true)
      if (window.location.pathname !== '/login') {
        window.history.pushState({}, '', '/login')
        setPath('/login')
      }
    }
    window.addEventListener('popstate', onPopState)
    window.addEventListener('wowlance:unauthorized', onUnauthorized)
    return () => {
      window.removeEventListener('popstate', onPopState)
      window.removeEventListener('wowlance:unauthorized', onUnauthorized)
    }
  }, [])

  if (path === '/login') {
    return <LoginPage needsLogin={needsLogin} />
  }
  const roomId = roomIdFromPath(path)
  if (roomId) {
    return <RoomPage roomId={roomId} />
  }
  return <HomePage />
}
