import type { ReactNode } from 'react'
import { getToken, tokenInfo } from './api'

/**
 * C39: 1.0-style app chrome. Only the shell lives here — pages keep their
 * own content. Routes stay as before (`/`, `/login`, `/rooms/:id`).
 */
export function SiteHeader() {
  const identity = tokenInfo(getToken())

  return (
    <header className="site-header">
      <div className="container header-inner">
        <div className="header-left">
          <a href="/" className="logo">
            <span className="logo-mark">W</span>
            <span className="logo-text">WowLance</span>
          </a>
        </div>
        <nav className="nav-menu">
          <a href="/">Home</a>
          <a href="/login">Login</a>
          {identity.sub ? <span className="nav-user">{identity.sub}</span> : null}
        </nav>
      </div>
    </header>
  )
}

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <SiteHeader />
      <main className="container">{children}</main>
      <footer className="site-footer">
        <div className="container footer-inner">
          <div className="footer-links">
            <a href="/">Home</a>
            <a href="/login">Login</a>
          </div>
          <p>© 2026 WowLance. Demo stub.</p>
        </div>
      </footer>
    </div>
  )
}
