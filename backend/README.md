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

`staffing_unlocked` в C1 **всегда** `false` (entitlement — следующий тикет).

**Auth:** endpoint открыт (internal). Позже — Gateway / service token. Keycloak в C1 не внедряем.

Чужие БД / HTTP Strategy не вызываются: весь снимок приходит в теле POST. Файлы — только URI + checksum.

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

## C3: GET room

`GET /api/v1/rooms/{room_id}` отдаёт комнату + снимок стратегии  
([`contracts/wowlance/RoomRead.v1.yaml`](../contracts/wowlance/RoomRead.v1.yaml)).  
`staffing_unlocked` читается из БД как есть (после C1 это `false`). GET ничего не пишет.

| Статус | Когда |
|--------|--------|
| **200** | комната есть |
| **404** | неизвестный `room_id` |

```powershell
curl -s http://127.0.0.1:8000/api/v1/rooms/<room_id>
```

CORS разрешён для Vite `localhost:5173`. UI: [frontend/README.md](../frontend/README.md).

## Тесты

Нужен живой Postgres из `docker compose` (`DATABASE_URL` как в `.env.example`).

```powershell
cd backend
.\.venv\Scripts\pytest -q
```

## Отложено (не C1/C3)

- Keycloak JWT  
- `EntitlementGranted` → `staffing_unlocked=true` (C2, параллельная ветка)  
- Скачивание файлов из object storage  
- Outbox `RoomCreated`  
