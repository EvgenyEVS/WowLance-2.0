# Задание: C18 — Outbox `StaffingUnlocked`

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-19 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c18-staffing-unlocked-outbox` |
| **База** | актуальный `main` **после merge C15** (нужны C2 entitlement + C9/C11 outbox) |
| **Параллельность** | ✅ **можно параллельно с C16 · C17 · C19 · C20 · C21** |
| **Фаза** | C18 (исходящее событие при unlock staffing) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 1–2 дня |
| **Канон** | [ADR-002](../../canon/ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../../../AGENTS.md), [05-integration-map](../../architecture/05-integration-map.md) |
| **Предыдущее** | [C2 Entitlement](261010%20-%20задание%20C2%20Entitlement%20unlock.md) · [C11 RoomCreated](261017%20-%20задание%20C11%20RoomCreated%20outbox.md) |
| **Параллель** | [C16](261017%20-%20задание%20C16%20Earnings%20stub.md) · [C17](261017%20-%20задание%20C17%20Member%20terminated.md) · [C19](261019%20-%20задание%20C19%20CRM%20deal%20status.md) · [C20](261019%20-%20задание%20C20%20Room%20chat.md) · [C21](261019%20-%20задание%20C21%20Internal%20service%20token.md) |

---

## 1. Зачем

Комната создаётся до оплаты (C1 → `RoomCreated`). Staffing открывается позже entitlement (C2). Соседям (Order / Strategy / шина) нужен сигнал **`StaffingUnlocked`**, симметричный RoomCreated.

Нужен срез: при **первом** успешном unlock (`staffing_unlocked` false→true) — строка outbox `StaffingUnlocked` / `sent`. Повтор того же entitlement (идемпотентный grant) — **не** дублировать. Без брокера.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `domain/entitlement.py`, adapter payload, контракт | Хуки earnings / `accept_task` (C16) |
| Reuse `outbox_messages` | Clear-slot / terminate (C17) |
| README SQL/curl | Chat, CRM webhook, service-token middleware (C19–C21) — только не ломать |

**Alembic:** обычно **без** миграции. Dual head с C16/C17 → merge на QA.

**Auth:** endpoint entitlement остаётся `/internal/v1` (C21 может позже закрыть service-token — не блокировать C18).

---

## 3. Не трогать / не делать

- Живой брокер / HTTP к Order.  
- Писать outbox на каждом replay entitlement, если unlock уже был.  
- Earnings, termination, chat, leads CRM inbound.  
- Менять правила C2 404/409 entitlement.

---

## 4. Продуктовые правила

1. Outbox только когда комната **впервые** получает `staffing_unlocked=true` в этом запросе.  
2. Идемпотентный повтор entitlement на уже unlocked комнате → **без** новой строки `StaffingUnlocked`.  
3. `event_type = StaffingUnlocked`, `status = sent`, `sent_at = now`.  
4. `idempotency_key` = `str(room_id)` **или** `room:{id}:StaffingUnlocked` — **зафиксируй одно; рекомендация: `str(room_id)` + уникальность по (event_type, key) если индекс есть, иначе проверка count перед insert**.  
5. Payload минимум: `room_id`, `entitlement_id`, `founder_sub` (если есть), `unlocked_at`, `staffing_unlocked: true`.  
6. Одна транзакция с grant (как RoomCreated с create).

---

## 5. Контракт

Файл: `contracts/order/StaffingUnlocked.v1.yaml`  
Пример: `contracts/order/examples/StaffingUnlocked.sale.json`

```yaml
id: StaffingUnlocked
version: "1"
direction: WowLance -> platform (Order/Strategy/bus)
channel: outbox
idempotency_key: room_id

payload:
  required: [room_id, entitlement_id, unlocked_at, staffing_unlocked]
  properties:
    room_id / entitlement_id: uuid
    staffing_unlocked: true
    unlocked_at: datetime
    founder_sub: string | null
```

Строка в `contracts/README.md`.

---

## 6. Код

### 6.1. Domain

В `grant_entitlement`: после перехода locked→unlocked — `db.add(OutboxMessage(...))` до `commit`.

### 6.2. Тесты

1. Handoff → entitlement → 1 row `StaffingUnlocked`.  
2. Повтор entitlement → всё ещё 1 row.  
3. Регрессия: RoomCreated на create по-прежнему 1; HotLead не ломается.  
4. 404/409 entitlement зелёные.

### 6.3. Frontend

Не обязателен.

### 6.4. Docs

`backend/README.md` — C18 + SQL example.

---

## 7. DoD

- [ ] Ветка `feature/c18-staffing-unlocked-outbox`.  
- [ ] Контракт + outbox на первом unlock + pytest + README.  
- [ ] Не дублирует на replay; атомарно с grant.  
- [ ] Не трогает C16/C17/C19–C21 зоны.  
- [ ] PR.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c18-staffing-unlocked-outbox
База: origin/main после C15.
Параллелен C16–C17 и C19–C21: не трогай earnings, terminate, leads webhook, chat, service-token.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261019 - задание C18 StaffingUnlocked outbox.md

Сделай C18: контракт StaffingUnlocked; при первом unlock — outbox sent; replay без дубля; pytest; README.
Не делай broker, matching, RBAC.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Только первый unlock.  
- Reuse outbox C9/C11.  
- Параллель с C16/C17 чистая.
