# Задание: C11 — Outbox `RoomCreated`

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-17 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c11-room-created-outbox` |
| **База** | актуальный `main` **после merge C8 + C9** |
| **Параллельность** | ✅ **можно параллельно с C10** (влит), **C12–C17** |
| **Фаза** | C11 (исходящее событие при создании комнаты) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 1–2 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md), [05-integration-map](architecture/05-integration-map.md) |
| **Предыдущее** | [C1 FounderHandoff](261010%20-%20задание%20C1%20FounderHandoff.md) · [C9 Hot lead CRM](261016%20-%20задание%20C9%20Hot%20lead%20CRM.md) (таблица outbox) |
| **Параллель** | [C10](261017%20-%20задание%20C10%20Quality%20Gate.md) · [C12](261017%20-%20задание%20C12%20Slot%20unassign.md) · [C13](261017%20-%20задание%20C13%20Room%20health.md) · [C14](261017%20-%20задание%20C14%20Meet%20Jitsi%20stub.md) · [C15](261017%20-%20задание%20C15%20Task%20roster%20assignee.md) · [C16](261017%20-%20задание%20C16%20Earnings%20stub.md) · [C17](261017%20-%20задание%20C17%20Member%20terminated.md) |

C9 должен быть в базе: нужна таблица `outbox_messages`. Если C9 ещё не в `main` — ветка от C9 tip / после merge.

---

## 1. Зачем

По ADR исходящие события комнаты идут через **Outbox** в PG. C9 уже пишет `HotLeadToCrm`. При **создании** комнаты (первый FounderHandoff) соседям нужен сигнал **`RoomCreated`** (Strategy/Order/демо-шина).

Нужен срез: на `status=created` handoff → строка outbox `RoomCreated` / `sent` (stub, без брокера). Повтор handoff `already_exists` → **новую** запись не создавать.

---

## 2. Параллель с C10 — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `domain/handoff.py`, контракт RoomCreated, чтение outbox | Менять `room_tasks` / complete/accept/reject |
| Опционально `GET /internal/v1/outbox` (debug) | Ломать Quality Gate UI |
| Использовать существующую `outbox_messages` | Новая таблица outbox «с нуля», если C9 уже есть |

**Alembic:** обычно **без** миграции (таблица есть). Если нужны индекс/поле — `008_c11_*`. Dual head с C10 → merge на QA.

Не трогать TasksPanel.

---

## 3. Не трогать / не делать

- Живой брокер / HTTP к Strategy.  
- Quality Gate (C10).  
- Менять идемпотентность handoff / fingerprint.  
- Писать outbox на entitlement (later).  
- React обязателен только если останется время (достаточно Swagger/curl + тест).

---

## 4. Продуктовые правила

1. Только при **первом** create комнаты (`FounderHandoffResponse.status == created`).  
2. `already_exists` → outbox не дублировать.  
3. `idempotency_key` = `room:{room_id}:RoomCreated` или `handoff_id` (зафиксировать одно; **рекомендация: `room_id` как uuid string**).  
4. Payload минимум: `room_id`, `handoff_id`, `room_type`, `name`, `founder_sub`, `strategy_id`, `strategy_version`, `created_at`.  
5. `event_type = RoomCreated`, `status = sent`, `sent_at = now` (как HotLead stub).  
6. Ошибка записи outbox **не** должна молча глотать create комнаты: либо транзакция вместе с create, либо create + outbox в одной commit — комната и событие атомарны.

---

## 5. Контракт

Файл: `contracts/strategy/RoomCreated.v1.yaml`  
Пример: `contracts/strategy/examples/RoomCreated.sale.json`

```yaml
id: RoomCreated
version: "1"
direction: WowLance -> platform (Strategy/Order/bus)
channel: outbox
idempotency_key: room_id

payload:
  required: [room_id, handoff_id, room_type, name, founder_sub, strategy_id, strategy_version, created_at]
  properties:
    room_id / handoff_id / strategy_id: uuid
    room_type: sale | develop
    name: string
    founder_sub: string
    strategy_version: string
    created_at: datetime
    staffing_unlocked: boolean  # always false on create
```

Опционально internal debug:

```http
GET /internal/v1/outbox?event_type=RoomCreated
```

(не обязателен для DoD, удобен для QA.)

Строка в `contracts/README.md`.

---

## 6. Код

### 6.1. Handoff

В `domain/handoff.py` после успешного insert room+snapshot — insert `OutboxMessage`.  
Вынести сбор payload в `adapters/room_created.py` или `domain/outbox.py` (тонко).

### 6.2. Тесты

1. Handoff create → в БД 1 row `event_type=RoomCreated`, payload.room_id совпадает.  
2. Повтор того же handoff → `already_exists`, по-прежнему **одна** outbox-строка.  
3. Регрессия: 409 на другой payload; entitlement/GET room зелёные.  
4. Не ломать C9: HotLead outbox-тесты если есть в suite.

### 6.3. Frontend

Не обязателен. Можно одну строку в README: «проверить outbox через SQL / internal GET».

### 6.4. Docs

`backend/README.md` — C11: после handoff проверить outbox (SQL example или curl debug).

---

## 7. DoD

- [ ] Ветка `feature/c11-room-created-outbox` от main после C8+C9.  
- [ ] Контракт RoomCreated + example.  
- [ ] Create handoff пишет outbox; replay не дублирует.  
- [ ] Атомарность с create комнаты.  
- [ ] pytest.  
- [ ] Не меняет task Quality Gate (C10).  
- [ ] PR с проверкой.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c11-room-created-outbox
База: origin/main ПОСЛЕ merge C8 + C9 (нужна outbox_messages из C9).
Параллелен C10 (feature/c10-quality-gate): не трогай room_tasks / Quality Gate.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261017 - задание C11 RoomCreated outbox.md

Сделай C11:
1) contracts RoomCreated.v1.yaml + example + contracts/README
2) при FounderHandoff status=created — OutboxMessage event_type=RoomCreated, idempotent by room_id
3) already_exists — без второй outbox-строки
4) одна транзакция с create комнаты
5) pytest + backend/README

Не делай broker, Quality Gate, entitlement outbox.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Outbox только на create, не на replay.  
- Не ломает C1 fingerprint/409.  
- Переиспользует `outbox_messages` C9.  
- Параллель с C10 чистая.
