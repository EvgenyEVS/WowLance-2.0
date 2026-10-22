# Задание: C19 — CRM deal-status inbound stub

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-19 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c19-crm-deal-status` |
| **База** | актуальный `main` **после merge C15** (нужен C9 leads) |
| **Параллельность** | ✅ **можно параллельно с C16 · C17 · C18 · C20 · C21** |
| **Фаза** | C19 (обратный сигнал CRM → статус сделки на лиде) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md), [05-integration-map](architecture/05-integration-map.md) |
| **Предыдущее** | [C9 Hot lead CRM](261016%20-%20задание%20C9%20Hot%20lead%20CRM.md) |
| **Параллель** | [C16](261017%20-%20задание%20C16%20Earnings%20stub.md) · [C17](261017%20-%20задание%20C17%20Member%20terminated.md) · [C18](261019%20-%20задание%20C18%20StaffingUnlocked%20outbox.md) · [C20](261019%20-%20задание%20C20%20Room%20chat.md) · [C21](261019%20-%20задание%20C21%20Internal%20service%20token.md) |

---

## 1. Зачем

C9 отдаёт Hot в CRM (outbox stub). По карте SRM шлёт обратно стадию сделки. В комнате лид «застывает» в `handed_to_crm`.

Нужен срез: internal webhook **обновляет** у лида CRM-стадию / outcome (stub enum) + показывает в UI. Без live CRM OAuth и без биллинга лида.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `domain/leads.py`, `api/leads` или `api/crm_webhooks.py`, поля на `room_leads` | Менять Hot handoff outbox semantics C9 (кроме чтения `crm_ref`) |
| Миграция nullable колонок deal_* | Earnings accept (C16), terminate (C17), StaffingUnlocked (C18) |
| LeadsPanel: показать deal status | Chat / service-token |

**Alembic:** `010_c19_*` / `011_*` — колонки на `room_leads`. Dual head с C16/C17 ожидаем.

---

## 3. Не трогать / не делать

- Live CRM HTTP / OAuth.  
- Создавать Deal-модель «как продукт CRM» в WL.  
- Менять open→hot→handed_to_crm happy-path C9.  
- Earnings / termination / chat / entitlement outbox.

---

## 4. Продуктовые правила

1. Новый endpoint (рекомендация):

```http
POST /internal/v1/crm/deal-status
```

   Body: `{ "crm_ref": "crm-stub:…", "deal_status": "won"|"lost"|"in_progress"|"unknown", "amount"?: number|null, "currency"?: string|null }`.  
   Альтернатива: path по `lead_id` — хуже для stub CRM; **предпочитай crm_ref**.

2. Лид находится по `crm_ref`; нет → **404**.  
3. Лид не в `handed_to_crm` → **409** `lead_not_handed` (или разрешить только handed — зафиксируй 409).  
4. Успех: сохранить `deal_status`, optional `deal_amount` / `deal_currency`, `deal_updated_at`; ответ 200 с lead.  
5. Повтор с тем же статусом → 200 идемпотентно.  
6. Исходящий outbox **не** обязателен в C19 (это inbound).  
7. List/GET leads отдают новые поля.

---

## 5. Контракт

Файл: `contracts/crm/CrmDealStatus.v1.yaml` (+ дописать RoomLeads example)

```yaml
id: CrmDealStatus
version: "1"
direction: CRM/SRM -> WowLance
channel: https
path: /internal/v1/crm/deal-status
method: POST

request:
  required: [crm_ref, deal_status]
  properties:
    crm_ref: string
    deal_status: won | lost | in_progress | unknown
    amount: number | null
    currency: string | null

# room_leads additions:
deal_status: string | null
deal_amount: number | null
deal_currency: string | null
deal_updated_at: datetime | null
```

`contracts/README.md` — строка.

---

## 6. Код

### 6.1. Данные

Nullable колонки на `room_leads` (+ миграция).

### 6.2. Domain / API

`apply_deal_status(db, payload)` в leads domain или `adapters/crm_inbound_stub.py`.

### 6.3. Тесты

1. Hand to CRM → deal-status won → поля на лиде.  
2. Неверный crm_ref → 404.  
3. Deal-status на `open`/`hot` → 409.  
4. List отдаёт deal_*.  
5. Регрессия C9 handoff outbox.

### 6.4. Frontend

LeadsPanel: для `handed_to_crm` показать deal_status / amount (если есть).

### 6.5. Docs

`backend/README.md` — curl deal-status.

---

## 7. DoD

- [ ] Ветка `feature/c19-crm-deal-status`.  
- [ ] Контракт + миграция + webhook + UI + pytest.  
- [ ] Не ломает C9 Hot path.  
- [ ] PR.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c19-crm-deal-status
База: origin/main после C15 (C9 leads).
Параллелен C16–C18, C20–C21: не трогай earnings, terminate, entitlement outbox, chat, service-token.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261019 - задание C19 CRM deal status.md

Сделай C19: CrmDealStatus contract; POST /internal/v1/crm/deal-status; поля deal_* на lead; UI; pytest.
Не делай live CRM, Deal entity, earnings.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Inbound only; C9 outbound intact.  
- Параллель с C16/C17 чистая (leads ≠ tasks/slots).
