import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import AppShell from './AppShell'
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

  let page: ReactNode
  if (path === '/login') {
    page = <LoginPage needsLogin={needsLogin} />
  } else {
    const roomId = roomIdFromPath(path)
    page = roomId ? <RoomPage roomId={roomId} /> : <HomePage />
  }

  return <AppShell>{page}</AppShell>
}
