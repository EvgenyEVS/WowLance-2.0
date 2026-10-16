# Задание: C9 — Hot lead → CRM stub

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-16 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c9-hot-lead-crm` |
| **База** | актуальный `main` **после merge C6 + C7** |
| **Параллельность** | ✅ **можно делать параллельно с C8** (`feature/c8-keycloak-jwt`) |
| **Фаза** | C9 (лид до Hot + исходящий stub в CRM) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md), [05-integration-map](architecture/05-integration-map.md) |
| **Предыдущее** | [C3 Room read](261010%20-%20задание%20C3%20Room%20read%20shell.md) · [C7 Room tasks](261015%20-%20задание%20C7%20Room%20tasks.md) |
| **Параллель** | [C8 Keycloak JWT](261016%20-%20задание%20C8%20Keycloak%20JWT.md) |

Комната и UI комнаты уже в `main`. Auth C8 **не** блокер: эндпоинты C9 под `/api/v1/...` могут временно опираться на `X-Actor-Sub` / `AUTH_DISABLED` как C5–C7; после merge C8 их подхватит JWT.

---

## 1. Зачем

По ADR в комнате идёт работа **до Hot**; горячий лид уходит в **CRM**, сделка там. Сейчас в WL нет сущности лида — только стратегия и задачи.

Нужен срез: создать лид в комнате → пометить Hot → зафиксировать исходящее событие/вызов **`HotLeadToCrm`** (stub: запись в outbox-таблицу + ответ с `crm_ref` fake). Живой CRM HTTP и биллинг лида — **не** здесь.

---

## 2. Параллель с C8 — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `api/leads.py`, `domain/leads.py`, `adapters/crm_stub.py`, миграции `room_leads` + `outbox_messages` | `app/auth/*`, Keycloak compose, login UI |
| Блок Leads на `RoomPage` | Менять JWT middleware / `AUTH_*` |
| Append `main.py`, `models.py`, README | Ломать allowlist internal ради auth |

**Alembic:** `007_c9_hot_leads` (или `007_c9_*`) от `006_merge_c6_c7_heads`. Dual head с C8 → merge на QA.

**Auth:** не требовать Bearer в C9. Если удобно — те же `X-Actor-Sub` на мутациях. После merge C8 роуты `/api/v1/rooms/.../leads` автоматически попадут под JWT.

Не вызывать Keycloak из CRM stub.

---

## 3. Не трогать / не делать

- Живой CRM / SRM API, OAuth к CRM.  
- Воронка сделки, счета лиду, менеджерский UI CRM.  
- Keycloak (C8).  
- Quality Gate / proof на задачах.  
- Matching Talent, unassign.  
- Шину/брокер (достаточно PG outbox + sync stub «отправили»).  
- Копировать Django Hot UI 1.0 as-is.

---

## 4. Продуктовые правила

1. Лид принадлежит `room_id`. Чужие БД не читать.  
2. Статусы лида (минимум):  
   - `open` — создан в комнате  
   - `hot` — передан (или готов к передаче)  
   - `handed_to_crm` — stub CRM принял / outbox записан  
3. Переходы:  
   - create → `open`  
   - `open` → mark hot → `hot` (или сразу create-as-hot — **не** надо; два шага яснее)  
   - `hot` → handoff to CRM → `handed_to_crm` + outbox row  
   - повтор handoff того же лида → **200** `already_handed` (идемпотентность)  
   - handoff из `open` → **409**  
4. Неизвестная комната / лид → **404**.  
5. Handoff пишет **локальный** outbox: `event_type=HotLeadToCrm`, payload по контракту, `status=sent` (stub сразу «sent»; retry/broker — later).  
6. В ответе handoff — `crm_ref` вида `crm-stub:<lead_id>` (не null).  
7. Список лидов комнаты — GET; лимит 100.

---

## 5. Контракт (C0 этого шага)

### 5.1. RoomLeads (client API)

Файл: `contracts/wowlance/RoomLeads.v1.yaml`  
Пример: `contracts/wowlance/examples/RoomLeads.sale.json`

```yaml
id: RoomLeads
version: "1"
paths:
  list:   GET  /api/v1/rooms/{room_id}/leads
  create: POST /api/v1/rooms/{room_id}/leads
  mark_hot: POST /api/v1/rooms/{room_id}/leads/{lead_id}/mark-hot
  handoff:  POST /api/v1/rooms/{room_id}/leads/{lead_id}/handoff-crm

lead:
  required: [id, room_id, title, status, created_at]
  properties:
    id: uuid
    room_id: uuid
    title: string
    contact_name: string | null
    contact_email: string | null
    notes: string | null
    status: open | hot | handed_to_crm
    crm_ref: string | null
    created_at / updated_at: datetime
```

### 5.2. HotLeadToCrm (outbound)

Файл: `contracts/wowlance/HotLeadToCrm.v1.yaml`  
Пример: `contracts/wowlance/examples/HotLeadToCrm.json`

```yaml
id: HotLeadToCrm
version: "1"
direction: WowLance -> CRM
channel: https_or_outbox   # C9: persist outbox; HTTP optional stub no-op
idempotency_key: lead_id

payload:
  required: [lead_id, room_id, title, handed_at]
  properties:
    lead_id: uuid
    room_id: uuid
    title: string
    contact_name / contact_email / notes: string | null
    founder_sub: string
    room_name: string
    handed_at: datetime
```

Строки в `contracts/README.md`.

---

## 6. Что сделать в коде

### 6.1. Данные

**`room_leads`:**

| Колонка | Тип |
|---------|-----|
| `id` | UUID PK |
| `room_id` | UUID FK CASCADE |
| `title` | str |
| `contact_name` / `contact_email` / `notes` | nullable |
| `status` | str |
| `crm_ref` | str nullable |
| `created_at` / `updated_at` | timestamptz |

**`outbox_messages`** (минимальный outbox сервиса):

| Колонка | Тип |
|---------|-----|
| `id` | UUID PK |
| `event_type` | str (`HotLeadToCrm`) |
| `idempotency_key` | str unique (например `lead_id`) |
| `payload` | JSONB |
| `status` | `pending` \| `sent` \| `failed` — C9: сразу `sent` |
| `created_at` / `sent_at` | timestamptz |

Миграция от `006_merge_c6_c7_heads`.

### 6.2. API

```http
GET  /api/v1/rooms/{room_id}/leads
POST /api/v1/rooms/{room_id}/leads
POST /api/v1/rooms/{room_id}/leads/{lead_id}/mark-hot
POST /api/v1/rooms/{room_id}/leads/{lead_id}/handoff-crm
```

Мутации: `X-Actor-Sub` обязателен (**422** без него), как C7 — пока нет C8.  
`domain/leads.py` + `adapters/crm_stub.py` (формирует payload, пишет outbox, возвращает `crm_ref`).

### 6.3. Тесты (pytest + PG)

1. Create → list `open`.  
2. mark-hot → `hot`.  
3. handoff-crm → `handed_to_crm` + `crm_ref` + строка outbox `HotLeadToCrm` / `sent`.  
4. Повтор handoff → `already_handed`, одна outbox-строка (unique idempotency).  
5. handoff из `open` → 409.  
6. 404 на чужой lead_id.  
7. Регрессия: handoff комнаты C1 / GET room.

### 6.4. Frontend

`LeadsPanel` на `RoomPage`:

1. Список: title, status, crm_ref.  
2. Форма create (title + optional contact).  
3. Кнопки **Mark hot** / **Hand off to CRM** по статусу.  
4. `X-Actor-Sub: teamlead-demo-sub` (или freelancer — константа).

Не ломать Roster / Slots / Tasks / PendingStrategy.

### 6.5. Документация

`backend/README.md` — C9 + curl.  
`frontend/README.md` — блок Leads.

---

## 7. DoD

- [ ] Ветка **`feature/c9-hot-lead-crm`** от `main` с C6+C7.  
- [ ] Контракты RoomLeads + HotLeadToCrm + examples.  
- [ ] Миграции leads + outbox; API; stub handoff.  
- [ ] Идемпотентность handoff / outbox key.  
- [ ] React LeadsPanel.  
- [ ] pytest зелёный + регрессия C1/C3.  
- [ ] Не внедряет Keycloak (C8).  
- [ ] PR с ручным сценарием.

---

## 8. Вне скоупа / параллель

- Keycloak JWT (C8)  
- Live CRM, broker consumer  
- Quality Gate, биллинг лида  

**Параллельно:** [C8 — Keycloak JWT](261016%20-%20задание%20C8%20Keycloak%20JWT.md).

---

## 9. Промпт для стажёра + ИИ (копировать целиком)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c9-hot-lead-crm
База: origin/main ПОСЛЕ merge C6 + C7.
Этот тикет ПАРАЛЛЕЛЕН C8 (feature/c8-keycloak-jwt): не трогай app/auth, Keycloak, AUTH_*, login UI.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Читай AGENTS.md, docs/ADR-002-wowlance-2.0-platform-room.md.
Задание: docs/261016 - задание C9 Hot lead CRM.md

Сделай C9:
1) contracts RoomLeads.v1 + HotLeadToCrm.v1 + examples + contracts/README.md
2) таблицы room_leads + outbox_messages; Alembic 007_c9_* от 006_merge_c6_c7_heads
3) GET/POST leads; POST mark-hot; POST handoff-crm
   - open → hot → handed_to_crm
   - handoff пишет outbox HotLeadToCrm (status sent), crm_ref stub
   - повтор handoff → already_handed; из open → 409
   - мутации: X-Actor-Sub (422 без)
4) pytest сценарии + регрессия handoff/GET room
5) React LeadsPanel на RoomPage (рядом с Tasks, не ломая C6 UI)
6) backend/README.md curl

Не делай live CRM, Keycloak, Quality Gate, broker.
Сначала план 5–8 шагов, потом маленькие коммиты.
```

---

## 10. Ревьюеру

- CRM не вызывается live; outbox локальный.  
- Идемпотентность по `lead_id`.  
- Нет правок auth/C8.  
- Dual Alembic с C8 ожидаем.  
- `RoomPage`: Leads не вытесняет Tasks/Slots.
