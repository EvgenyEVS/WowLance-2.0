# Задание: C4 — Staffing slots (gated)

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-15 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c4-staffing-slots` |
| **База** | актуальный `main` **после merge C2 + C3** |
| **Параллельность** | ✅ **можно делать параллельно с C5** (`feature/c5-strategy-accept`) |
| **Фаза** | C4 (слоты комнаты под флагом entitlement) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md) |
| **Предыдущее** | [C2 Entitlement](261010%20-%20задание%20C2%20Entitlement%20unlock.md) · [C3 Room read](261010%20-%20задание%20C3%20Room%20read%20shell.md) |
| **Параллель** | [C5 Strategy Accept](261015%20-%20задание%20C5%20Strategy%20accept.md) |

Если C2/C3 ещё не в `main`: дождаться merge. Не начинать C4 от ветки без `staffing_unlocked` и `GET /rooms`.

---

## 1. Зачем

После C2 флаг `staffing_unlocked` есть, но **ничего не открывает**. В handoff уже лежит `staffing_intent.slots` (например `seller × 2`). Нужен первый срез staffing: материализовать **слоты-места** в БД комнаты и показать их в UI — только когда staffing разблокирован.

Matching, Talent roster, назначение фрилансеров — **не** здесь. Цель: entitlement перестаёт быть декоративным бейджем.

---

## 2. Параллель с C5 — правила стыковки

| Можно | Нельзя |
|-------|--------|
| Новые файлы: `api/slots.py`, `domain/staffing.py`, миграция `room_function_slots` | Менять модель `StrategySnapshot` / proposal-таблицы C5 |
| Расширить `RoomRead` **опциональным** полем `slots` **или** отдельный GET (предпочтительно отдельный) | Ломать контракт `RoomRead.v1` без строки в YAML |
| Трогать `RoomPage` блок «Slots» | Править Accept/Reject / `StrategyPublished` |

Merge: при конфликте в `main.py` / `RoomPage.tsx` — оставить оба блока (slots + strategy pending).

---

## 3. Не трогать / не делать

- Matching, поиск кандидатов, Talent API / live JOIN.  
- Назначение `freelancer_sub` на слот (можно nullable-колонку заранее, без API assign).  
- Keycloak / роли teamlead (endpoint открыт или stub-заголовок — как C1–C3).  
- Revoke entitlement, биллинг, Order UI.  
- `StrategyPublished` / Accept (это C5).  
- Outbox `RoomCreated`, CRM, Jira, задачи.  
- Копировать Django 1.0 staffing UI as-is.

---

## 4. Продуктовые правила

1. Чужие БД не читать; слоты берутся из **локального** `staffing_intent` снимка комнаты.  
2. Пока `staffing_unlocked=false`:  
   - материализация / мутации слотов → **403** (`staffing_locked`);  
   - GET списка слотов → **403** **или** пустой список + явный сигнал locked (выбрать одно и зафиксировать в контракте; **рекомендация: 403** на staffing API).  
3. При `staffing_unlocked=true`: можно один раз (идемпотентно) создать места из `staffing_intent.slots`.  
4. Правило разворота: для каждого элемента `{ role_key, count, level_min? }` создать `count` строк слотов с `seat_index` 1…count.  
5. Нет `staffing_intent` / пустые `slots` → materialize → **200** + `slots: []` (не 422).  
6. Повторный materialize того же состояния → **200** + `status: already_materialized`, слоты не дублировать.  
7. Handoff / entitlement **не** обязаны сами создавать слоты (создание — явный POST materialize **или** лениво при первом GET после unlock — зафиксируй один способ в README; **рекомендация: явный POST**).

---

## 5. Контракт (C0 этого шага)

### 5.1. StaffingSlotsRead

Файл: `contracts/wowlance/StaffingSlots.v1.yaml`  
Пример: `contracts/wowlance/examples/StaffingSlots.sale.json`

```yaml
id: StaffingSlots
version: "1"
direction: client -> WowLance
channel: https

paths:
  list:
    method: GET
    path: /api/v1/rooms/{room_id}/slots
  materialize:
    method: POST
    path: /api/v1/rooms/{room_id}/slots/materialize

slot:
  required: [id, room_id, role_key, seat_index, status]
  properties:
    id: uuid
    room_id: uuid
    role_key: string          # e.g. seller, teamlead
    seat_index: integer       # 1..N within role_key
    level_min: string | null
    status: open | filled | cancelled   # C4: всегда open после materialize
    freelancer_sub: string | null       # C4: всегда null

response_list_200:
  required: [room_id, staffing_unlocked, slots]
  properties:
    room_id: uuid
    staffing_unlocked: true
    slots: [slot]

response_materialize_200:
  required: [room_id, status, slots]
  properties:
    room_id: uuid
    status: materialized | already_materialized
    slots: [slot]

errors:
  - { code: 403, when: "staffing_unlocked is false" }
  - { code: 404, when: "room_id does not exist" }
  - { code: 422, when: "validation failed" }
```

Строка в `contracts/README.md`.

`RoomRead.v1` **не обязан** включать массив слотов; UI C4 ходит отдельным GET (проще параллель с C5).

---

## 6. Что сделать в коде

### 6.1. Данные

Таблица `room_function_slots` (имя можно уточнить, смысл — место в комнате):

| Колонка | Тип | Заметки |
|---------|-----|---------|
| `id` | UUID PK | |
| `room_id` | UUID FK → rooms | ON DELETE CASCADE, index |
| `role_key` | str | |
| `seat_index` | int | |
| `level_min` | str nullable | |
| `status` | str | default `open` |
| `freelancer_sub` | str nullable | всегда null в C4 |
| `created_at` | timestamptz | |

Unique: `(room_id, role_key, seat_index)`.

Alembic-миграция от головы `main` (после C2/C3).

### 6.2. API

```http
POST /api/v1/rooms/{room_id}/slots/materialize
GET  /api/v1/rooms/{room_id}/slots
```

Логика в `domain/staffing.py` (или `domain/slots.py`), тонкий router.  
Источник слотов: `StrategySnapshot.staffing_intent` **активной** комнаты (после C5 — тот снимок, который сейчас active; до merge C5 — единственный snapshot C1).

Auth: открытый API + пометка в README («Gateway / JWT later»), как C3.

### 6.3. Тесты (pytest + PG)

1. Handoff (example sale) → entitlement → materialize → 2 слота `seller` с seat_index 1 и 2, status `open`.  
2. Повтор materialize → `already_materialized`, в БД по-прежнему 2 строки.  
3. Без entitlement → materialize **403**; GET slots **403**.  
4. Неизвестный `room_id` → **404**.  
5. Handoff без slots / `staffing_intent: null` → materialize → `[]`.  
6. Регрессия: C1/C2/C3 тесты зелёные.

### 6.4. Frontend

На `RoomPage` (после успешного GET room):

1. Если `staffing_unlocked === false` — текст вроде «Slots locked until entitlement» (без кнопки materialize или disabled).  
2. Если unlocked — кнопка **Materialize slots** + список слотов (`role_key`, `#seat`, status).  
3. После materialize — обновить список; повтор кнопки безопасен (already_materialized).  
4. Состояния loading / 403 / 404 / ok.

Без канбана, drag-and-drop, подбора людей.

### 6.5. Документация

- `backend/README.md` — секция C4 + curl (handoff → entitlement → materialize → GET).  
- `frontend/README.md` — одна строка про блок Slots.

---

## 7. DoD

- [ ] Ветка **`feature/c4-staffing-slots`** от `main` с C2+C3.  
- [ ] Контракт `StaffingSlots.v1` + example + строка в `contracts/README.md`.  
- [ ] Миграция `room_function_slots`, POST materialize, GET list, 403/404.  
- [ ] Идемпотентность materialize.  
- [ ] React: список слотов + materialize при unlocked.  
- [ ] `pytest` зелёный + регрессия C1–C3.  
- [ ] PR с кратким «как проверить руками».

---

## 8. Вне скоупа / параллель

- Assign freelancer, matching, Talent roster  
- Keycloak RBAC  
- Strategy Accept (C5)

**Параллельно:** [C5 — Strategy Accept](261015%20-%20задание%20C5%20Strategy%20accept.md).

---

## 9. Промпт для стажёра + ИИ (копировать целиком)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c4-staffing-slots
База: origin/main ПОСЛЕ merge C2 + C3.
Этот тикет ПАРАЛЛЕЛЕН C5 (feature/c5-strategy-accept): не трогай StrategySnapshot schema под proposals/Accept.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Читай AGENTS.md, docs/ADR-002-wowlance-2.0-platform-room.md.
Задание: docs/261015 - задание C4 Staffing slots.md

Сделай C4:
1) contracts/wowlance/StaffingSlots.v1.yaml + examples/StaffingSlots.sale.json + contracts/README.md
2) таблица room_function_slots + Alembic migration
3) POST /api/v1/rooms/{room_id}/slots/materialize — из staffing_intent.slots; идемпотентно; 403 если locked; 404 если нет комнаты
4) GET /api/v1/rooms/{room_id}/slots — список; 403 если locked
5) pytest: unlock→2 seller seats; replay; locked 403; empty intent; регрессия C1–C3
6) React RoomPage: кнопка Materialize + список слотов при unlocked
7) backend/README.md curl-сценарий

Не делай matching, Talent, assign freelancer, Keycloak, StrategyPublished/Accept.
Сначала план 5–8 шагов, потом маленькие коммиты.
```

---

## 10. Ревьюеру

- Слоты не создаются при locked; нет обхода через handoff.  
- Идемпотентность по `(room_id, role_key, seat_index)`, не «DELETE ALL + insert».  
- Не тащит Talent и не пишет в чужие БД.  
- Параллельный merge с C5: оба роутера и оба UI-блока на месте.
