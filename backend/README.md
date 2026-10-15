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

## Тесты

Нужен живой Postgres из `docker compose` (`DATABASE_URL` как в `.env.example`).

```powershell
cd backend
.\.venv\Scripts\pytest -q
```

## Отложено (не C1–C5)

- Keycloak JWT / реальная роль teamlead  
- Matching / assign freelancer / Talent roster  
- Пересборка слотов после Accept  
- Скачивание файлов из object storage  
- Outbox `RoomCreated`  
- Живой webhook Billing  

