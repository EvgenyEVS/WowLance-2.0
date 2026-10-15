# WowLance 2.0 — frontend (React + Vite)

C3: read-only room shell. No login, no entitlement form, no staffing UI.

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
