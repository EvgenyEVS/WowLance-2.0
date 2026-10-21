# Задание: C22 — Rematerialize слотов после Strategy Accept

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-21 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c22-slot-rematerialize` |
| **База** | актуальный `main` **после merge C21** (нужны C4 materialize + C5 Accept) |
| **Параллельность** | ✅ **можно параллельно с C19 · C23 · C24 · C25** (с **C23** — общий `staffing.py`, см. §2) |
| **Фаза** | C22 (пересборка seats под новый active `staffing_intent`) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md) |
| **Предыдущее** | [C4 Staffing](261015%20-%20задание%20C4%20Staffing%20slots.md) · [C5 Strategy accept](261015%20-%20задание%20C5%20Strategy%20accept.md) |
| **Параллель** | [C19](261019%20-%20задание%20C19%20CRM%20deal%20status.md) · [C23](261021%20-%20задание%20C23%20Matching%20lite.md) · [C24](261021%20-%20задание%20C24%20TaskAccepted%20outbox.md) · [C25](261021%20-%20задание%20C25%20Health%20earnings.md) |

Не ждать C19. Не трогать leads.

---

## 1. Зачем

После C5 Accept активный snapshot может сменить `staffing_intent`, а слоты C4 остаются от старого materialize. Долг задания C5: «пересборка — later».

Нужен срез: явный **`POST …/slots/rematerialize`** (или флаг на materialize) приводит seats в соответствие с **новым** intent: добавить недостающие `open`, лишние пустые — `cancelled` / удалить (зафиксируй одно); **filled** не сносить молча.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `domain/staffing.py`, `api/slots.py`, SlotsPanel кнопка | Leads / CRM deal (C19) |
| Дописать StaffingSlots.v1 | Matching shortlist logic C23 — только не ломать assign; вынести общий `_planned_seats` если оба правят файл |
| Вызов **не** из Accept автоматически (явный POST) — безопаснее | Earnings / TaskAccepted / health (C24/C25) |

**С C23:** C22 = rematerialize seats; C23 = `GET …/match` suggest. Разные endpoints; при конфликте в `staffing.py` — маленькие функции рядом.

**Alembic:** обычно без миграции (статусы `open|filled|cancelled` уже есть). Если нужен audit — `013_c22_*`. Dual с C19 `012` / C23 — merge на QA.

---

## 3. Не трогать / не делать

- Авто-rematerialize внутри `accept_proposal` (можно опциональный query later; **DoD = явный POST**).  
- Unassign всех filled «за компанию».  
- Live Talent / matching (C23).  
- Leads, chat, service-token.

---

## 4. Продуктовые правила

1. Только при `staffing_unlocked=true`; иначе **403**.  
2. Diff intent (active snapshot) vs текущие слоты комнаты:  
   - недостающие `(role_key, seat_index)` → создать `open`;  
   - лишние **open** → `cancelled` (**рекомендация**) или hard-delete — зафиксируй cancelled;  
   - **filled**, которых нет в новом intent → **не** трогать автоматически; вернуть в ответе `orphaned_filled: […]` (тимлид решит unassign/terminate вручную).  
3. Повтор rematerialize без изменений → `200` `status=already_synced`.  
4. Первый materialize (C4) поведение не ломать.  
5. Actor: `get_actor_sub` как на assign.

---

## 5. Контракт

Дописать `StaffingSlots.v1.yaml`:

```yaml
paths:
  rematerialize:
    method: POST
    path: /api/v1/rooms/{room_id}/slots/rematerialize

response_200:
  required: [room_id, status, slots]
  properties:
    status: rematerialized | already_synced
    slots: [...]
    orphaned_filled: [slot]  # optional list
```

`contracts/README.md` — правка.

---

## 6. Код

### 6.1. Domain

`rematerialize_slots(db, room_id)` рядом с `materialize_slots`; reuse `planned_seats_from_intent`.

### 6.2. Тесты

1. Materialize intent A → Accept snapshot с большим count → rematerialize → больше open seats.  
2. Уменьшение intent → лишние open становятся cancelled; filled orphaned в ответе.  
3. Locked → 403.  
4. Регрессия C4 materialize / C12 unassign.

### 6.3. Frontend

SlotsPanel: кнопка **Rematerialize** (если unlocked), показать orphaned hint.

### 6.4. Docs

`backend/README.md` — C22 curl.

---

## 7. DoD

- [ ] Ветка `feature/c22-slot-rematerialize`.  
- [ ] API + правила orphaned filled + UI + pytest + контракт.  
- [ ] Не трогает C19 leads.  
- [ ] PR.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c22-slot-rematerialize
База: origin/main после C21.
Параллелен C19 (не трогай leads), C23 matching (только rematerialize seats), C24–C25.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261021 - задание C22 Slot rematerialize.md

Сделай C22: POST rematerialize по active staffing_intent; open sync; filled не сносить; orphaned_filled в ответе; UI; pytest.
Не делай auto из Accept, matching, CRM.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Filled защищены.  
- Явный POST, не сюрприз на Accept.  
- Стык с C23 только staffing helpers.
