import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { LeadStatus, LeadsList, RoomLead } from '../types'

/** Fallback actor for AUTH_DISABLED=true; ignored when a JWT Bearer is sent. */
const ACTOR_SUB = 'founder-demo-sub'

type LeadFilter = 'all' | LeadStatus

type LeadsState =
  | { kind: 'loading' }
  | { kind: 'ok'; leads: RoomLead[]; total: number }
  | { kind: 'not_found' }
  | { kind: 'error'; message: string }

export default function LeadsPanel({
  roomId,
  canStaff = true,
}: {
  roomId: string
  canStaff?: boolean
}) {
  const [state, setState] = useState<LeadsState>({ kind: 'loading' })
  const [title, setTitle] = useState('')
  const [contactName, setContactName] = useState('')
  const [filter, setFilter] = useState<LeadFilter>('all')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadLeads = useCallback(() => {
    const controller = new AbortController()
    setState({ kind: 'loading' })
    const url =
      filter === 'all'
        ? `/api/v1/rooms/${encodeURIComponent(roomId)}/leads`
        : `/api/v1/rooms/${encodeURIComponent(roomId)}/leads?status=${encodeURIComponent(filter)}`
    apiFetch(url, { signal: controller.signal })
      .then(async (res) => {
        if (res.status === 404) {
          setState({ kind: 'not_found' })
          return
        }
        if (!res.ok) {
          setState({ kind: 'error', message: `HTTP ${res.status}` })
          return
        }
        const body = (await res.json()) as LeadsList
        setState({ kind: 'ok', leads: body.leads, total: body.leads.length })
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        setState({
          kind: 'error',
          message: err instanceof Error ? err.message : 'Request failed',
        })
      })
    return () => controller.abort()
  }, [roomId, filter])

  useEffect(() => {
    return loadLeads()
  }, [loadLeads])

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
        `/api/v1/rooms/${encodeURIComponent(roomId)}/leads${path}`,
        { method: 'POST', headers, body: payload },
      )
      if (res.status === 404) {
        setError('Room or lead not found.')
        return false
      }
      if (res.status === 409) {
        setError('Illegal lead transition. Reload the list.')
        loadLeads()
        return false
      }
      if (res.status === 422) {
        setError('Invalid request. Check the input.')
        return false
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return false
      }
      loadLeads()
      return true
    } finally {
      setBusy(false)
    }
  }

  async function addLead(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = title.trim()
    if (!trimmed) return
    const display = contactName.trim()
    const ok = await mutate('', {
      title: trimmed,
      contact_name: display ? display : null,
    })
    if (ok) {
      setTitle('')
      setContactName('')
    }
  }

  const filteredCount = state.kind === 'ok' ? state.total : 0

  return (
    <section className="block leads-block">
      <h2>Leads</h2>
      <p className="hint">
        Pipeline: open → Mark hot → Hand to CRM → deal status
      </p>
      {canStaff ? (
      <form className="task-form" onSubmit={addLead}>
        <input
          type="text"
          value={title}
          placeholder="New lead title"
          onChange={(e) => setTitle(e.target.value)}
          disabled={busy}
        />
        <input
          type="text"
          value={contactName}
          placeholder="Contact name (optional)"
          onChange={(e) => setContactName(e.target.value)}
          disabled={busy}
        />
        <button type="submit" className="slot-action" disabled={busy || !title.trim()}>
          Add
        </button>
      </form>
      ) : null}
      <div className="filter-chip-group">
        {(['all', 'open', 'hot', 'handed_to_crm'] as const).map((f) => (
          <button
            key={f}
            type="button"
            className={`filter-chip ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'All' : f}
            {state.kind === 'ok' && f !== 'all' ? ` · ${filteredCount}` : ''}
          </button>
        ))}
      </div>
      {state.kind === 'loading' && <p className="hint">Loading leads…</p>}
      {state.kind === 'not_found' && <p className="error">Room not found.</p>}
      {state.kind === 'error' && <p className="error">{state.message}</p>}
      {state.kind === 'ok' && state.leads.length === 0 && (
        <p className="hint">
          No leads yet. Add a lead, Mark hot, then Hand to CRM.
        </p>
      )}
      {state.kind === 'ok' && state.leads.length > 0 && (
        <ul className="task-list">
          {state.leads.map((lead) => (
            <li key={lead.id} className="task-item">
              <span className="task-title">{lead.title}</span>
              <span className="hint task-status">{lead.status}</span>
              {lead.contact_name ? (
                <span className="hint task-assignee">{lead.contact_name}</span>
              ) : null}
              {lead.crm_ref ? (
                <code className="hint">{lead.crm_ref}</code>
              ) : null}
              {lead.status === 'handed_to_crm' && (
                <>
                  <span className="hint task-assignee">
                    deal: {lead.deal_status ?? '—'}
                    {lead.deal_amount && lead.deal_currency
                      ? ` ${lead.deal_amount} ${lead.deal_currency}`
                      : ''}
                  </span>
                </>
              )}
              {canStaff && lead.status === 'open' && (
                <button
                  type="button"
                  className="slot-action"
                  disabled={busy}
                  onClick={() => void mutate(`/${lead.id}/mark-hot`)}
                >
                  Mark hot
                </button>
              )}
              {canStaff && lead.status === 'hot' && (
                <button
                  type="button"
                  className="slot-action"
                  disabled={busy}
                  onClick={() => void mutate(`/${lead.id}/handoff-crm`)}
                >
                  Hand to CRM
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
