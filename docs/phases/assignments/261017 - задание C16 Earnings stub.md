# Задание: C16 — «Я заработал» stub (после accept)

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-17 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c16-earnings-stub` |
| **База** | актуальный `main` **после merge C10** (нужен accept → done) |
| **Параллельность** | ✅ **можно параллельно с C11–C15 · C17 · C18–C21** |
| **Фаза** | C16 (журнал начислений фрилансера, stub) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](../../canon/ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../../../AGENTS.md), [07-jira-roles-model](../../architecture/07-jira-roles-model.md) |
| **Предыдущее** | [C10 Quality Gate](261017%20-%20задание%20C10%20Quality%20Gate.md) |
| **Параллель** | [C11](261017%20-%20задание%20C11%20RoomCreated%20outbox.md) · [C12](261017%20-%20задание%20C12%20Slot%20unassign.md) · [C13](261017%20-%20задание%20C13%20Room%20health.md) · [C14](261017%20-%20задание%20C14%20Meet%20Jitsi%20stub.md) · [C15](261017%20-%20задание%20C15%20Task%20roster%20assignee.md) · [C17](261017%20-%20задание%20C17%20Member%20terminated.md) · [C18](261019%20-%20задание%20C18%20StaffingUnlocked%20outbox.md) · [C19](261019%20-%20задание%20C19%20CRM%20deal%20status.md) · [C20](261019%20-%20задание%20C20%20Room%20chat.md) · [C21](261019%20-%20задание%20C21%20Internal%20service%20token.md) |

По ролевой модели «я заработал» — **не из Jira**, а журнал WowLance / Billing. Здесь — локальный stub ledger.

---

## 1. Зачем

После accept задачи (C10) статус `done`, но фрилансер не видит начисление. Нужен тонкий срез: при **accept** создать запись earnings; отдать сумму по комнате / по `sub`.

Без живого Billing, выплат, налоговой, рейтингов Talent.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| Новая таблица `earnings_entries` (имя свободное), `domain/earnings.py`, API | Менять proof/reject/transitions QG кроме **хука после успешного accept** |
| Тонкий вызов из `accept_task` → `earnings.record_task_accepted(...)` | Ломать C15 assignee-валидацию (если параллельно — merge аккуратно в `tasks.py`) |
| UI блок «Earned» на RoomPage / кабинет | Staffing, handoff, meet, health counts (опционально later добавить earned в health — **не** в C16) |
| Outbox `ReportAccepted` / `TaskAccepted` **опционально** | Обязательный outbox в Talent — later; если пишешь — свой `event_type`, не RoomCreated |

**Стык с C15:** оба могут трогать `domain/tasks.py`. Правило: C16 только в `accept_task` после commit-ready изменения статуса; C15 не трогает accept. На QA — один merge-commit / rebase.

**Alembic:** `009_c16_*` или `010_*`. Dual head ожидаем.

---

## 3. Не трогать / не делать

- Stripe / Payment live / вывод денег.  
- Рейтинг в Talent, termination (C17).  
- Менять сумму стратегии / budget как SoT оплаты комнаты.  
- Начислять на `complete`/`submitted` — **только на accept→done**.  
- Reject не создаёт и не откатывает запись (нет reverse в C16; later).

---

## 4. Продуктовые правила

1. При первом успешном accept задачи с `assignee_sub`:  
   - insert earnings: `room_id`, `task_id`, `freelancer_sub=assignee_sub`, `amount` (Decimal), `currency` (default `USD` или `DEMO`), `source=task_accepted`.  
2. Если `assignee_sub` null → **не** создавать earnings (или начислять actor'у accept — **запрещено**; только assignee).  
3. Повторный accept той же задачи невозможен (уже done) — идемпотентность через уникальность `task_id` в earnings (**UNIQUE task_id**).  
4. `amount`: константа stub из settings `EARNINGS_TASK_AMOUNT` (например `10.00`) **или** фиксировано в коде + README; не считать из strategy в C16.  
5. API:  
   - `GET /api/v1/rooms/{room_id}/earnings` — список / сумма по комнате;  
   - `GET /api/v1/me/earnings` (или query `?freelancer_sub=`) — **рекомендация:** room-scoped list + `total` в ответе достаточно для демо.  
6. Auth: `/api/v1` guard; в тестах AUTH_DISABLED.

---

## 5. Контракт

Файл: `contracts/wowlance/RoomEarnings.v1.yaml`  
Пример: `contracts/wowlance/examples/RoomEarnings.sale.json`

```yaml
id: RoomEarnings
version: "1"
direction: WowLance internal / UI
channel: https

entry:
  required: [id, room_id, task_id, freelancer_sub, amount, currency, source, created_at]
  properties:
    amount: string   # decimal as string
    currency: string
    source: task_accepted

paths:
  list_room:
    method: GET
    path: /api/v1/rooms/{room_id}/earnings
response_200:
  required: [room_id, total_amount, currency, entries]
```

Опционально outbox:

```yaml
event_type: TaskAccepted
payload: { room_id, task_id, freelancer_sub, amount, currency }
```

`contracts/README.md` — строка.

---

## 6. Код

### 6.1. Данные

Таблица `earnings_entries`: id, room_id FK, task_id FK UNIQUE, freelancer_sub, amount Numeric, currency, source, created_at.

### 6.2. Domain / API

`record_for_accepted_task` вызывается из `accept_task` в одной транзакции с переходом в `done`.  
List endpoint в `api/earnings.py`.

### 6.3. Тесты

1. Accept с assignee → 1 earnings row, amount = stub.  
2. Accept без assignee → 0 rows, task всё равно done.  
3. List room → total и entries.  
4. Reject path не создаёт earnings.  
5. Регрессия QG suite зелёная.

### 6.4. Frontend

Блок **Earned** на RoomPage: total + последние N строк (sub, amount, task title optional).

### 6.5. Docs

`backend/README.md` — C16 + `EARNINGS_TASK_AMOUNT`.

---

## 7. DoD

- [ ] Ветка `feature/c16-earnings-stub`.  
- [ ] Таблица + хук на accept + GET + UI + pytest + контракт.  
- [ ] Не начисляет на submit; не трогает C11–C15/C17 чужие зоны сверх хука accept.  
- [ ] PR.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c16-earnings-stub
База: origin/main после C10.
Параллелен C11–C15 и C17: не трогай handoff, slots, health publish, meet, assignee-валидацию (кроме чтения assignee на accept), termination.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261017 - задание C16 Earnings stub.md

Сделай C16: earnings_entries, record on accept→done, GET room earnings, UI Earned, pytest, контракт.
Не делай Billing live, reverse на reject, рейтинги Talent.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Одна транзакция с accept; UNIQUE task_id.  
- Стык с C15: только чтение assignee_sub.  
- Outbox TaskAccepted опционален.
