# Задание: C17 — MemberTerminated lite (расторжение / выход)

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-17 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c17-member-terminated` |
| **База** | актуальный `main` **после merge C10** (желательно C6 slots; C12 не обязателен) |
| **Параллельность** | ✅ **можно параллельно с C11 · C13–C16 · C18–C21**; с **C12** — осторожно (оба могут трогать слоты) |
| **Фаза** | C17 (фиксация расторжения участника + сигнал наружу stub) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md), [05-integration-map](architecture/05-integration-map.md) |
| **Предыдущее** | [C6 Roster assign](261015%20-%20задание%20C6%20Roster%20assign.md) · наследие 1.0 termination |
| **Параллель** | [C11](261017%20-%20задание%20C11%20RoomCreated%20outbox.md) · [C12](261017%20-%20задание%20C12%20Slot%20unassign.md) · [C13](261017%20-%20задание%20C13%20Room%20health.md) · [C14](261017%20-%20задание%20C14%20Meet%20Jitsi%20stub.md) · [C15](261017%20-%20задание%20C15%20Task%20roster%20assignee.md) · [C16](261017%20-%20задание%20C16%20Earnings%20stub.md) · [C18](261019%20-%20задание%20C18%20StaffingUnlocked%20outbox.md) · [C19](261019%20-%20задание%20C19%20CRM%20deal%20status.md) · [C20](261019%20-%20задание%20C20%20Room%20chat.md) · [C21](261019%20-%20задание%20C21%20Internal%20service%20token.md) |

По карте: WowLance → Talent: расторжение / MemberTerminated. Здесь — локальный журнал + unseat + outbox stub.

---

## 1. Зачем

В 1.0 было расторжение фрилансера. В 2.0 после assign человек «навечно» на слоте (пока нет C12 unassign). Нужен **продуктовый** акт: тимлид фиксирует **termination** с причиной → слот освобождается → событие в outbox для Talent.

Это не то же самое, что «просто Unassign» (C12): termination — юридически/кадровый сигнал с причиной и историей.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| Новые `room_terminations` (или `membership_events`), `domain/termination.py`, API | Переписывать C12 unassign API — **вызывать** общий helper «освободить слот» или дублировать clear sub **аккуратно** |
| Outbox `event_type=MemberTerminated` | Менять RoomCreated (C11), health publish logic (C13), meet, earnings хук, QG |
| UI: кнопка Terminate на filled-слоте | Matching, live Talent HTTP |

**Стык с C12:**  
- Если C12 уже в `main` — termination **внутри** вызывает тот же clear-slot, что unassign (общий `_open_slot`), плюс пишет журнал + outbox.  
- Если C12 ещё нет — termination сам делает `filled→open` + clear sub (как unassign) и документирует: C12 потом рефакторит в shared helper.  
- **Не** делать два разных смысла «снять со слота» без причины в разных таблицах без связи.

**Alembic:** `009_c17_*` / `010_*`. Dual head с C12 возможен — merge на QA.

---

## 3. Не трогать / не делать

- Live Talent API / бан в Keycloak.  
- Удаление user shadow / roster (roster остаётся).  
- Авто-terminate по SLA.  
- Earnings reverse (C16) — **не** откатывать начисления в C17.  
- Полный RBAC (кто «тимлид») — любой валидный актор + README later.  
- Каскадно закрывать tasks assignee — optional note only; **не** обязательно в C17.

---

## 4. Продуктовые правила

1. `POST /api/v1/rooms/{room_id}/members/{freelancer_sub}/terminate`  
   body: `{ reason: string (required, min_length=1), slot_id?: uuid }`.  
2. Участник считается «в комнате», если есть **filled** слот с этим `freelancer_sub` (в C17 нет отдельной membership-таблицы членства — слот = seat).  
3. Нет filled слота для sub → **404** `not_seated`.  
4. Успех (одна транзакция):  
   - слот(ы): если передан `slot_id` — только он; иначе **все** filled слоты этого sub в комнате (при C6 max 1 — достаточно одного);  
   - insert `room_terminations`;  
   - outbox `MemberTerminated`, `status=sent`, payload: room_id, freelancer_sub, reason, slot_ids, terminated_by_sub, terminated_at.  
5. Повтор terminate того же sub без нового seat → **409** `already_terminated` или снова 404 `not_seated` — **зафиксируй: 404 not_seated** (проще).  
6. История terminations доступна: `GET /api/v1/rooms/{room_id}/terminations`.

---

## 5. Контракт

Файл: `contracts/wowlance/MemberTerminated.v1.yaml`  
Пример: `contracts/wowlance/examples/MemberTerminated.sale.json`

```yaml
id: MemberTerminated
version: "1"
direction: WowLance -> Talent (stub outbox)
channel: outbox + https API

paths:
  terminate:
    method: POST
    path: /api/v1/rooms/{room_id}/members/{freelancer_sub}/terminate
    request:
      required: [reason]
      properties:
        reason: { type: string, minLength: 1 }
        slot_id: { type: string, format: uuid, nullable: true }
  list:
    method: GET
    path: /api/v1/rooms/{room_id}/terminations

outbox:
  event_type: MemberTerminated
  payload:
    required: [room_id, freelancer_sub, reason, terminated_by_sub, terminated_at, slot_ids]
```

`contracts/README.md` — строка.

---

## 6. Код

### 6.1. Данные

`room_terminations`: id, room_id, freelancer_sub, reason, terminated_by_sub, slot_ids JSONB/array, created_at.

### 6.2. Domain

`terminate_member(...)` → open slots + insert + outbox.  
Желательно `_clear_slot(slot)` рядом со staffing, чтобы C12 мог переиспользовать.

### 6.3. Тесты

1. Assign → terminate → слот open, 1 termination, 1 outbox MemberTerminated.  
2. Terminate без seat → 404.  
3. reason пустой → 422.  
4. List terminations отдаёт запись.  
5. Регрессия: assign/list slots; не ломает HotLead/RoomCreated event types.  
6. Если C12 в базе — unassign по-прежнему работает отдельно (без outbox MemberTerminated).

### 6.4. Frontend

На filled слоте: **Terminate** (prompt/reason) рядом с Unassign (если C12 есть).  
Unassign = без журнала/outbox; Terminate = с причиной.

### 6.5. Docs

`backend/README.md` — C17 curl + отличие от unassign.

---

## 7. DoD

- [ ] Ветка `feature/c17-member-terminated`.  
- [ ] Журнал + clear seat + outbox + GET + UI + pytest + контракт.  
- [ ] Явно задокументировано отличие от C12 unassign.  
- [ ] PR.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c17-member-terminated
База: origin/main после C10 (C6 assign).
Параллелен C11, C13–C16; с C12 — общий clear-slot helper, не ломай unassign.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261017 - задание C17 Member terminated.md

Сделай C17: terminate API, room_terminations, clear filled slot, outbox MemberTerminated, list, UI reason, pytest.
Не делай live Talent, RBAC, earnings reverse, удаление roster.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Termination ≠ unassign: есть reason + история + outbox.  
- Одна транзакция seat+journal+outbox.  
- Не конфликтует с RoomCreated / HotLead event_type.
