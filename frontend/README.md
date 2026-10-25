# WowLance 2.0 — frontend (React + Vite)

C3–C9 room shell. C12 slot unassign/reassign. C13 room health card. C16 earnings. C17 member termination. No login.  

Slots: after entitlement + **Materialize slots**.  
Roster (C6): add a freelancer (sub + name) → **Assign** on an `open` slot with `X-Actor-Sub: teamlead-demo-sub`; filled slots show the seated freelancer.  
Slot unassign/reassign (C12): a `filled` slot has **Unassign** (→ `open`, sub cleared) and a **Reassign to…** picker + **Reassign** (swap the seated person; same sub → idempotent `already_assigned`). Reassign on an `open` slot shows a 409 — use Assign instead.  
Pending strategy: **Accept** / **Reject** with stub header `X-Actor-Sub: teamlead-demo-sub`.  
Tasks (C7): **Add** / **Start** with stub header `X-Actor-Sub: freelancer-demo-sub`.  
Tasks assignee (C15): при **Add** можно выбрать исполнителя из ростера (`GET /api/v1/roster`); `assignee_sub` должен быть в roster, иначе 404. **Start** без assignee подставляет `X-Actor-Sub` — актер тоже должен быть в ростере. На задачах в `todo`/`in_progress` доступен **Assign** для смены исполнителя.  
Tasks Quality Gate (C10): **Submit** proof URI (+ note) → `submitted`; **Accept** / **Reject** (optional reason) as `X-Actor-Sub: teamlead-demo-sub`. Proof shown on the card; reject keeps proof for resubmit.  
Leads (C9): **Add** / **Mark hot** / **Hand to CRM** with stub header `X-Actor-Sub: founder-demo-sub`.
C19 Deal status: после `Hand to CRM` вебхук `POST /internal/v1/crm/deal-status` ставит `deal_status` (+ `deal_amount`/`deal_currency`) на лид в статусе `handed_to_crm`, показывается в списке лидов.
Chat (C20 + C35): **ChatPanel** на RoomPage — список сообщений + форма **Send** + **Refresh** (poll каждые ~7 сек без WebSocket, мягкое обновление без “Loading…”). После **Send** список перезагружается сразу. Сообщение показывает автора + короткое время. Пустой чат — подсказка.
Meet (C14 + C35): блок Meet на RoomPage — если `meeting_url` уже есть, показывается ссылка **Open** + кнопка **Re-ensure**; если нет — **Ensure meeting / Создать ссылку**. После ensure ссылка подхватывается без полной перезагрузки страницы. Ошибка ensure — короткий текст.
Room health (C13 + C25): card on the room page shows slots/tasks/leads aggregates
plus the **Earned** block (`total_amount`, `currency`, `entries_count`) from the
stub earnings ledger; **Refresh** re-reads `GET …/health`, **Publish snapshot**
writes an outbox `RoomHealthSnapshot` row (stub).
Earned (C16): block on the room page shows total earned + entries per accepted task (`GET …/earnings`). Amount per accepted task = stub `EARNINGS_TASK_AMOUNT` (default `10.00 USD`).
Member termination (C17): on a **filled** slot, **Terminate** button (next to **Unassign**) prompts for a reason → `POST …/members/{sub}/terminate` → frees the slot, writes `room_terminations` journal + outbox `MemberTerminated`. **Unassign** = just frees the slot (no journal/outbox); **Terminate** = с причиной и историей.
Slots (C31): Rematerialize hint after strategy Accept; orphaned filled seats as badges; open = «свободен»; Unassign/Reassign refresh the list; 409/422 as short copy (not JSON). Occupancy «занято/всего». Member still does not see Assign/Unassign/Rematerialize (C27). Empty roster: upsert first, then Suggest→Pick.
Tasks / QG (C30): status filter `all | todo | in_progress | submitted | done | rejected` (server `?status=`; `rejected` = in_progress with last reject reason). Counter «N задач · фильтр». Proof URI is a link; long notes collapse. Reject reason comes back on GET list (not lost after Refresh). Member still has no staff Accept (C27).
UX polish (C29): Suggest **Pick** selects the candidate (not disabled). Chat list is the **last** N messages. Earned refreshes after task Accept. Empty slots/tasks/leads/chat hint the next step. Panels wrap under 640px.
Room RBAC (C27): GET room returns `viewer_role` + `rbac_enforced`. When RBAC is on and the viewer is `member`, the shell hides Terminate / strategy Accept / Assign / QG Accept (API still 403). Default `ROOM_RBAC_DISABLED=true` shows all buttons (demo). Override actor: `sessionStorage.wowlance_actor_sub`.

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
  --data-binary "@..\contracts\strategy\examples\FounderHandoff.sale.json"
```

2. Copy `room_id` from the JSON.
3. Open http://127.0.0.1:5173 → paste id → **Open**, or go to `/rooms/<room_id>`.
4. Expect name, type, timezone, **Staffing locked**, offer / audience / hot criteria, document URI as text (no download).
5. After C2 entitlement, refresh: **Staffing unlocked**, block **Slots** with **Materialize slots** (sale example → two `seller` seats). Locked rooms show «Slots locked until entitlement».
6. After C5 publish, refresh: **Strategy** stays the old offer; **Pending strategy** block with Accept/Reject. Accept → new offer, pending disappears.
7. C6: in **Roster** upsert a freelancer (e.g. `f-1234` / demo), then in **Slots** pick them on an `open` seat and **Assign** → seat becomes `filled` with the sub; assigning the same freelancer again returns idempotent `already_assigned`.
8. Block **Tasks** (available right after room creation, no entitlement needed): type a title → **Add** (→ `todo`), **Start** (→ `in_progress`, assignee from `X-Actor-Sub`). C10 Quality Gate: enter a **proof URI** (+ optional note) → **Submit** (→ `submitted`, missing URI → 422), then **Accept** (→ `done`) or **Reject** with optional reason (→ `in_progress`, proof kept for resubmit). Illegal transitions (incl. direct `in_progress` → `done`) show a 409 error.
9. Block **Leads** (C9, available right after room creation): type a title (+ optional contact name) → **Add** (→ `open`), **Mark hot** (→ `hot`), **Hand to CRM** (→ `handed_to_crm`, shows `crm-stub:<lead_id>`). Handing a hot lead off twice is idempotent (`already_handed`); illegal transitions show a 409 error.
10. C12 on a `filled` seat: **Unassign** frees it back to `open` (sub cleared, assignable again); **Reassign to…** + **Reassign** swaps in another roster member without going through `open`. Reassigning the seated person again returns idempotent `already_assigned`; a sub already seated on another seat in the room shows a 409 `already_seated`.
11. Block **Room health** (C13): after adding slots/tasks/leads, **Refresh** shows matching counts (empty entities are zeros, not errors). **Publish snapshot** writes an outbox row and shows the `outbox_id`; repeat publishes create a new row each time (history).
12. Block **Meet / Jitsi stub** (C14): if `meeting_url` is null, shows **Ensure meeting / Создать ссылку** button → `POST …/meet/ensure` → link `https://meet.jit.si/wowlance-{room_id}`. After ensure, the link is shown and clicking opens Jitsi in a new tab. Repeat ensure is idempotent (same url, `already_exists`).
