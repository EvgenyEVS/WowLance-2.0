# Реестр контрактов WowLance 2.0

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-22 |
| **Правило** | Контракт раньше кода; путь = сервис-сосед (или `wowlance` для API комнаты) |
| **Проверка** | Сверка YAML ↔ `backend/app` (API paths, Pydantic `schemas.py`, outbox event_type) |

Раскладка:

```text
contracts/
  strategy/   ← Strategy (Founder Studio)
  order/      ← Order / Payments
  talent/     ← Talent
  crm/        ← CRM / SRM
  keycloak/   ← вход пользователей (JWT)
  platform/   ← сервис↔сервис (Gateway / service-token)
  meet/       ← Jitsi / Meet
  wowlance/   ← API комнаты (клиент → WowLance)
```

**Статусы:** `draft` — черновик OpenSpec · `aligned` — совпадает с кодом stub · `agreed` — подписан соседом (пока ни одного).

**Синонимы из arch-доков → фактический id:**

| В architecture / ADR | Фактический контракт |
|----------------------|----------------------|
| PaymentSucceeded | `EntitlementGranted` (вход в WL) |
| RoomStarted | `RoomCreated` |
| ReportAccepted | `TaskAccepted` |
| LeadHandedToCrm | `HotLeadToCrm` |
| RoomHealthSnapshot (событие) | outbox `event_type` внутри `RoomHealth` |
| FreelancerProfileChanged | пока нет (есть `TalentRosterUpsert`) |

---

## 1. Strategy

| Контракт | Файл | Направление | Канал | Фаза | Статус | Совместимость с кодом |
|----------|------|-------------|-------|------|--------|------------------------|
| **FounderHandoff** | [strategy/FounderHandoff.v1.yaml](strategy/FounderHandoff.v1.yaml) | Strategy → WL | `POST /internal/v1/handoffs` | C1 | aligned | Поля и ответы = `FounderHandoffRequest/Response`; идемпотентность `handoff_id` |
| **StrategyPublished** | [strategy/StrategyPublished.v1.yaml](strategy/StrategyPublished.v1.yaml) | Strategy → WL | `POST /internal/v1/strategy-publications` | C5 | aligned | = `StrategyPublishedRequest/Response` |
| **StrategyProposalDecide** | тот же YAML (второй документ) | client → WL | accept/reject `/api/v1/rooms/…/strategy-proposals/…` | C5 | aligned | Пути в `strategy_proposals.py`; header `X-Actor-Sub` |
| **RoomCreated** | [strategy/RoomCreated.v1.yaml](strategy/RoomCreated.v1.yaml) | WL → Strategy/platform | outbox `RoomCreated` | C11 | aligned | `handoff.py` `ROOM_CREATED_EVENT`; key=`room_id` |
| **RoomHealth** | [strategy/RoomHealth.v1.yaml](strategy/RoomHealth.v1.yaml) | WL → Strategy | GET health + publish outbox | C13/C25 | aligned | GET + `POST …/health/publish`; outbox `RoomHealthSnapshot`; блок `earnings` |

Примеры: `strategy/examples/`.

---

## 2. Order / Payments

| Контракт | Файл | Направление | Канал | Фаза | Статус | Совместимость с кодом |
|----------|------|-------------|-------|------|--------|------------------------|
| **EntitlementGranted** | [order/EntitlementGranted.v1.yaml](order/EntitlementGranted.v1.yaml) | Order/Payments → WL | `POST /internal/v1/entitlements` | C2 | aligned | = `EntitlementGrantedRequest/Response`; unlock + outbox StaffingUnlocked |
| **StaffingUnlocked** | [order/StaffingUnlocked.v1.yaml](order/StaffingUnlocked.v1.yaml) | WL → Order/Strategy | outbox `StaffingUnlocked` | C18 | aligned | key=`room:{id}:StaffingUnlocked` в `entitlement.py` |

Примеры: `order/examples/`.  
*Заметка:* отдельного `PaymentSucceeded` / Order-status YAML нет — для согласований Order достаточно `EntitlementGranted` + опционально расширить позже.

---

## 3. Talent

| Контракт | Файл | Направление | Канал | Фаза | Статус | Совместимость с кодом |
|----------|------|-------------|-------|------|--------|------------------------|
| **TalentRosterUpsert** | [talent/TalentRosterUpsert.v1.yaml](talent/TalentRosterUpsert.v1.yaml) | Talent → WL (+ GET list client) | `POST /internal/v1/roster`, `GET /api/v1/roster` | C6 | aligned | Upsert = schemas; **добавлен** path GET list (был только в коде) |
| **MemberTerminated** | [talent/MemberTerminated.v1.yaml](talent/MemberTerminated.v1.yaml) | WL → Talent | API terminate + outbox | C17 | aligned | Paths и outbox `MemberTerminated` |
| **TaskAccepted** | [talent/TaskAccepted.v1.yaml](talent/TaskAccepted.v1.yaml) | WL → Talent/platform | outbox `TaskAccepted` | C24 | aligned | key=`task:{id}:TaskAccepted`; amount/currency опционально из earnings |

Примеры: `talent/examples/`.

---

## 4. CRM / SRM

| Контракт | Файл | Направление | Канал | Фаза | Статус | Совместимость с кодом |
|----------|------|-------------|-------|------|--------|------------------------|
| **HotLeadToCrm** | [crm/HotLeadToCrm.v1.yaml](crm/HotLeadToCrm.v1.yaml) | WL → CRM | outbox `HotLeadToCrm` | C9 | aligned | Payload = `crm_stub.build_hot_lead_payload`; `crm-stub:<lead_id>` |
| **CrmDealStatus** | [crm/CrmDealStatus.v1.yaml](crm/CrmDealStatus.v1.yaml) | CRM → WL | `POST /internal/v1/crm/deal-status` | C19 | aligned | Request/response = schemas; `deal_amount` string |

Примеры: `crm/examples/` (deal-status example пока нет — добавить при согласовании).

Связанный **внутренний** API лидов: `wowlance/RoomLeads.v1.yaml`.

---

## 5. Keycloak

| Контракт | Файл | Направление | Канал | Фаза | Статус | Совместимость с кодом |
|----------|------|-------------|-------|------|--------|------------------------|
| **AuthBearer** | [keycloak/AuthBearer.v1.yaml](keycloak/AuthBearer.v1.yaml) | client → WL | `Authorization: Bearer` на `/api/v1/*` | C8 | aligned | `require_user` + shadow User; `/internal` не user-JWT (см. platform) |

---

## 6. Platform (Gateway / service auth)

| Контракт | Файл | Направление | Канал | Фаза | Статус | Совместимость с кодом |
|----------|------|-------------|-------|------|--------|------------------------|
| **InternalServiceAuth** | [platform/InternalServiceAuth.v1.yaml](platform/InternalServiceAuth.v1.yaml) | service → WL | `X-Service-Token` на `/internal/v1/*` | C21 | aligned | middleware в `main.py`; fail-fast без токена |

---

## 7. Meet (Jitsi)

| Контракт | Файл | Направление | Канал | Фаза | Статус | Совместимость с кодом |
|----------|------|-------------|-------|------|--------|------------------------|
| **RoomMeet** | [meet/RoomMeet.v1.yaml](meet/RoomMeet.v1.yaml) | client → WL → Jitsi URL | `POST /api/v1/rooms/{id}/meet/ensure` | C14 | aligned | `meet_stub` + `meeting_url` в RoomRead |

---

## 8. WowLance (API комнаты)

Владелец — сервис комнаты. Соседям на подпись обычно **не** нужны, кроме ознакомления.

| Контракт | Файл | Канал | Фаза | Статус | Совместимость с кодом |
|----------|------|-------|------|--------|------------------------|
| **RoomRead** | [wowlance/RoomRead.v1.yaml](wowlance/RoomRead.v1.yaml) | GET room | C3/C5/C14 | aligned | + `pending_strategy`, `meeting_url` |
| **StaffingSlots** | [wowlance/StaffingSlots.v1.yaml](wowlance/StaffingSlots.v1.yaml) | slots CRUD-like | C4/C6/C12/C22 | aligned | materialize / assign / unassign / reassign / rematerialize |
| **SlotMatch** | [wowlance/SlotMatch.v1.yaml](wowlance/SlotMatch.v1.yaml) | GET match | C23 | aligned* | *исправлено: `skills`/`level` nullable (как в коде) |
| **RoomTasks** | [wowlance/RoomTasks.v1.yaml](wowlance/RoomTasks.v1.yaml) | tasks + QG | C7/C10/C15 | aligned | статусы + proof + assign |
| **RoomLeads** | [wowlance/RoomLeads.v1.yaml](wowlance/RoomLeads.v1.yaml) | leads lifecycle | C9/C19 | aligned* | *исправлено: `deal_amount` string (было number) |
| **RoomMessages** | [wowlance/RoomMessages.v1.yaml](wowlance/RoomMessages.v1.yaml) | chat | C20 | aligned | list + post |
| **RoomEarnings** | [wowlance/RoomEarnings.v1.yaml](wowlance/RoomEarnings.v1.yaml) | ledger | C16 | aligned | GET earnings |
| **RoomMembers** | [wowlance/RoomMembers.v1.yaml](wowlance/RoomMembers.v1.yaml) | membership | C27 | draft | GET list + POST promote teamlead; local roles, not Keycloak |

Примеры: `wowlance/examples/`.

---

## 9. Что ещё нет (для будущих согласований)

| Тема | Сосед | Зачем |
|------|------|--------|
| PaymentSucceeded / OrderStatus (outbound Order) | Order | Если entitlement не единственный сигнал |
| FreelancerProfileChanged / Verified | Talent | Live sync beyond upsert |
| Gateway route map | Platform | Публичные vs internal пути |
| Object storage URI convention | Strategy / Platform | SOP documents |
| Jira issue sync | Jira | По ADR не обязательно для sale |

---

## 10. Итог проверки 2026-10-22

| Результат | Деталь |
|-----------|--------|
| Paths / methods | Совпадают с роутерами FastAPI |
| Outbox event_type | `RoomCreated`, `StaffingUnlocked`, `HotLeadToCrm`, `MemberTerminated`, `TaskAccepted`, `RoomHealthSnapshot` |
| Исправлено при ревизии | `RoomLeads.deal_amount` → string; `SlotMatch` nullable skills/level; `TalentRosterUpsert` + GET list; AuthBearer ссылка на C21 |
| Не блокер | Нет example для CrmDealStatus; нет live broker (stub `sent`) — ожидаемо |
| Переписывать с нуля | **Не нужно** — реестр + папки по сервисам снимают путаницу |
