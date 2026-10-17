# Задание: C13 — Room health stub → Strategy

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-17 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c13-room-health` |
| **База** | актуальный `main` **после merge C10** (желательно C7+C9+C10; C6 желателен для слотов) |
| **Параллельность** | ✅ **можно параллельно с C11 · C12 · C14–C17** |
| **Фаза** | C13 (минимальный агрегат комнаты для витрины Стратегии) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md), [05-integration-map](architecture/05-integration-map.md) |
| **Предыдущее** | [C3 Room read](261010%20-%20задание%20C3%20Room%20read%20shell.md) · [C9 Hot lead](261016%20-%20задание%20C9%20Hot%20lead%20CRM.md) · [C10 Quality Gate](261017%20-%20задание%20C10%20Quality%20Gate.md) |
| **Параллель** | [C11](261017%20-%20задание%20C11%20RoomCreated%20outbox.md) · [C12](261017%20-%20задание%20C12%20Slot%20unassign.md) · [C14](261017%20-%20задание%20C14%20Meet%20Jitsi%20stub.md) · [C15](261017%20-%20задание%20C15%20Task%20roster%20assignee.md) · [C16](261017%20-%20задание%20C16%20Earnings%20stub.md) · [C17](261017%20-%20задание%20C17%20Member%20terminated.md) |

По ADR фаундер-аналитика — витрина в **Стратегии**; WowLance отдаёт **агрегаты**. Здесь — первый read-срез + stub outbox, без живого брокера и без UI Стратегии.

---

## 1. Зачем

Соседу (Strategy) нужны цифры по комнате: сколько мест занято, как задачи, сколько Hot/ушло в CRM. Сейчас есть сырые list API, нет одного контракта «здоровье комнаты».

Нужен срез: **`GET …/health`** (или `/summary`) с агрегатами + опционально запись outbox **`RoomHealthSnapshot`** (stub `sent`, как HotLead/RoomCreated). Без графиков, без CRM-аналитики сделок, без live Strategy HTTP.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| Новые `domain/room_health.py`, `api/room_health.py` (имена свободные) | Менять complete/accept/reject / proof (C10) |
| Читать `room_function_slots`, `room_tasks`, `room_leads`, room/snapshot | Менять `domain/handoff.py` ради RoomCreated (C11) |
| Outbox `event_type=RoomHealthSnapshot` в существующую `outbox_messages` | Менять assign/unassign логику (C12) — только **читать** статусы слотов |
| Опционально блок на `RoomPage` | Ломать StaffingSlots мутации |

**Alembic:** обычно **без** миграции. Если нужен индекс по `event_type` — `009_c13_*`. Dual head с C11/C12 → merge на QA.

**Auth:** `GET` health под `/api/v1` (C8). Emit outbox — internal или authenticated POST; **рекомендация:**  
- `GET /api/v1/rooms/{id}/health` — read;  
- `POST /internal/v1/rooms/{id}/health/publish` — пишет outbox (stub «отправили в Strategy»).

---

## 3. Не трогать / не делать

- Живой брокер / HTTP в Strategy.  
- Виджеты фаундера в UI Стратегии.  
- Quality Gate мутации (C10).  
- RoomCreated на handoff (C11) — новый `event_type`, не править create path.  
- Unassign/reassign (C12).  
- Биллинг / «я заработал» / рейтинги.  
- Jira / matching.

---

## 4. Продуктовые правила

1. Агрегат **только read** из локальной PG WowLance.  
2. Минимальный payload health:

   | Блок | Поля |
   |------|------|
   | room | `room_id`, `room_type`, `name`, `staffing_unlocked`, `strategy_id`, `strategy_version` |
   | slots | `open`, `filled`, `cancelled` (counts); `total` |
   | tasks | counts by status: `todo`, `in_progress`, `submitted`, `done` (C10) |
   | leads | `total`, `hot`, `handed_to_crm` (или как названы статусы в C9 — взять фактические enum) |

3. Нет комнаты → **404**.  
4. Пустые сущности → нули, не 404.  
5. **Publish** (если в scope): одна строка outbox `RoomHealthSnapshot`, `status=sent`, `sent_at=now`; payload = тот же snapshot + `captured_at`.  
6. Идемпотентность publish: **рекомендация** — каждый publish = **новая** строка (история снимков) **или** ключ `room:{id}:RoomHealthSnapshot:{date}` — зафиксируй одно; для демо достаточно **всегда новая строка** + тест «две publish → две outbox».  
7. Не дублировать и не ломать `HotLeadToCrm` / будущий `RoomCreated`.

---

## 5. Контракт

Файл: `contracts/wowlance/RoomHealth.v1.yaml`  
Пример: `contracts/wowlance/examples/RoomHealth.sale.json`

```yaml
id: RoomHealth
version: "1"
direction: WowLance -> Strategy (витрина)
channel: https + optional outbox

paths:
  get:
    method: GET
    path: /api/v1/rooms/{room_id}/health
  publish:   # optional but preferred for DoD outbox
    method: POST
    path: /internal/v1/rooms/{room_id}/health/publish

snapshot:
  required: [room_id, captured_at, room, slots, tasks, leads]
  properties:
    room_id: uuid
    captured_at: datetime
    room: { room_type, name, staffing_unlocked, strategy_id, strategy_version }
    slots: { total, open, filled, cancelled }
    tasks: { todo, in_progress, submitted, done }
    leads: { total, hot, handed_to_crm }  # имена статусов = код C9
```

Outbox (если publish):

```yaml
event_type: RoomHealthSnapshot
idempotency_key: optional / per-publish uuid
payload: { $ref: snapshot }
status: sent
```

Строка в `contracts/README.md`.

---

## 6. Код

### 6.1. Домен

`domain/room_health.py` (или `domain/health.py`): один запрос/несколько count-ов → dataclass/schema `RoomHealthOut`.  
Не тащить бизнес-логику assign/tasks внутрь — только SELECT/count.

### 6.2. API

```http
GET  /api/v1/rooms/{room_id}/health
POST /internal/v1/rooms/{room_id}/health/publish   # stub outbox
```

Опционально debug: `GET /internal/v1/outbox?event_type=RoomHealthSnapshot`.

### 6.3. Тесты

1. Пустая комната после handoff → health с нулями (или slots=0 до materialize).  
2. Materialize + assign → `slots.filled >= 1`.  
3. Tasks: создать/start/complete(proof) → counts отражают `submitted` (C10).  
4. Lead Hot → `leads.hot` / handed растут по правилам C9.  
5. Publish → outbox row `RoomHealthSnapshot`; повтор publish не ломает GET.  
6. Регрессия: handoff, entitlement, tasks QG, leads — зелёные.  
7. Не требует C12: тесты не зовут unassign.

### 6.4. Frontend

Не обязателен для DoD. Можно короткая карточка **Room health** на `RoomPage` (цифры) + кнопка Publish — плюс к демо. Если времени мало — только curl/Swagger + README.

### 6.5. Docs

`backend/README.md` — C13: пример GET health + SQL/curl outbox после publish.

---

## 7. DoD

- [ ] Ветка `feature/c13-room-health` от `main` после C10.  
- [ ] Контракт `RoomHealth.v1` + example.  
- [ ] `GET …/health` с агрегатами slots/tasks/leads.  
- [ ] Publish → outbox `RoomHealthSnapshot` (stub).  
- [ ] pytest.  
- [ ] Не меняет QG (C10), RoomCreated path (C11), assign/unassign (C12).  
- [ ] PR с проверкой.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c13-room-health
База: origin/main ПОСЛЕ merge C10 (нужны tasks со submitted + leads + slots).
Параллелен C11 (RoomCreated) и C12 (unassign): не трогай handoff create outbox и staffing мутации.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261017 - задание C13 Room health.md

Сделай C13:
1) contracts RoomHealth.v1.yaml + example + contracts/README
2) GET /api/v1/rooms/{id}/health — агрегаты room/slots/tasks/leads
3) POST /internal/v1/rooms/{id}/health/publish — OutboxMessage RoomHealthSnapshot (stub sent)
4) pytest + backend/README

Не делай live Strategy, broker, Quality Gate мутации, unassign, RoomCreated на handoff.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Только read + свой outbox type; не пишет в tasks/slots.  
- Counts включают `submitted` (C10).  
- Не конфликтует с C11 `RoomCreated` и C12 unassign.  
- Dual Alembic `009_*` ожидаем.
