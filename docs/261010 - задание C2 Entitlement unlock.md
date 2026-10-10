# Задание: C2 — Entitlement → staffing unlocked

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-10 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c2-entitlement-unlock` |
| **База** | актуальный `main` **после merge** [`feature/c1-founder-handoff`](https://github.com/EvgenyEVS/WowLance-2.0/tree/feature/c1-founder-handoff) |
| **Фаза** | C2 (продолжает C1) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 1–2 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md) |
| **Предыдущее** | [C1 FounderHandoff](261010%20-%20задание%20C1%20FounderHandoff.md) |

Если C1 ещё не в `main`: сначала merge C1, затем ветка от `main`. Не начинать C2 от голого скелета без handoff.

---

## 1. Зачем

После C1 комната создаётся, но `staffing_unlocked=false` всегда. По ADR и integration-map: **handoff до оплаты допустим, staffing — только после entitlement**. Этот тикет замыкает правило: событие/вызов от Order/Payments (stub) открывает staffing-флаг на комнате.

Реальный staffing (слоты, roster, matching) и React — **не** здесь.

---

## 2. Не трогать / не делать

- Matching, слоты `RoomFunctionSlot`, добавление фрилансеров, Talent API.  
- Keycloak, CRM, Jira, скачивание SOP из S3.  
- Outbox `RoomCreated` / брокер (достаточно sync POST как у handoff).  
- React UI (можно не открывать `frontend/`).  
- Ломать идемпотентность и контракт C1 `FounderHandoff.v1` без причины.  
- Копировать Django 1.0.

---

## 3. Продуктовые правила

1. Чужие БД не читать; payload entitlement приходит в POST.  
2. Разрешено разблокировать только **существующую** комнату (`room_id`).  
3. Повтор с тем же `entitlement_id` — идемпотентен (флаг уже true → 200, без ошибки).  
4. Неизвестный `room_id` → **404**.  
5. Handoff по-прежнему создаёт комнаты с `staffing_unlocked=false`.  
6. Откат «заблокировать снова» в C2 **не** нужен (нет revoke).

---

## 4. Контракт (создать в тикете — C0 этого шага)

Файл: `contracts/wowlance/EntitlementGranted.v1.yaml`  
Пример: `contracts/wowlance/examples/EntitlementGranted.json`

Черновик (можно уточнить имена полей, смысл сохранить):

```yaml
id: EntitlementGranted
version: "1"
direction: Order/Payments -> WowLance
channel: https
path: /internal/v1/entitlements
method: POST
idempotency_key: entitlement_id

request:
  required: [entitlement_id, room_id]
  properties:
    entitlement_id: { type: string, format: uuid }
    room_id: { type: string, format: uuid }
    order_id: { type: string, format: uuid }       # optional
    source: { type: string, enum: [order, payments, stub], default: stub }

response_200:
  required: [room_id, staffing_unlocked, status]
  properties:
    room_id: uuid
    staffing_unlocked: true
    status: granted | already_granted
```

Обновить `contracts/README.md` — строка про новый контракт.

---

## 5. Что сделать в коде

### 5.1. Данные

- На `Room` уже есть `staffing_unlocked`.  
- Добавить учёт идемпотентности entitlement, например:
  - таблица `entitlements` (`entitlement_id` PK/unique, `room_id`, `source`, `created_at`), **или**
  - поле `entitlement_id` unique nullable на `Room` (хуже, если позже несколько дозаказов — предпочтительна отдельная таблица).  
- Alembic-миграция от головы после C1.

### 5.2. API

```http
POST /internal/v1/entitlements
Content-Type: application/json
```

| Код | Когда |
|-----|--------|
| **200** | первый grant → `status: granted`, `staffing_unlocked: true` |
| **200** | повтор того же `entitlement_id` → `status: already_granted` |
| **404** | `room_id` нет |
| **409** | тот же `entitlement_id` уже привязан к **другой** `room_id` |
| **422** | валидация |

Логика в `domain/`, тонкий router. Auth: как в C1 — internal open + пометка в README.

### 5.3. Совместимость с handoff

Тест: handoff → room с `false` → entitlement → `true`.  
Повторный handoff того же JSON **не** должен сбрасывать `staffing_unlocked` в `false`.

### 5.4. Тесты (pytest + PG)

1. Grant после handoff → `staffing_unlocked is True`.  
2. Повтор того же `entitlement_id` → `already_granted`, одна строка entitlement.  
3. Неизвестный `room_id` → 404.  
4. Тот же `entitlement_id`, другой `room_id` → 409.  
5. Регрессия: C1 handoff example по-прежнему `created` / `staffing_unlocked false` до grant.

### 5.5. Документация

В `backend/README.md`: секция C2 + пример `curl` для entitlements (после create room подставить `room_id`).

---

## 6. DoD

- [ ] Ветка **`feature/c2-entitlement-unlock`** от `main` с влитым C1.  
- [ ] Контракт YAML + example в `contracts/`.  
- [ ] Миграция, `POST /internal/v1/entitlements`, идемпотентность / 404 / 409.  
- [ ] Handoff не затирает unlocked.  
- [ ] `pytest` зелёный.  
- [ ] PR с кратким «как проверить руками».

---

## 7. Вне скоупа / параллель

- Реальный staffing / roster Talent  
- Keycloak  
- Webhook от живого Billing  

**Параллельно с этим тикетом** можно вести  
[C3 — GET room + React room shell](261010%20-%20задание%20C3%20Room%20read%20shell.md)  
(`feature/c3-room-read-shell`) — только чтение `staffing_unlocked`, без POST entitlements.

---

## 8. Промпт для стажёра + ИИ (копировать целиком)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c2-entitlement-unlock
База: origin/main ПОСЛЕ merge feature/c1-founder-handoff (если C1 ещё не в main — сначала дождаться merge или временно от C1 и перебазировать).
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Читай AGENTS.md, docs/ADR-002-wowlance-2.0-platform-room.md.
Задание: docs/261010 - задание C2 Entitlement unlock.md

Сделай C2:
1) contracts/wowlance/EntitlementGranted.v1.yaml + examples/EntitlementGranted.json + строка в contracts/README.md
2) таблица entitlements (или эквивалент) + Alembic migration
3) POST /internal/v1/entitlements:
   - room exists → staffing_unlocked=true
   - same entitlement_id → already_granted
   - unknown room_id → 404
   - entitlement_id bound to other room → 409
4) handoff не сбрасывает unlocked при повторном POST
5) pytest на сценарии выше + регрессия C1
6) обновить backend/README.md (curl)

Не делай staffing/matching, React, Keycloak, CRM, Jira. Не читай чужие БД.
Сначала план 5–8 шагов, потом маленькие коммиты.
```

---

## 9. Ревьюеру

- Контракт лежит в `contracts/` до или вместе с кодом, не «только в голове».  
- Идемпотентность по `entitlement_id`, не «просто UPDATE rooms SET true».  
- Повторный FounderHandoff не обнуляет флаг.  
- Нет revoke/billing UI.
