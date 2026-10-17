# Задание: C15 — Task assignee из roster

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-17 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c15-task-roster-assignee` |
| **База** | актуальный `main` **после merge C10** (нужны C6 roster + C7/C10 tasks) |
| **Параллельность** | ✅ **можно параллельно с C11 · C12 · C13 · C14 · C16 · C17** |
| **Фаза** | C15 (привязка исполнителя задачи к локальному roster) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 1–2 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md) |
| **Предыдущее** | [C6 Roster](261015%20-%20задание%20C6%20Roster%20assign.md) · [C7 Tasks](261015%20-%20задание%20C7%20Room%20tasks.md) · [C10 QG](261017%20-%20задание%20C10%20Quality%20Gate.md) |
| **Параллель** | [C11](261017%20-%20задание%20C11%20RoomCreated%20outbox.md) · [C12](261017%20-%20задание%20C12%20Slot%20unassign.md) · [C13](261017%20-%20задание%20C13%20Room%20health.md) · [C14](261017%20-%20задание%20C14%20Meet%20Jitsi%20stub.md) · [C16](261017%20-%20задание%20C16%20Earnings%20stub.md) · [C17](261017%20-%20задание%20C17%20Member%20terminated.md) |

C6 и C10 должны быть в базе. C12 (unassign) не блокер: C15 читает roster, не слоты.

---

## 1. Зачем

Сейчас `assignee_sub` на задаче — свободная строка (C7). По ADR matching/состав опираются на **локальный roster**; исполнитель задачи должен быть известным фрилансером (или явно «не назначен»).

Нужен срез: при create/start с `assignee_sub` — проверка наличия в roster; UI выбирает из roster. Без слотов, matching и RBAC.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `domain/tasks.py`, `api/tasks.py`, TasksPanel (выбор assignee) | Менять complete/accept/reject/proof правила QG (C10) — только валидация assignee |
| Read `freelancer_roster` | Менять assign/unassign слотов (C12) |
| Дописать RoomTasks.v1 | Писать health counts (C13 только читает статусы — OK) |
| | Handoff/meet/earnings/termination |

**Alembic:** обычно без миграции. Dual head маловероятен, если нет новых колонок.

**Важно для C16:** accept→done не менять по смыслу; earnings повесится на accept отдельно.

---

## 3. Не трогать / не делать

- Требовать, чтобы assignee сидел на **слоте** (seat) — later.  
- Matching / auto-pick.  
- Ломать create без assignee (по-прежнему optional).  
- Quality Gate proof/accept/reject.  
- Unassign слотов, Meet, earnings, termination.

---

## 4. Продуктовые правила

1. `assignee_sub` optional на create; если передан и **не** в roster → **404** `freelancer_not_in_roster` (как C6).  
2. `start` без assignee: как сейчас — подставить `actor_sub`; если actor **не** в roster → **404** (или **409** `actor_not_in_roster` — **зафиксируй: 404**).  
3. `start` / явный set assignee на уже заданный другой sub:  
   - **рекомендация C15:** добавить `PATCH …/tasks/{id}` или `POST …/assign` с `{ assignee_sub }` только для `todo` \| `in_progress`; не из `submitted`/`done` → **409**.  
4. Пустой assignee на create/list — OK.  
5. Complete/accept/reject — без новых правил assignee (C10 as-is).  
6. Исторические задачи с «левым» sub не мигрировать; новые мутации валидируют.

---

## 5. Контракт

Дописать `contracts/wowlance/RoomTasks.v1.yaml`:

```yaml
# create / assign
assignee_sub: string | null  # must exist in roster when non-null

paths:
  assign:   # или PATCH task
    method: POST
    path: /api/v1/rooms/{room_id}/tasks/{task_id}/assign
    request: { required: [assignee_sub], properties: { assignee_sub: string } }
```

Ошибки: 404 `freelancer_not_in_roster`; 409 illegal status.

`contracts/README.md` — правка строки RoomTasks.

---

## 6. Код

### 6.1. Domain

В `domain/tasks.py`: хелпер `_require_roster(db, sub)`.  
Create / start / assign вызывают его при non-null sub.

### 6.2. API

Существующие create/start + новый assign (или PATCH).  
Не менять сигнатуры complete/accept/reject.

### 6.3. Тесты

1. Create с roster sub → OK; без roster → 404.  
2. Start: actor в roster → assignee заполнен; actor нет → 404.  
3. Assign на todo → OK; на submitted → 409.  
4. Регрессия QG: complete/accept/reject зелёные.  
5. Регрессия C6 roster upsert / slot assign не ломаются.

### 6.4. Frontend

TasksPanel: select assignee из `GET /api/v1/roster` (уже есть с C6); не free-text.

### 6.5. Docs

`backend/README.md` / `frontend/README.md` — assignee из roster.

---

## 7. DoD

- [ ] Ветка `feature/c15-task-roster-assignee`.  
- [ ] Валидация roster + UI select + pytest.  
- [ ] QG переходы не изменены.  
- [ ] PR с сценарием.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c15-task-roster-assignee
База: origin/main после C10 (C6 roster + tasks).
Параллелен C11–C14, C16–C17: не трогай handoff, slots unassign, health, meet, earnings, termination; не меняй proof/accept/reject.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261017 - задание C15 Task roster assignee.md

Сделай C15: assignee_sub только из roster; create/start/assign; TasksPanel select; pytest; контракт.
Не делай seat-check по слотам, matching, RBAC.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- QG не регрессирует.  
- Не требует filled slot.  
- C13 health по статусам не ломается.
