# WowLance 2.0 — backend (FastAPI)

## C1: FounderHandoff

`POST /internal/v1/handoffs` создаёт комнату + immutable `StrategySnapshot` по контракту  
[`contracts/wowlance/FounderHandoff.v1.yaml`](../contracts/wowlance/FounderHandoff.v1.yaml).

| Статус | Когда |
|--------|--------|
| **201** | первый create (`status: created`) |
| **200** | повтор того же `handoff_id` + того же payload (`status: already_exists`) |
| **409** | тот же `handoff_id`, другой payload |
| **422** | валидация тела |

`staffing_unlocked` после handoff **false**, пока не придёт C2 entitlement.

**Auth:** endpoint открыт (internal). Позже — Gateway / service token. Keycloak в C1–C3 не внедряем.

Чужие БД / HTTP Strategy не вызываются: весь снимок приходит в теле POST. Файлы — только URI + checksum.

## C2: EntitlementGranted

`POST /internal/v1/entitlements` открывает staffing на **уже существующей** комнате  
([`contracts/wowlance/EntitlementGranted.v1.yaml`](../contracts/wowlance/EntitlementGranted.v1.yaml)).

| Статус | Когда |
|--------|--------|
| **200** | первый grant (`status: granted`, `staffing_unlocked: true`) |
| **200** | повтор того же `entitlement_id` (`status: already_granted`) |
| **404** | неизвестный `room_id` |
| **409** | тот же `entitlement_id` уже привязан к другой комнате |
| **422** | валидация тела |

Повторный FounderHandoff **не** сбрасывает `staffing_unlocked` обратно в `false`.

Revoke / «заблокировать снова» в C2 нет.

## C3: GET room

`GET /api/v1/rooms/{room_id}` отдаёт комнату + снимок стратегии  
([`contracts/wowlance/RoomRead.v1.yaml`](../contracts/wowlance/RoomRead.v1.yaml)).  
`staffing_unlocked` читается из БД как есть. GET ничего не пишет.

| Статус | Когда |
|--------|--------|
| **200** | комната есть |
| **404** | неизвестный `room_id` |

CORS разрешён для Vite `localhost:5173`. UI: [frontend/README.md](../frontend/README.md).

## Поднять локально

```powershell
# из корня репо
docker compose up -d db
# Postgres на хосте: localhost:5433 (см. docker-compose.yml)

cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy ..\.env.example .env   # если ещё нет

.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Health: http://127.0.0.1:8000/health  
OpenAPI: http://127.0.0.1:8000/docs

## curl (example sale)

```powershell
curl -s -X POST http://127.0.0.1:8000/internal/v1/handoffs `
  -H "Content-Type: application/json" `
  --data-binary "@..\contracts\wowlance\examples\FounderHandoff.sale.json"
```

Повтор того же JSON → `200` + `"status":"already_exists"` и тот же `room_id`.

## curl (entitlement, C2)

Подставьте `room_id` из ответа handoff.

```powershell
curl -s -X POST http://127.0.0.1:8000/internal/v1/entitlements `
  -H "Content-Type: application/json" `
  -d '{
    "entitlement_id": "33333333-3333-3333-3333-333333333333",
    "room_id": "<room_id from handoff>",
    "source": "stub"
  }'
```

Повтор того же `entitlement_id` → `200` + `"status":"already_granted"`.

## curl (GET room, C3)

```powershell
curl -s http://127.0.0.1:8000/api/v1/rooms/<room_id>
```

`strategy` — только **active** снимок. Пока есть proposal, в ответе ещё `pending_strategy`.

## C4: Staffing slots

Слоты **не** создаются на handoff/entitlement. Явный POST после unlock читает локальный `staffing_intent` **active** снимка.

`GET /api/v1/rooms/{room_id}/slots` и `POST /api/v1/rooms/{room_id}/slots/materialize`  
([`contracts/wowlance/StaffingSlots.v1.yaml`](../contracts/wowlance/StaffingSlots.v1.yaml)).

| Статус | Когда |
|--------|--------|
| **200** GET | staffing unlocked; тело: `slots` |
| **200** POST | `status: materialized` или `already_materialized` (слоты не дублируются) |
| **403** | `staffing_unlocked=false` (`detail: staffing_locked`) |
| **404** | нет комнаты |
| **422** | невалидный `room_id` |

Пустой / отсутствующий `staffing_intent.slots` → `200` и `slots: []`. Auth открыт (Gateway / JWT later).

```powershell
# после handoff + entitlement, подставить room_id
curl -s -X POST http://127.0.0.1:8000/api/v1/rooms/<room_id>/slots/materialize
curl -s http://127.0.0.1:8000/api/v1/rooms/<room_id>/slots
```

Sale example → два слота `seller` `#1` и `#2`, `status: open`.

## C5: Strategy publish / Accept / Reject

Новая версия стратегии не применяется молча.  
`POST /internal/v1/strategy-publications` создаёт `pending` proposal  
([`contracts/wowlance/StrategyPublished.v1.yaml`](../contracts/wowlance/StrategyPublished.v1.yaml)).

| Статус | Когда |
|--------|--------|
| **200** publish | `pending` или повтор `publication_id` → `already_exists` |
| **409** publish | уже есть pending; `strategy_version` == active; publication на другую комнату |
| **404** | нет комнаты / нет proposal |
| **200** accept/reject | `X-Actor-Sub` обязателен |
| **422** | нет `X-Actor-Sub` |
| **409** decide | proposal уже не `pending` |

Accept: старый snapshot → `superseded`, новый insert `active` (payload не UPDATE).  
Reject: active не меняется.  
**Слоты C4 не пересобираются** при Accept (later).

```powershell
# room_id из handoff; подставьте его в JSON publication
curl -s -X POST http://127.0.0.1:8000/internal/v1/strategy-publications `
  -H "Content-Type: application/json" `
  --data-binary "@..\contracts\wowlance\examples\StrategyPublished.sale.json"

curl -s http://127.0.0.1:8000/api/v1/rooms/<room_id>

curl -s -X POST http://127.0.0.1:8000/api/v1/rooms/<room_id>/strategy-proposals/<proposal_id>/accept `
  -H "X-Actor-Sub: teamlead-demo-sub"
```

## C6: Local roster + Assign slot

Фрилансер приходит из Talent в **локальный roster** (stub, своя БД, без live Talent).  
Назначение садит человека из roster на **открытый** слот комнаты (per-slot).

`POST /internal/v1/roster` — upsert (idempotent по `freelancer_sub`)  
([`contracts/wowlance/TalentRosterUpsert.v1.yaml`](../contracts/wowlance/TalentRosterUpsert.v1.yaml)).  
`GET /api/v1/roster` — список для UI.  
`POST /api/v1/rooms/{room_id}/slots/{slot_id}/assign` — назначение  
([`contracts/wowlance/StaffingSlots.v1.yaml`](../contracts/wowlance/StaffingSlots.v1.yaml), блок SlotAssign).

| Статус | Когда |
|--------|--------|
| **200** roster | `upserted` (новый / изменён) или `already_exists` (тот же payload) |
| **200** assign | `assigned`; повтор того же `freelancer_sub` на тот же слот → `already_assigned` |
| **403** assign | `staffing_unlocked=false` (`detail: staffing_locked`) |
| **404** assign | нет комнаты / нет слота в комнате / `freelancer_not_in_roster` |
| **409** assign | слот занят другим (`slot_already_filled`) / этот фрилансер уже на другом слоте комнаты (`already_seated`) |
| **422** assign | невалидное тело / нет `X-Actor-Sub` |

Правила: roster **глобальный** по `freelancer_sub`, назначение — per-slot. Один фрилансер — максимум один слот в комнате. Matching, скоринг, Keycloak — вне C6.

```powershell
# 1) upsert фрилансера в roster
curl -s -X POST http://127.0.0.1:8000/internal/v1/roster `
  -H "Content-Type: application/json" `
  --data-binary "@..\contracts\wowlance\examples\TalentRosterUpsert.json"

curl -s http://127.0.0.1:8000/api/v1/roster

# 2) handoff -> entitlement -> materialize (см. выше), затем взять slot id
curl -s -X POST http://127.0.0.1:8000/api/v1/rooms/<room_id>/slots/<slot_id>/assign `
  -H "Content-Type: application/json" `
  -H "X-Actor-Sub: teamlead-demo-sub" `
  -d '{ "freelancer_sub": "f-1234" }'
# -> { "slot": { "status": "filled", "freelancer_sub": "f-1234", ... }, "status": "assigned" }
```

## C7: Room tasks

Минимальный трекер комнаты: создать → взять → сдать. Без Quality Gate.  
([`contracts/wowlance/RoomTasks.v1.yaml`](../contracts/wowlance/RoomTasks.v1.yaml)).

| Метод | Путь |
|-------|------|
| `GET` | `/api/v1/rooms/{room_id}/tasks` |
| `POST` | `/api/v1/rooms/{room_id}/tasks` |
| `POST` | `/api/v1/rooms/{room_id}/tasks/{task_id}/start` |
| `POST` | `/api/v1/rooms/{room_id}/tasks/{task_id}/complete` |

Статусы: `todo` → `in_progress` → `done`. Другие переходы → **409**.  
`assignee_sub` — свободная строка (без FK на roster); при `start` заполняется из `X-Actor-Sub`, если пусто.

| Статус | Когда |
|--------|--------|
| **201** create | задача создана в `todo` |
| **200** start/complete | переход выполнен |
| **404** | нет комнаты или задачи |
| **409** | недопустимый переход статуса |
| **422** | валидация; нет `X-Actor-Sub` на мутациях |

Задачи доступны **всегда** после создания комнаты — `staffing_unlocked` (C2) не блокирует. Get — без пагинации (лимит 100).

```powershell
# room_id из handoff; мутации требуют X-Actor-Sub
curl -s http://127.0.0.1:8000/api/v1/rooms/<room_id>/tasks

curl -s -X POST http://127.0.0.1:8000/api/v1/rooms/<room_id>/tasks `
  -H "Content-Type: application/json" `
  -H "X-Actor-Sub: teamlead-demo-sub" `
  -d '{ "title": "Call the first 20 leads" }'

curl -s -X POST http://127.0.0.1:8000/api/v1/rooms/<room_id>/tasks/<task_id>/start `
  -H "X-Actor-Sub: freelancer-demo-sub"

curl -s -X POST http://127.0.0.1:8000/api/v1/rooms/<room_id>/tasks/<task_id>/complete `
  -H "X-Actor-Sub: freelancer-demo-sub"
```

## C8: Keycloak JWT + shadow User

Клиентские API `/api/v1/*` проверяют `Authorization: Bearer <access_token>` (RS256, JWKS). Первый успешный запрос upsert-ит shadow-пользователя в `users` по `sub`. Контракт: [`contracts/wowlance/AuthBearer.v1.yaml`](../contracts/wowlance/AuthBearer.v1.yaml). Модуль: `app/auth/` (JWT verify + `require_user` + `get_actor_sub`).

| Поведение | `AUTH_DISABLED=true` (default, pytest) | `AUTH_DISABLED=false` |
|-----------|------------------------------------------|------------------------|
| `/api/v1/*` (rooms, slots, roster GET, strategy decide, tasks) | открыт — C1–C7 как раньше | **401** без валидного JWT |
| `/health`, `/internal/v1/*` | открыт | открыт (service token later) |
| actor мутаций | `X-Actor-Sub` (422 без него) | `sub` из JWT; `X-Actor-Sub` игнорируется |
| `/auth/stub-jwks`, `/auth/stub-token` | 404 | 200 только при `AUTH_STUB_JWKS=true` |

Env (`.env`, см. [.env.example](../.env.example)): `AUTH_DISABLED`, `KEYCLOAK_ISSUER`, `KEYCLOAK_AUDIENCE` (пусто → без проверки `aud`), `KEYCLOAK_JWKS_URL` (пусто → `issuer + /protocol/openid-connect/certs`), `AUTH_STUB_JWKS` (dev-only).

### Токен за 2 минуты (stub JWKS, без Keycloak)

```powershell
# 1) в backend/.env поставить: AUTH_DISABLED=false, AUTH_STUB_JWKS=true
#    перезапустить uvicorn
# 2) mint demo-токена:
curl.exe -s -X POST http://127.0.0.1:8000/auth/stub-token `
  -H "Content-Type: application/json" `
  -d '{"sub":"demo-user","name":"Demo User"}'
# -> { "access_token": "eyJ...", "sub": "demo-user" }

# 3) клиентский API:
curl.exe -s http://127.0.0.1:8000/api/v1/rooms/<room_id> `
  -H "Authorization: Bearer eyJ..."
# без Bearer -> 401; /internal/v1/handoffs и /health без токена -> работают
```

`GET /auth/stub-jwks` отдаёт публичный ключ, RSA-ключ генерируется в памяти процесса — режим **«не для prod»** (оба endpoint-а отдают 404, пока `AUTH_STUB_JWKS=false`).

### Настоящий Keycloak

`AUTH_DISABLED=false` + `AUTH_STUB_JWKS=false` + `KEYCLOAK_ISSUER` / `KEYCLOAK_JWKS_URL` своего realm — верификация идёт по JWKS из issuer, токен выпускает сам Keycloak. Платформенный прод-Keycloak, Gateway, RBAC (teamlead vs freelancer) и token exchange — вне C8.


## C9: Hot lead → CRM stub

Лиды комнаты: создать → **hot** → выгрузить в CRM (stub). Своя БД, без live CRM / OAuth.  
([`contracts/wowlance/RoomLeads.v1.yaml`](../contracts/wowlance/RoomLeads.v1.yaml),
исходящее событие — [`contracts/wowlance/HotLeadToCrm.v1.yaml`](../contracts/wowlance/HotLeadToCrm.v1.yaml)).

| Метод | Путь |
|-------|------|
| `GET` | `/api/v1/rooms/{room_id}/leads` |
| `POST` | `/api/v1/rooms/{room_id}/leads` |
| `POST` | `/api/v1/rooms/{room_id}/leads/{lead_id}/mark-hot` |
| `POST` | `/api/v1/rooms/{room_id}/leads/{lead_id}/handoff-crm` |

Статусы: `open` → `hot` → `handed_to_crm`. Другие переходы → **409**.
`handoff-crm` пишет строку в `outbox_messages` (`event_type: HotLeadToCrm`,
`status: sent`, `idempotency_key = lead_id`) и проставляет `crm_ref = crm-stub:<lead_id>`.
Повторный `handoff-crm` идемпотентен: **200** + `status: already_handed`, второй outbox-строки нет.

| Статус | Когда |
|--------|--------|
| **201** create | лид создан в `open` |
| **200** mark-hot | `open` → `hot` |
| **200** handoff | `hot` → `handed_to_crm` (+ outbox); повтор → `already_handed` |
| **404** | нет комнаты или лида |
| **409** | недопустимый переход (`mark-hot` не из `open`; `handoff` не из `hot`) |
| **422** | валидация; нет `X-Actor-Sub` на мутациях |

Лиды доступны **всегда** после создания комнаты — `staffing_unlocked` (C2) не требуется.
Get — без пагинации (лимит 100). Auth — заглушка `X-Actor-Sub` (как C7), пока нет C8.

```powershell
# room_id из handoff; мутации требуют X-Actor-Sub
curl -s -X POST http://127.0.0.1:8000/api/v1/rooms/<room_id>/leads `
  -H "Content-Type: application/json" `
  -H "X-Actor-Sub: founder-demo-sub" `
  -d '{ "title": "Warm intro to Acme", "contact_name": "Jane" }'

curl -s -X POST http://127.0.0.1:8000/api/v1/rooms/<room_id>/leads/<lead_id>/mark-hot `
  -H "X-Actor-Sub: founder-demo-sub"

curl -s -X POST http://127.0.0.1:8000/api/v1/rooms/<room_id>/leads/<lead_id>/handoff-crm `
  -H "X-Actor-Sub: founder-demo-sub"
# -> { "lead": {... "status": "handed_to_crm", "crm_ref": "crm-stub:<lead_id>" },
#      "crm_ref": "crm-stub:<lead_id>", "status": "handed" }

curl -s http://127.0.0.1:8000/api/v1/rooms/<room_id>/leads
```

## Тесты

Нужен живой Postgres из `docker compose` (`DATABASE_URL` как в `.env.example`).

C8: pytest всегда идёт с `AUTH_DISABLED=true` (форсирует `tests/conftest.py`) —
Keycloak для регресса C1–C7 не нужен; строгий режим включается точечно в
`tests/test_auth_c8.py`.

```powershell
cd backend
.\.venv\Scripts\pytest -q
```

> **Внимание: после `pytest` dev-БД остаётся без таблиц.**
> Тесты используют ту же БД, что и приложение (`tests/conftest.py` берёт
> `settings.database_url`), и фикстура вызывает `drop_all` в teardown.
> Сваггер и UI после прогона начнут отдавать ошибки на любых запросах к данным
> (`/health` при этом продолжит работать).
>
> Простого `alembic upgrade head` недостаточно: штамп в `alembic_version`
> остаётся на head, поэтому миграции заново не выполняются. Пересобери схему:
>
> ```powershell
> cd backend
> .\.venv\Scripts\alembic stamp base
> .\.venv\Scripts\alembic upgrade head
> ```
>
> Известное ограничение: тестам нужна отдельная БД, пока не сделано.

## Отложено (не C1–C8)

## Отложено (не C1–C9)

- Полный RBAC (teamlead vs freelancer на каждый endpoint), Gateway, token exchange  
- Живой Keycloak в compose / demo realm (C8 закрыт stub-JWKS, см. выше)  
- Matching / live Talent / shortlist  
- Unassign слота  
- Quality Gate: proof-файлы, рейтинги, reject с причиной  
- Пересборка слотов после Accept  
- Скачивание файлов из object storage  
- Живой CRM / OAuth: сейчас `HotLeadToCrm` только в локальном outbox  
- Outbox `RoomCreated`  
- Живой webhook Billing  


