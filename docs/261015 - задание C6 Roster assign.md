# Задание: C6 — Local Talent roster + assign slot

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-15 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c6-roster-assign` |
| **База** | актуальный `main` **после merge C4 + C5** |
| **Параллельность** | ✅ **можно делать параллельно с C7** (`feature/c7-room-tasks`) |
| **Фаза** | C6 (локальный roster + заполнение слота) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md) |
| **Предыдущее** | [C4 Staffing slots](261015%20-%20задание%20C4%20Staffing%20slots.md) |
| **Параллель** | [C7 Room tasks](261015%20-%20задание%20C7%20Room%20tasks.md) |

Если C4 ещё не в `main`: дождаться merge. Без `room_function_slots` и materialize C6 не начинать.

---

## 1. Зачем

После C4 слоты материализуются, но всегда `open` / `freelancer_sub=null`. По ADR фрилансеры приходят из Talent в **локальный roster**; matching — по своей БД, без live JOIN.

Нужен срез: stub upsert roster → назначить человека на **открытый** слот → слот `filled`. Поиск по рынку Talent, скоринг, Keycloak — **не** здесь.

---

## 2. Параллель с C7 — правила стыковки

| Можно | Нельзя |
|-------|--------|
| Новые файлы: `api/roster.py`, `domain/roster.py`, миграция `freelancer_roster` (имя уточнить) | Создавать таблицу `tasks` / task API (это C7) |
| Расширить **только** staffing: `POST …/slots/{slot_id}/assign` (+ при необходимости unassign) | Менять контракт/поведение C7 tasks |
| UI: список roster + кнопка Assign на `SlotsPanel` (или соседний блок) | Править task-трекер на `RoomPage` |
| Append в `main.py`, `models.py`, README | Редактировать те же строки C7 без согласования |

**Alembic:** свой revision `005_c6_…` от текущего head `main` (`004_merge_c4_c5_heads`). Если C7 тоже сделает `005_*` — при merge появится dual head → merge-миграция на стенде QA (как C4∥C5).

**Merge:** в `RoomPage` оставить и Slots/Roster (C6), и Tasks (C7).

C7 **не** обязан читать roster. Связь «задача → assignee из roster» — later; в C7 достаточно свободного `assignee_sub` string.

---

## 3. Не трогать / не делать

- Live Talent HTTP / чтение чужой БД.  
- Matching «подобрать лучшего», shortlist UI, видео/скиллы-каталог.  
- Задачи комнаты (C7).  
- Keycloak JWT / проверка роли teamlead по токену (достаточно `X-Actor-Sub` stub на assign).  
- Пересборка слотов после Strategy Accept.  
- Unassign обязателен только если останется время (иначе out of scope).  
- CRM, Jira, Outbox, биллинг.

---

## 4. Продуктовые правила

1. Чужие БД не читать; профиль фрилансера приходит в POST roster (stub Talent).  
2. Roster — **глобальный** для сервиса (по `freelancer_sub`), не per-room. Назначение — per-slot в комнате.  
3. Assign только если: комната существует, `staffing_unlocked=true`, слот `open`, `freelancer_sub` есть в roster.  
4. Иначе:  
   - нет комнаты / нет слота → **404**  
   - locked → **403** `staffing_locked`  
   - нет в roster → **404** или **409** `freelancer_not_in_roster` (зафиксировать одно в контракте; **рекомендация: 404**)  
   - слот уже `filled` → **409**  
5. Успешный assign: `freelancer_sub` на слоте, `status=filled`.  
6. Повтор assign того же `freelancer_sub` на тот же слот → **200** `already_assigned` (идемпотентность).  
7. Один `freelancer_sub` на **два** разных слота одной комнаты в C6 **запрещён** → **409** `already_seated` (упрощение демо).  
8. Upsert roster по `freelancer_sub` — идемпотентен (повтор → update display/skills snapshot, 200).

---

## 5. Контракт (C0 этого шага)

### 5.1. TalentRosterUpsert

Файл: `contracts/wowlance/TalentRosterUpsert.v1.yaml`  
Пример: `contracts/wowlance/examples/TalentRosterUpsert.json`

```yaml
id: TalentRosterUpsert
version: "1"
direction: Talent -> WowLance   # stub: client/curl
channel: https
path: /internal/v1/roster
method: POST
idempotency_key: freelancer_sub

request:
  required: [freelancer_sub, display_name]
  properties:
    freelancer_sub: string
    display_name: string
    skills: [string]           # optional snapshot
    level: string | null       # optional e.g. B
    source: stub | talent      # default stub

response_200:
  required: [freelancer_sub, status]
  properties:
    freelancer_sub: string
    status: upserted | already_exists   # already_exists = тот же payload; или всегда upserted
```

### 5.2. SlotAssign (дописать в StaffingSlots.v1 или отдельный файл)

```yaml
id: SlotAssign
path: /api/v1/rooms/{room_id}/slots/{slot_id}/assign
method: POST
headers:
  X-Actor-Sub: string   # stub teamlead

request:
  required: [freelancer_sub]
  properties:
    freelancer_sub: string

response_200:
  required: [slot]
  properties:
    slot: { … как StaffingSlots.slot, status: filled }
    status: assigned | already_assigned
```

Строки в `contracts/README.md`. Обновить example slots: один `filled` с `freelancer_sub`.

---

## 6. Что сделать в коде

### 6.1. Данные

Таблица `freelancer_roster` (или `roster_members`):

| Колонка | Тип |
|---------|-----|
| `freelancer_sub` | PK str |
| `display_name` | str |
| `skills` | JSONB nullable |
| `level` | str nullable |
| `source` | str |
| `updated_at` / `created_at` | timestamptz |

`room_function_slots.freelancer_sub` / `status` уже есть (C4) — использовать их, не плодить колонки без нужды.

Миграция `005_c6_freelancer_roster` (имя свободное) от `004_merge_c4_c5_heads`.

### 6.2. API

```http
POST /internal/v1/roster
GET  /api/v1/roster                    # список для UI assign (минимально: sub + display_name)
POST /api/v1/rooms/{room_id}/slots/{slot_id}/assign
```

`GET /roster` можно ограничить query `q=` later; в C6 — весь список или первые N.

Логика в `domain/roster.py` + расширение `domain/staffing.py` (assign).  
Internal roster — open; assign — `X-Actor-Sub` обязателен (**422** без него).

### 6.3. Тесты (pytest + PG)

1. Upsert roster → GET содержит запись.  
2. Handoff → entitlement → materialize → assign → слот `filled` + sub.  
3. Повтор assign того же → `already_assigned`.  
4. Assign без roster → 404.  
5. Assign при locked → 403.  
6. Assign на filled другим человеком → 409.  
7. Один freelancer на два слота → 409.  
8. Регрессия: C4 materialize / list без assign зелёные.

### 6.4. Frontend

1. Блок **Roster**: короткая форма upsert (sub + display name) **или** подсказка «создай через curl» + refresh списка — форма предпочтительна для демо.  
2. В `SlotsPanel`: для `open` слотов — выбор freelancer из roster + **Assign**.  
3. Для `filled` — показать `freelancer_sub` / display_name.  
4. Заголовок `X-Actor-Sub: teamlead-demo-sub` как в C5.

### 6.5. Документация

`backend/README.md` — C6 + curl: roster → materialize → assign.  
`frontend/README.md` — одна строка про Assign.

---

## 7. DoD

- [ ] Ветка **`feature/c6-roster-assign`** от `main` с C4+C5.  
- [ ] Контракты TalentRosterUpsert + SlotAssign; README contracts.  
- [ ] Миграция roster; POST roster; GET roster; POST assign; коды ошибок.  
- [ ] UI: roster + assign на open slots.  
- [ ] `pytest` зелёный + регрессия C4.  
- [ ] Не реализует tasks (C7).  
- [ ] PR с ручным сценарием.

---

## 8. Вне скоупа / параллель

- Room tasks (C7)  
- Matching / Talent live  
- Keycloak  

**Параллельно:** [C7 — Room tasks](261015%20-%20задание%20C7%20Room%20tasks.md).

---

## 9. Промпт для стажёра + ИИ (копировать целиком)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c6-roster-assign
База: origin/main ПОСЛЕ merge C4 + C5.
Этот тикет ПАРАЛЛЕЛЕН C7 (feature/c7-room-tasks): не создавай tasks-таблицы и не трогай task API/UI.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Читай AGENTS.md, docs/ADR-002-wowlance-2.0-platform-room.md.
Задание: docs/261015 - задание C6 Roster assign.md

Сделай C6:
1) contracts TalentRosterUpsert.v1 + SlotAssign (в StaffingSlots или отдельно) + examples + contracts/README
2) таблица freelancer_roster + Alembic 005_c6_* от 004_merge_c4_c5_heads
3) POST /internal/v1/roster, GET /api/v1/roster
4) POST /api/v1/rooms/{room_id}/slots/{slot_id}/assign + X-Actor-Sub:
   - unlocked + open + in roster → filled
   - locked 403; unknown 404; filled/conflict 409; idempotent already_assigned
   - один freelancer — один слот в комнате
5) pytest сценарии выше + регрессия materialize
6) React: roster upsert/list + Assign на open slots
7) backend/README.md curl

Не делай tasks, matching, Keycloak, live Talent.
Сначала план 5–8 шагов, потом маленькие коммиты.
```

---

## 10. Ревьюеру

- Нет live Talent / чужих БД.  
- Assign не обходит `staffing_unlocked`.  
- Не тронуты task-модели C7.  
- Alembic от `004_…`; при merge с C7 — dual head ожидаем.  
- Параллельный merge: оба UI-блока на `RoomPage`.
