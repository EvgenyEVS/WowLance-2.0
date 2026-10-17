# Задание: C10 — Quality Gate lite (task proof)

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-17 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c10-quality-gate` |
| **База** | актуальный `main` **после merge C8 + C9** |
| **Параллельность** | ✅ **можно делать параллельно с C11** (`feature/c11-room-created-outbox`) |
| **Фаза** | C10 (минимальный Quality Gate на сдаче задачи) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md) |
| **Предыдущее** | [C7 Room tasks](261015%20-%20задание%20C7%20Room%20tasks.md) |
| **Параллель** | [C11 RoomCreated outbox](261017%20-%20задание%20C11%20RoomCreated%20outbox.md) |

Без C7 tasks в `main` не начинать. C8/C9 желательны в базе (JWT + привычный RoomPage); если C8/C9 ещё не влиты — ветка от `main`+C7, но мержить после C8/C9.

---

## 1. Зачем

По ADR и наследию 1.0 сдача работы идёт через **Quality Gate** (доказательство). Сейчас C7: `complete` без proof — задача сразу `done`.

Нужен тонкий срез: при complete обязателен **proof** (URI + короткий note); тимлид может **accept** / **reject** сдачи. Без object storage upload, рейтингов и выплат.

---

## 2. Параллель с C11 — правила стыковки

| Можно | Нельзя |
|-------|--------|
| Расширять `room_tasks`, `domain/tasks.py`, `TasksPanel` | Писать `RoomCreated` / трогать handoff create outbox |
| Новые статусы / поля proof на задаче | Менять `outbox_messages` схему под C11 без нужды |
| Append README / RoomRead опционально | Править `domain/handoff.py` ради outbox |

**Alembic:** `008_c10_quality_gate` от head после C8+C9 (ожидай `007_c9_*` или merge). Dual head с C11 `008_c11_*` → merge-миграция на QA.

**Auth:** мутации под существующим `/api/v1` guard (C8). В тестах `AUTH_DISABLED=true`.

---

## 3. Не трогать / не делать

- Загрузка файлов в S3 (только URI строкой, как documents в handoff).  
- Рейтинги, «я заработал», начисления.  
- RoomCreated outbox (C11).  
- Jira, чат, спринты.  
- Ломать create/start без proof.

---

## 4. Продуктовые правила

1. Статусы задачи (расширение C7):  
   - `todo` → `in_progress` (start) — без изменений  
   - `in_progress` → `submitted` (**complete** с proof)  
   - `submitted` → `done` (**accept** тимлидом)  
   - `submitted` → `in_progress` (**reject** + optional reason; proof сохраняется или очищается — зафиксируй: **сохранять**)  
2. `POST …/complete` **без** `proof_uri` → **422**.  
3. Старый путь `in_progress` → `done` напрямую — **запрещён** (409).  
4. Accept/Reject не-`submitted` → **409**.  
5. `proof_uri` — непустая строка (uri); `proof_note` — optional string.  
6. Кто accept/reject: `get_actor_sub` / JWT (как C7); отдельной роли teamlead в C10 **нет** (любой валидный актор; README: RBAC later).

---

## 5. Контракт

Обновить `contracts/wowlance/RoomTasks.v1.yaml` (+ example):

```yaml
task.status: todo | in_progress | submitted | done
task.proof_uri: string | null
task.proof_note: string | null
task.reviewed_by_sub: string | null
task.review_note: string | null   # reject reason

paths:
  complete:  POST .../tasks/{id}/complete
    body: { required: [proof_uri], proof_note? }
  accept:    POST .../tasks/{id}/accept
  reject:    POST .../tasks/{id}/reject
    body: { review_note? }
```

Строка в `contracts/README.md` при изменении.

---

## 6. Код

### 6.1. Данные

На `room_tasks` добавить nullable: `proof_uri`, `proof_note`, `reviewed_by_sub`, `review_note`.  
Миграция Alembic. Существующие `done` строки оставить как есть (исторические).

### 6.2. API

```http
POST /api/v1/rooms/{room_id}/tasks/{task_id}/complete   # → submitted
POST /api/v1/rooms/{room_id}/tasks/{task_id}/accept     # → done
POST /api/v1/rooms/{room_id}/tasks/{task_id}/reject     # → in_progress
```

### 6.3. Тесты

1. start → complete с proof → `submitted` + поля proof.  
2. complete без proof → 422.  
3. accept → `done` + `reviewed_by_sub`.  
4. reject → `in_progress`, можно complete снова.  
5. accept из `in_progress` → 409.  
6. Регрессия: create/start; list отдаёт новые поля.

### 6.4. Frontend

`TasksPanel`:  
- Complete → поля proof URI (+ note) → Submit.  
- Для `submitted`: кнопки **Accept** / **Reject**.  
- Показать proof на карточке.

### 6.5. Docs

`backend/README.md` — C10 + curl.  
`frontend/README.md` — Quality Gate кнопки.

---

## 7. DoD

- [ ] Ветка `feature/c10-quality-gate` от main после C8+C9.  
- [ ] Контракт обновлён; миграция; API; UI; pytest.  
- [ ] Нет прямого complete→done.  
- [ ] Не трогает RoomCreated / handoff outbox (C11).  
- [ ] PR с ручным сценарием.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c10-quality-gate
База: origin/main ПОСЛЕ merge C8 + C9.
Параллелен C11 (feature/c11-room-created-outbox): не трогай handoff/outbox RoomCreated.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261017 - задание C10 Quality Gate.md

Сделай C10:
1) расширь RoomTasks.v1: submitted/done + proof_*; complete/accept/reject
2) миграция полей на room_tasks
3) complete требует proof_uri → submitted; accept → done; reject → in_progress
4) pytest + TasksPanel UI
5) README curl

Не делай S3 upload, рейтинги, RoomCreated outbox.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Breaking change complete→done осознан и покрыт тестами.  
- Параллель с C11: нет правок handoff.  
- Dual Alembic 008 ожидаем.
