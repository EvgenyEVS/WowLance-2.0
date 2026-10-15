# Задание: C7 — Минимальные задачи комнаты

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-15 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c7-room-tasks` |
| **База** | актуальный `main` **после merge C4 + C5** |
| **Параллельность** | ✅ **можно делать параллельно с C6** (`feature/c6-roster-assign`) |
| **Фаза** | C7 (простой трекер исполнения в комнате) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md) |
| **Предыдущее** | [C3 Room read](261010%20-%20задание%20C3%20Room%20read%20shell.md) |
| **Параллель** | [C6 Roster assign](261015%20-%20задание%20C6%20Roster%20assign.md) |

База — `main` с комнатой и GET room. Staffing/roster **не** блокер для старта C7.

---

## 1. Зачем

По ADR WowLance — место **исполнения**: задачи и контроль, не только снимок стратегии. После C3–C5 UI показывает стратегию/слоты/Accept, но **делать нечего**.

Нужен минимальный трекер комнаты: создать задачу → взять в работу → сдать. Без Jira, без полноценного Quality Gate (доказательства/рейтинг — later), без привязки к roster C6 (assignee — свободная строка `sub`).

---

## 2. Параллель с C6 — правила стыковки

| Можно | Нельзя |
|-------|--------|
| Новые файлы: `api/tasks.py`, `domain/tasks.py`, миграция `room_tasks`, `TasksPanel.tsx` | Трогать `room_function_slots`, materialize, roster, assign |
| Поле `assignee_sub: string \| null` **без** FK на roster | Требовать, что assignee есть в `freelancer_roster` |
| Блок Tasks на `RoomPage` | Править `SlotsPanel` / roster UI C6 |

**Alembic:** свой `005_c7_room_tasks` от `004_merge_c4_c5_heads`. Dual head с C6 при merge — норма; merge-миграция на QA-стенде.

**Merge:** `RoomPage` = PendingStrategy + Slots/Roster (C6) + Tasks (C7).

Не вызывать assign из task flow. Не блокировать создание задач флагом `staffing_unlocked` (тимлид может планировать до unlock; **рекомендация:** tasks доступны всегда после создания комнаты).

---

## 3. Не трогать / не делать

- Roster / assign / Talent (C6).  
- Jira, спринты как отдельная сущность, канбан-доска «как продукт».  
- Quality Gate: обязательные proof-файлы, рейтинги, reject с причиной (достаточно статусов).  
- Keycloak JWT (stub `X-Actor-Sub` на мутациях).  
- Уведомления, чат, CRM Hot.  
- Копировать Django 1.0 task UI as-is.

---

## 4. Продуктовые правила

1. Задачи принадлежат `room_id`. Чужие БД не читать.  
2. Статусы (минимальный набор):  
   - `todo` — создана  
   - `in_progress` — взята  
   - `done` — сдана  
3. Переходы:  
   - create → `todo`  
   - `todo` → `in_progress` (claim / start)  
   - `in_progress` → `done` (complete)  
   - иные переходы → **409**  
4. `assignee_sub` опционален при create; при start можно выставить из `X-Actor-Sub`, если пусто.  
5. Неизвестная комната / задача → **404**.  
6. Список задач комнаты — GET; без пагинации (лимит 100 ок).  
7. Удаление задач в C7 **не** обязательно (можно skip).  
8. Редактирование title после create — опционально; достаточно create + переходы статусов.

---

## 5. Контракт (C0 этого шага)

Файл: `contracts/wowlance/RoomTasks.v1.yaml`  
Пример: `contracts/wowlance/examples/RoomTasks.sale.json`

```yaml
id: RoomTasks
version: "1"
direction: client -> WowLance
channel: https

task:
  required: [id, room_id, title, status, created_at]
  properties:
    id: uuid
    room_id: uuid
    title: string
    status: todo | in_progress | done
    assignee_sub: string | null
    created_at: datetime
    updated_at: datetime

paths:
  list:
    method: GET
    path: /api/v1/rooms/{room_id}/tasks
  create:
    method: POST
    path: /api/v1/rooms/{room_id}/tasks
    headers: [X-Actor-Sub]
    request: { required: [title], properties: { title, assignee_sub? } }
  start:
    method: POST
    path: /api/v1/rooms/{room_id}/tasks/{task_id}/start
    headers: [X-Actor-Sub]
  complete:
    method: POST
    path: /api/v1/rooms/{room_id}/tasks/{task_id}/complete
    headers: [X-Actor-Sub]

errors:
  - { code: 404, when: "room or task missing" }
  - { code: 409, when: "illegal status transition" }
  - { code: 422, when: "validation or missing X-Actor-Sub on mutating routes" }
```

Строка в `contracts/README.md`. `RoomRead.v1` **не** обязан встраивать tasks (отдельный GET — проще параллель с C6).

---

## 6. Что сделать в коде

### 6.1. Данные

Таблица `room_tasks`:

| Колонка | Тип |
|---------|-----|
| `id` | UUID PK |
| `room_id` | UUID FK → rooms CASCADE, index |
| `title` | str |
| `status` | str (`todo` / `in_progress` / `done`) |
| `assignee_sub` | str nullable |
| `created_at` / `updated_at` | timestamptz |

Миграция `005_c7_room_tasks` от `004_merge_c4_c5_heads`.

### 6.2. API

```http
GET  /api/v1/rooms/{room_id}/tasks
POST /api/v1/rooms/{room_id}/tasks
POST /api/v1/rooms/{room_id}/tasks/{task_id}/start
POST /api/v1/rooms/{room_id}/tasks/{task_id}/complete
```

Мутации требуют `X-Actor-Sub`. Логика в `domain/tasks.py`, тонкий router.  
Auth: открытый API + README («JWT later»).

### 6.3. Тесты (pytest + PG)

1. Handoff → create task → list содержит `todo`.  
2. start → `in_progress`; complete → `done`.  
3. complete из `todo` → 409.  
4. start уже `done` → 409.  
5. Без `X-Actor-Sub` на POST → 422.  
6. Неизвестная комната → 404.  
7. Регрессия: C1 handoff / C3 GET room зелёные (не ломать staffing тесты чужими миграциями — своя таблица).

### 6.4. Frontend

`TasksPanel` на `RoomPage`:

1. Список: title, status, assignee.  
2. Форма: title + **Add**.  
3. Кнопки **Start** / **Complete** по допустимому статусу.  
4. `X-Actor-Sub: teamlead-demo-sub` (или freelancer-demo-sub — константа + комментарий).  
5. Не смешивать разметку со Slots/Roster.

### 6.5. Документация

`backend/README.md` — C7 + curl.  
`frontend/README.md` — блок Tasks.

---

## 7. DoD

- [ ] Ветка **`feature/c7-room-tasks`** от `main` с C4+C5.  
- [ ] Контракт `RoomTasks.v1` + example.  
- [ ] Миграция, CRUD-переходы, pytest.  
- [ ] React TasksPanel на комнате.  
- [ ] Не реализует roster/assign (C6).  
- [ ] PR с ручным сценарием.

---

## 8. Вне скоупа / параллель

- Roster / slot assign (C6)  
- Quality Gate / proof upload  
- Keycloak, Jira, спринты  

**Параллельно:** [C6 — Roster assign](261015%20-%20задание%20C6%20Roster%20assign.md).

---

## 9. Промпт для стажёра + ИИ (копировать целиком)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c7-room-tasks
База: origin/main ПОСЛЕ merge C4 + C5.
Этот тикет ПАРАЛЛЕЛЕН C6 (feature/c6-roster-assign): не трогай room_function_slots, roster, assign API/UI.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Читай AGENTS.md, docs/ADR-002-wowlance-2.0-platform-room.md.
Задание: docs/261015 - задание C7 Room tasks.md

Сделай C7:
1) contracts/wowlance/RoomTasks.v1.yaml + examples/RoomTasks.sale.json + contracts/README.md
2) таблица room_tasks + Alembic 005_c7_* от 004_merge_c4_c5_heads
3) GET/POST /api/v1/rooms/{room_id}/tasks; POST …/start; POST …/complete
   - статусы todo → in_progress → done; иначе 409
   - мутации требуют X-Actor-Sub (422 без него)
   - assignee_sub свободная строка, без проверки roster
4) pytest: create/list/start/complete; illegal transition 409; 404; регрессия handoff/GET
5) React TasksPanel на RoomPage (не ломая Slots/Pending блоки)
6) backend/README.md curl

Не делай roster, assign, matching, Keycloak, Jira, Quality Gate.
Сначала план 5–8 шагов, потом маленькие коммиты.
```

---

## 10. Ревьюеру

- Нет зависимости от C6 roster.  
- Нет записи в slots.  
- Переходы статусов жёсткие; нет «свободного UPDATE status».  
- Dual Alembic head с C6 при merge — ожидаемо.  
- `RoomPage`: Tasks рядом со слотами, без перетирания C6.
