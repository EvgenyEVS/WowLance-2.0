# Задание: C12 — Unassign / reassign слота

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-17 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c12-slot-unassign` |
| **База** | актуальный `main` **после merge C10** (лучше после C6+C8+C10) |
| **Параллельность** | ✅ **можно параллельно с C11 · C13 · C14–C16**; с **C17** — общий clear-slot |
| **Фаза** | C12 (освобождение и смена человека на слоте) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 1–2 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md) |
| **Предыдущее** | [C6 Roster assign](261015%20-%20задание%20C6%20Roster%20assign.md) |
| **Параллель** | [C11](261017%20-%20задание%20C11%20RoomCreated%20outbox.md) · [C13](261017%20-%20задание%20C13%20Room%20health.md) · [C14](261017%20-%20задание%20C14%20Meet%20Jitsi%20stub.md) · [C15](261017%20-%20задание%20C15%20Task%20roster%20assignee.md) · [C16](261017%20-%20задание%20C16%20Earnings%20stub.md) · [C17](261017%20-%20задание%20C17%20Member%20terminated.md) |

Без C6 assign в `main` не начинать. C10 уже в `main` — не трогать tasks/QG.

---

## 1. Зачем

После C6 слот можно только **назначить** (`open` → `filled`). В демо нельзя снять человека или заменить на другого без костылей в БД.

Нужен тонкий срез: **unassign** и **reassign** на staffing, без matching Talent и без RBAC ролей.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `domain/staffing.py`, `api/slots.py`, `SlotsPanel` / roster UI | Менять `room_tasks` / complete / accept / reject (C10) |
| Дописать `StaffingSlots.v1.yaml` (unassign/reassign) | Писать `RoomCreated` / трогать handoff create outbox (C11) |
| Append README | Ломать агрегаты C13 ради unassign (C13 только читает слоты) |

**Alembic:** обычно **без** миграции (колонки слота уже есть). Если понадобится audit-поле — `009_c12_*` от head после C10 (`008_c10_*` или merge). Dual head с C11/C13 → merge-миграция на QA.

**Auth:** мутации под существующим `/api/v1` guard (C8). В тестах `AUTH_DISABLED=true` + `X-Actor-Sub` как на assign.

---

## 3. Не трогать / не делать

- Matching / live Talent / shortlist.  
- Quality Gate / tasks (C10).  
- RoomCreated outbox (C11).  
- Room health агрегаты (C13) — можно не знать про health API.  
- Полноценный RBAC teamlead (достаточно актора как на assign).  
- Termination / рейтинги / «я заработал».  
- Менять правило C6 `already_seated` (один sub — один слот в комнате).

---

## 4. Продуктовые правила

1. **Unassign** только если слот `filled` → `open`, `freelancer_sub = null`.  
2. Unassign на `open` → **409** `slot_not_filled` (или эквивалент; зафиксировать в контракте).  
3. Нет комнаты / слота → **404**. Locked staffing → **403** `staffing_locked` (как assign).  
4. **Reassign** = смена человека на **уже filled** слоте:  
   - вариант A (рекомендуемый): `POST …/reassign` с `{ freelancer_sub }` атомарно;  
   - вариант B: клиент unassign + assign (два вызова) — **не** как единственный DoD, если A проще.  
5. Reassign: новый `freelancer_sub` должен быть в roster; иначе **404** `freelancer_not_in_roster`.  
6. Reassign на того же sub → **200** `already_assigned` (идемпотентность).  
7. Reassign на sub, уже сидящего на **другом** слоте этой комнаты → **409** `already_seated`.  
8. Reassign на `open` слот → **409** (сначала assign) **или** разрешить как assign — **зафиксируй: 409 `slot_not_filled`**, чтобы API были ортогональны.  
9. Кто вызывает: любой валидный актор (`get_actor_sub`); отдельной роли teamlead в C12 **нет** (README: RBAC later).

---

## 5. Контракт

Дописать `contracts/wowlance/StaffingSlots.v1.yaml` (+ example при необходимости):

```yaml
paths:
  unassign:
    method: POST
    path: /api/v1/rooms/{room_id}/slots/{slot_id}/unassign
    # body пустой
  reassign:
    method: POST
    path: /api/v1/rooms/{room_id}/slots/{slot_id}/reassign
    request:
      required: [freelancer_sub]
      properties:
        freelancer_sub: { type: string }

response_unassign_200:
  required: [slot, status]
  properties:
    slot: { $ref: "#/slot" }   # status: open, freelancer_sub: null
    status: unassigned

response_reassign_200:
  required: [slot, status]
  properties:
    slot: { $ref: "#/slot" }   # status: filled, new freelancer_sub
    status: reassigned | already_assigned
```

Строка/правка в `contracts/README.md`.

---

## 6. Код

### 6.1. Данные

Новых таблиц нет. Использовать `room_function_slots.status` / `freelancer_sub`.

### 6.2. API

```http
POST /api/v1/rooms/{room_id}/slots/{slot_id}/unassign
POST /api/v1/rooms/{room_id}/slots/{slot_id}/reassign
```

Логика в `domain/staffing.py` рядом с `assign_slot`; тонкие хендлеры в `api/slots.py`.

### 6.3. Тесты

1. Assign → unassign → слот `open`, sub `null`; можно assign снова.  
2. Unassign на `open` → 409.  
3. Reassign filled A→B → `filled` + sub B.  
4. Reassign тот же sub → `already_assigned`.  
5. Reassign на sub с другого слота той же комнаты → 409 `already_seated`.  
6. Unassign/reassign при locked → 403.  
7. Регрессия: assign / materialize / list зелёные; tasks/QG не ломаются.

### 6.4. Frontend

`SlotsPanel` (или соседний staffing-блок):

- для `filled`: кнопки **Unassign** и **Reassign** (выбор другого из roster);  
- для `open`: по-прежнему Assign (C6).

### 6.5. Docs

`backend/README.md` — curl unassign/reassign.  
`frontend/README.md` — кнопки на слотах.

---

## 7. DoD

- [ ] Ветка `feature/c12-slot-unassign` от актуального `main` (после C10).  
- [ ] Контракт + API unassign/reassign + UI + pytest.  
- [ ] Не трогает tasks/QG (C10), handoff/RoomCreated (C11), health (C13).  
- [ ] PR с ручным сценарием.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c12-slot-unassign
База: origin/main ПОСЛЕ merge C10 (нужен C6 assign).
Параллелен C11 (RoomCreated) и C13 (Room health): не трогай handoff/outbox RoomCreated и не пиши health-агрегаты.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261017 - задание C12 Slot unassign.md

Сделай C12:
1) допиши StaffingSlots.v1: unassign + reassign
2) domain/staffing + api/slots: filled→open; reassign на filled
3) правила locked/404/409 already_seated как у assign
4) pytest + SlotsPanel кнопки + README curl

Не делай matching, Quality Gate, RoomCreated, Room health, RBAC ролей.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Unassign и reassign ортогональны assign; нет обхода `already_seated`.  
- Параллель с C11/C13 чистая (только staffing).  
- Dual Alembic `009_*` ожидаем, если кто-то из параллели тоже заведёт миграцию.
