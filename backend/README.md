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

**Auth:** endpoint открыт (internal). Позже — Gateway / service token. Keycloak в C1/C2 не внедряем.

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

Подставьте `room_id` из ответа handoff. Пример в контракте использует placeholder.

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

## Тесты

Нужен живой Postgres из `docker compose` (`DATABASE_URL` как в `.env.example`).

```powershell
cd backend
.\.venv\Scripts\pytest -q
```

## Отложено (не C1/C2)

- Keycloak JWT, React UI  
- Реальный staffing / roster Talent  
- Скачивание файлов из object storage  
- Outbox `RoomCreated`  
- Живой webhook Billing  
