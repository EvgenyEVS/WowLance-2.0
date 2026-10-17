# WowLance 2.0 — frontend (React + Vite)

C3–C9 room shell. C13 room health card. No login.  
Slots: after entitlement + **Materialize slots**.  
Roster (C6): add a freelancer (sub + name) → **Assign** on an `open` slot with `X-Actor-Sub: teamlead-demo-sub`; filled slots show the seated freelancer.  
Pending strategy: **Accept** / **Reject** with stub header `X-Actor-Sub: teamlead-demo-sub`.  
Tasks (C7): **Add** / **Start** with stub header `X-Actor-Sub: freelancer-demo-sub`.  
Tasks Quality Gate (C10): **Submit** proof URI (+ note) → `submitted`; **Accept** / **Reject** (optional reason) as `X-Actor-Sub: teamlead-demo-sub`. Proof shown on the card; reject keeps proof for resubmit.  
Leads (C9): **Add** / **Mark hot** / **Hand to CRM** with stub header `X-Actor-Sub: founder-demo-sub`.
Room health (C13): card on the room page shows slots/tasks/leads aggregates; **Refresh** re-reads `GET …/health`, **Publish snapshot** writes an outbox `RoomHealthSnapshot` row (stub).

## Login / token (C8)

All API calls go through `apiFetch` (`src/api.ts`), which adds
`Authorization: Bearer <token>` when a token is stored (memory +
`sessionStorage`, key `wowlance_access_token`).

- **Login page**: `/login` (link in the header of Home) — paste a Keycloak
  access token → **Save token**. Home then shows `Signed in: <sub>`.
- **401 from the API** (backend `AUTH_DISABLED=false`, no/expired token) →
  the app switches to `/login` with «нужен login».
- **Backend `AUTH_DISABLED=true` (default)** → requests work without any
  token, login is optional (local demo without Keycloak).
- Demo token without Keycloak: backend with `AUTH_DISABLED=false` +
  `AUTH_STUB_JWKS=true` → `POST /auth/stub-token` (see backend/README.md, C8).

OIDC code flow is out of scope for C8 (paste-token MVP, see the task file).

## Local

Backend must be running on port 8000 (`backend/README.md`). Vite proxies `/api`, `/internal`, `/health`.

```powershell
cd frontend
npm install
npm run dev
```

UI: http://127.0.0.1:5173

## How to check

1. Create a room (C1):

```powershell
curl -s -X POST http://127.0.0.1:8000/internal/v1/handoffs `
  -H "Content-Type: application/json" `
  --data-binary "@..\contracts\wowlance\examples\FounderHandoff.sale.json"
```

2. Copy `room_id` from the JSON.
3. Open http://127.0.0.1:5173 → paste id → **Open**, or go to `/rooms/<room_id>`.
4. Expect name, type, timezone, **Staffing locked**, offer / audience / hot criteria, document URI as text (no download).
5. After C2 entitlement, refresh: **Staffing unlocked**, block **Slots** with **Materialize slots** (sale example → two `seller` seats). Locked rooms show «Slots locked until entitlement».
6. After C5 publish, refresh: **Strategy** stays the old offer; **Pending strategy** block with Accept/Reject. Accept → new offer, pending disappears.
7. C6: in **Roster** upsert a freelancer (e.g. `f-1234` / demo), then in **Slots** pick them on an `open` seat and **Assign** → seat becomes `filled` with the sub; assigning the same freelancer again returns idempotent `already_assigned`.
8. Block **Tasks** (available right after room creation, no entitlement needed): type a title → **Add** (→ `todo`), **Start** (→ `in_progress`, assignee from `X-Actor-Sub`). C10 Quality Gate: enter a **proof URI** (+ optional note) → **Submit** (→ `submitted`, missing URI → 422), then **Accept** (→ `done`) or **Reject** with optional reason (→ `in_progress`, proof kept for resubmit). Illegal transitions (incl. direct `in_progress` → `done`) show a 409 error.
9. Block **Leads** (C9, available right after room creation): type a title (+ optional contact name) → **Add** (→ `open`), **Mark hot** (→ `hot`), **Hand to CRM** (→ `handed_to_crm`, shows `crm-stub:<lead_id>`). Handing a hot lead off twice is idempotent (`already_handed`); illegal transitions show a 409 error.
10. Block **Room health** (C13): after adding slots/tasks/leads, **Refresh** shows matching counts (empty entities are zeros, not errors). **Publish snapshot** writes an outbox row and shows the `outbox_id`; repeat publishes create a new row each time (history).
