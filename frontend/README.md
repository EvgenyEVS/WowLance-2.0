# WowLance 2.0 — frontend (React + Vite)

C3–C9 room shell. No login.  
Slots: after entitlement + **Materialize slots**.  
Roster (C6): add a freelancer (sub + name) → **Assign** on an `open` slot with `X-Actor-Sub: teamlead-demo-sub`; filled slots show the seated freelancer.  
Pending strategy: **Accept** / **Reject** with stub header `X-Actor-Sub: teamlead-demo-sub`.  
Tasks: **Add** / **Start** / **Complete** with stub header `X-Actor-Sub: freelancer-demo-sub`.  
Leads (C9): **Add** / **Mark hot** / **Hand to CRM** with stub header `X-Actor-Sub: founder-demo-sub`.

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
8. Block **Tasks** (available right after room creation, no entitlement needed): type a title → **Add** (→ `todo`), **Start** (→ `in_progress`, assignee from `X-Actor-Sub`), **Complete** (→ `done`). Illegal transitions show a 409 error.
9. Block **Leads** (C9, available right after room creation): type a title (+ optional contact name) → **Add** (→ `open`), **Mark hot** (→ `hot`), **Hand to CRM** (→ `handed_to_crm`, shows `crm-stub:<lead_id>`). Handing a hot lead off twice is idempotent (`already_handed`); illegal transitions show a 409 error.
