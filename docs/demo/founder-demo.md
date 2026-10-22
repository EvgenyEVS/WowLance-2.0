# Founder demo (C26)

Один воспроизводимый путь на stubs: **handoff → entitlement → команда → QG → Hot → health**.  
Live Strategy / CRM / Talent / Keycloak / Gateway **не** нужны.

Каждый прогон скрипта создаёт **новую** комнату (свежий `handoff_id`). Повтор того же JSON не требуется.

## Перед стартом

1. Postgres: `docker compose up -d db`
2. Backend: `alembic upgrade head` + uvicorn `:8000` (`AUTH_DISABLED=true`)
3. UI (ручной шаг): `cd frontend; npm run dev` → http://127.0.0.1:5173

Если `INTERNAL_AUTH_DISABLED=false`, задайте `INTERNAL_SERVICE_TOKEN` в окружении до скрипта.

## Скрипт

Из корня репозитория:

```powershell
powershell -File scripts/founder-demo.ps1
```

Скрипт печатает `room_id` и URL UI `/rooms/{id}`. Дальше — глазами в браузере.

## Что должно получиться в API

| Шаг | Endpoint | Ожидание |
|-----|----------|----------|
| Handoff | `POST /internal/v1/handoffs` | 201, `staffing_unlocked=false` |
| Entitlement | `POST /internal/v1/entitlements` | `granted`, staffing unlocked |
| Materialize | `POST /api/v1/rooms/{id}/slots/materialize` | open seats из staffing intent |
| Roster ×2 | `POST /internal/v1/roster` | `freelancer-demo-sub`, `teamlead-demo-sub` |
| Assign | `POST …/slots/{slot}/assign` | первый open слот → freelancer |
| Task | create → start → complete(proof) → accept | статус `done`, earned stub |
| Lead | create → mark-hot → handoff-crm | `handed_to_crm` + crm_ref |
| Meet | `POST …/meet/ensure` | Jitsi stub URL |
| Health | `GET …/health` (+ optional publish) | слоты/задачи/лиды/earned > 0 |

Мутации `/api/v1/*` идут с `X-Actor-Sub: founder-demo-sub` (start/complete задачи — `freelancer-demo-sub`).

## Что смотреть в UI

Откройте URL из вывода скрипта.

1. **Badge** «Staffing unlocked», founder = `founder-demo-sub`.
2. **Meet** — ссылка на звонок уже есть (ensure идемпотентен).
3. **Slots** — один filled (`freelancer-demo-sub`), остальные open. Suggest / Assign можно потрогать на втором seat.
4. **Tasks** — задача `Demo first dials` в `done` с proof. **Earned** — 10.00 USD (stub).
5. **Leads** — лид в `handed_to_crm`.
6. **Chat** — пустой: напишите сообщение, Refresh.
7. **Room health** — Refresh; цифры совпадают с GET health. Publish snapshot — stub outbox.

## Если скрипт упал

- API не на `:8000` — передайте `-ApiBase http://127.0.0.1:8001`
- 401 на `/internal/v1/*` — internal guard включён без токена
- 403 `staffing_locked` — entitlement не прошёл
- 422 на мутациях — нет `X-Actor-Sub` (скрипт ставит сам)

Золотой путь G1–G10 этим пакетом не меняется: только вызовы уже существующих endpoints.
