# Задание: C24 — Outbox `TaskAccepted`

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-21 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c24-task-accepted-outbox` |
| **База** | актуальный `main` **после merge C21** (нужны C10 accept + C16 earnings hook) |
| **Параллельность** | ✅ **можно параллельно с C19 · C22 · C23 · C25** |
| **Фаза** | C24 (исходящее событие при accept задачи) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 1–2 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [05-integration-map](architecture/05-integration-map.md) |
| **Предыдущее** | [C10 Quality Gate](261017%20-%20задание%20C10%20Quality%20Gate.md) · [C16 Earnings](261017%20-%20задание%20C16%20Earnings%20stub.md) |
| **Параллель** | [C19](261019%20-%20задание%20C19%20CRM%20deal%20status.md) · [C22](261021%20-%20задание%20C22%20Slot%20rematerialize.md) · [C23](261021%20-%20задание%20C23%20Matching%20lite.md) · [C25](261021%20-%20задание%20C25%20Health%20earnings.md) |

В C16 outbox `TaskAccepted` был опционален — здесь делаем обязательным тонким срезом.

---

## 1. Зачем

По карте WowLance → Talent/шина: принятый отчёт / задача. Сейчас accept только меняет статус (+ earnings). Соседям нужен **`TaskAccepted`** в outbox (stub `sent`).

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| Хук в `accept_task` **рядом** с earnings (после статуса done) | Менять proof/reject/transitions QG |
| Контракт + outbox row | Rematerialize / matching / leads |
| | Ломать C25 health (C25 только читает; outbox type свой) |

**Стык с C16:** одна транзакция: status done + earnings row + outbox TaskAccepted.  
**Alembic:** нет.

---

## 3. Не трогать / не делать

- Outbox на complete/submitted.  
- Reverse на reject.  
- Live Talent HTTP.  
- Leads / staffing rematerialize.

---

## 4. Продуктовые правила

1. Только при успешном accept → `done`.  
2. `event_type=TaskAccepted`, `status=sent`, `sent_at=now`.  
3. `idempotency_key` = `str(task_id)` (или `task:{id}:TaskAccepted` — **рекомендация: `task:{id}:TaskAccepted`**, чтобы не конфликтовать с другими ключами).  
4. Payload минимум: `room_id`, `task_id`, `assignee_sub`, `reviewed_by_sub`, `proof_uri`, `accepted_at`; optional `amount`/`currency` если earnings создан.  
5. Accept без assignee → outbox всё равно (assignee_sub null); earnings по C16 может отсутствовать.  
6. Повторный accept невозможен (уже done) — идемпотентность через unique key.

---

## 5. Контракт

`contracts/talent/TaskAccepted.v1.yaml` + example.

```yaml
id: TaskAccepted
direction: WowLance -> Talent/platform
channel: outbox
payload:
  required: [room_id, task_id, reviewed_by_sub, accepted_at]
```

`contracts/README.md`.

---

## 6. Код

### 6.1. Domain

`_task_accepted_outbox(...)` в `domain/tasks.py` или `adapters/task_accepted.py`; вызов из `accept_task` до commit.

### 6.2. Тесты

1. Accept → 1 outbox TaskAccepted, payload.task_id совпадает.  
2. Reject → 0 TaskAccepted.  
3. Earnings + TaskAccepted в одной транзакции (оба есть после accept с assignee).  
4. Регрессия QG suite.

### 6.3. Frontend

Не обязателен.

### 6.4. Docs

`backend/README.md` — C24 + SQL.

---

## 7. DoD

- [ ] Ветка `feature/c24-task-accepted-outbox`.  
- [ ] Outbox на accept + контракт + pytest + README.  
- [ ] Не на complete; не трогает C19/C22/C23.  
- [ ] PR.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c24-task-accepted-outbox
База: origin/main после C21 (C10+C16).
Параллелен C19, C22–C23, C25: не трогай leads, staffing rematerialize/match, health агрегаты сверх чтения.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261021 - задание C24 TaskAccepted outbox.md

Сделай C24: outbox TaskAccepted в той же транзакции что accept→done; контракт; pytest; README.
Не делай outbox на submit, reverse reject, live Talent.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Рядом с earnings, одна commit.  
- Unique idempotency по task.  
- C25 может позже считать earned — не блокирует.
