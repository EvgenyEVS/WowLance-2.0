# Задание: C25 — Earned в Room health

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-21 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c25-health-earnings` |
| **База** | актуальный `main` **после merge C21** (нужны C13 health + C16 earnings) |
| **Параллельность** | ✅ **можно параллельно с C19 · C22 · C23 · C24** |
| **Фаза** | C25 (агрегат начислений в снимке здоровья комнаты) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 1–2 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [C13](261017%20-%20задание%20C13%20Room%20health.md), [C16](261017%20-%20задание%20C16%20Earnings%20stub.md) |
| **Предыдущее** | [C13 Room health](261017%20-%20задание%20C13%20Room%20health.md) · [C16 Earnings](261017%20-%20задание%20C16%20Earnings%20stub.md) |
| **Параллель** | [C19](261019%20-%20задание%20C19%20CRM%20deal%20status.md) · [C22](261021%20-%20задание%20C22%20Slot%20rematerialize.md) · [C23](261021%20-%20задание%20C23%20Matching%20lite.md) · [C24](261021%20-%20задание%20C24%20TaskAccepted%20outbox.md) |

C16 оставил earned вне health («later»). C25 закрывает витрину Strategy.

---

## 1. Зачем

`GET …/health` отдаёт slots/tasks/leads, но не деньги комнаты. Фаундер-витрина в Strategy должна видеть **сколько начислено** по stub ledger.

Нужен срез: блок `earnings` в health snapshot (+ publish outbox payload тот же). Без Billing live и без reverse.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `domain/room_health.py`, schemas RoomHealth, RoomHealthPanel | Писать в `earnings_entries` / менять accept (C16/C24) |
| Read-only SUM/count из earnings | Leads deal fields (C19), staffing rematerialize/match |
| Обновить RoomHealth.v1.yaml | |

**С C24:** C24 пишет outbox TaskAccepted; C25 только читает earnings table — пересечений нет.  
**Alembic:** нет.

---

## 3. Не трогать / не делать

- Менять формулу `EARNINGS_TASK_AMOUNT`.  
- Reverse на reject.  
- Отдельный billing API.  
- Staffing / leads / chat.

---

## 4. Продуктовые правила

1. В snapshot добавить:

```yaml
earnings:
  total_amount: string   # decimal as string, e.g. "20.00"
  currency: string       # default USD / из settings
  entries_count: int
```

2. Нет earnings → `total_amount="0.00"`, `entries_count=0` (не 404).  
3. GET health и publish используют **один** builder (как сейчас).  
4. UI RoomHealthPanel: показать Earned total / count.  
5. Не фильтровать по freelancer в C25 (room-scoped total).

---

## 5. Контракт

Обновить `contracts/strategy/RoomHealth.v1.yaml` + example:

```yaml
earnings:
  required: [total_amount, currency, entries_count]
```

`contracts/README.md` — пометка C25.

---

## 6. Код

### 6.1. Domain

В `build_room_health`: query sum/count из `EarningsEntry` where room_id.

### 6.2. Тесты

1. Пустая комната → earnings zeros.  
2. Accept×2 с assignee → total `20.00`, count 2 (при default 10).  
3. Publish payload содержит earnings.  
4. Регрессия C13 counts slots/tasks/leads.

### 6.3. Frontend

RoomHealthPanel: строка Earned.

### 6.4. Docs

`backend/README.md` / `frontend/README.md` — C25.

---

## 7. DoD

- [ ] Ветка `feature/c25-health-earnings`.  
- [ ] earnings в GET/publish + UI + pytest + контракт.  
- [ ] Read-only; не трогает C19/C22–C24 зоны.  
- [ ] PR.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c25-health-earnings
База: origin/main после C21 (C13+C16).
Параллелен C19, C22–C24: не трогай leads, staffing, accept/outbox TaskAccepted.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261021 - задание C25 Health earnings.md

Сделай C25: блок earnings в RoomHealth (total/currency/count); UI; pytest; контракт.
Не делай reverse, Billing live, per-freelancer filter.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Один builder для GET и publish.  
- Нули без строк earnings.  
- Не зависит от влития C24.
