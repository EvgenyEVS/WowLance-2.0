# Задание: C5 — StrategyPublished → Accept / Reject

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-15 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c5-strategy-accept` |
| **База** | актуальный `main` **после merge C2 + C3** |
| **Параллельность** | ✅ **можно делать параллельно с C4** (`feature/c4-staffing-slots`) |
| **Фаза** | C5 (inbox новой версии стратегии + решение тимлида) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](../../canon/ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../../../AGENTS.md) |
| **Предыдущее** | [C1 FounderHandoff](261010%20-%20задание%20C1%20FounderHandoff.md) · [C3 Room read](261010%20-%20задание%20C3%20Room%20read%20shell.md) |
| **Параллель** | [C4 Staffing slots](261015%20-%20задание%20C4%20Staffing%20slots.md) |

---

## 1. Зачем

По ADR: после старта комнаты новую версию стратегии **не применяют молча**. Событие «опубликована новая версия» → тимлид **Accept** / **Reject**. До Accept комната работает на **прежнем** снимке.

Сейчас после C1 есть ровно один immutable snapshot на комнату. Нужен контур: proposal → решение → смена активного снимка (или отказ). Редактор стратегии, live Strategy DB, Keycloak roles — **не** здесь.

---

## 2. Параллель с C4 — правила стыковки

| Можно | Нельзя |
|-------|--------|
| Новые файлы: `api/strategy_proposals.py`, `domain/strategy_accept.py`, миграции proposals / history | Менять `room_function_slots` / materialize C4 |
| Расширить `RoomRead` полями `strategy` (active) + опционально `pending_strategy` | Ломать staffing API C4 |
| Блок Accept/Reject на `RoomPage` | Править логику entitlement / slots |

Важно для стыка со слотами: после Accept **новый** active snapshot может содержать другой `staffing_intent`. C4 materialize уже созданные слоты **не** обязан пересоздавать в C5 (документируй: «пересборка слотов — later»). Не вызывай materialize из Accept.

---

## 3. Не трогать / не делать

- Редактор стратегии / запись в БД Strategy.  
- Staffing slots / materialize (C4).  
- Keycloak JWT и проверка роли teamlead по токену (достаточно stub-заголовка).  
- Уведомления email/push (достаточно записи proposal + UI).  
- Auto-apply minor vs breaking (в C5 **любая** новая версия = ручной Accept).  
- CRM, Jira, Outbox наружу, биллинг.  
- Копировать Django 1.0.

---

## 4. Продуктовые правила

1. Чужие БД не читать; payload новой версии приходит в POST (stub Strategy).  
2. Proposal только для **существующей** комнаты.  
3. Пока proposal `pending` — `GET /rooms/{id}` отдаёт **старый** active snapshot.  
4. **Accept** → новый снимок становится active; старый — `superseded` (история). Proposal → `accepted`.  
5. **Reject** → active не меняется; proposal → `rejected`.  
6. Одновременно на комнату — **не больше одного** `pending`. Второй publish при открытом pending → **409**.  
7. Повтор того же `publication_id` — идемпотентен (`already_exists` / тот же proposal).  
8. Accept/Reject не-pending proposal → **409**.  
9. Тот же `strategy_version`, что уже active, при publish → **409** (нет смысла).  
10. Handoff C1 по-прежнему создаёт **первый** active snapshot; C5 не ломает идемпотентность handoff.

---

## 5. Контракт (C0 этого шага)

### 5.1. StrategyPublished (вход)

Файл: `contracts/strategy/StrategyPublished.v1.yaml`  
Пример: `contracts/strategy/examples/StrategyPublished.sale.json`

```yaml
id: StrategyPublished
version: "1"
direction: Strategy -> WowLance
channel: https
path: /internal/v1/strategy-publications
method: POST
idempotency_key: publication_id

request:
  required: [publication_id, room_id, strategy_id, strategy_version, strategy]
  properties:
    publication_id: uuid
    room_id: uuid
    strategy_id: uuid
    strategy_version: string          # новая версия, != active
    strategy:
      required: [offer, audience, hot_criteria]
      properties:
        offer / audience / hot_criteria / utp?: string
    documents: [{ role, uri, checksum }]
    staffing_intent: object | null    # опционально, как в FounderHandoff

response_200:
  required: [proposal_id, room_id, status]
  properties:
    proposal_id: uuid
    room_id: uuid
    status: pending | already_exists
```

### 5.2. StrategyProposalDecide

В том же YAML или `StrategyProposalDecide.v1.yaml`:

```yaml
id: StrategyProposalDecide
version: "1"
paths:
  accept:
    method: POST
    path: /api/v1/rooms/{room_id}/strategy-proposals/{proposal_id}/accept
  reject:
    method: POST
    path: /api/v1/rooms/{room_id}/strategy-proposals/{proposal_id}/reject

headers:
  X-Actor-Sub: string   # stub тимлида; обязателен в C5

response_200:
  required: [proposal_id, room_id, decision, active_strategy_version]
  properties:
    proposal_id: uuid
    room_id: uuid
    decision: accepted | rejected
    active_strategy_version: string
```

### 5.3. RoomRead — дополнение

Обновить `contracts/wowlance/RoomRead.v1.yaml` (minor совместимое расширение):

```yaml
# добавить опционально:
pending_strategy:
  nullable: true
  properties:
    proposal_id: uuid
    strategy_version: string
    offer / audience / hot_criteria: string
    status: pending
```

`strategy` в RoomRead = **только active**.

Строки в `contracts/README.md`.

---

## 6. Что сделать в коде

### 6.1. Данные

**Вариант (рекомендуемый):**

1. Таблица `strategy_proposals`:
   - `id` (proposal_id), `publication_id` UNIQUE, `room_id`,  
   - `strategy_id`, `strategy_version`,  
   - `strategy_payload` JSONB, `documents` JSONB, `staffing_intent` JSONB,  
   - `status`: `pending | accepted | rejected`,  
   - `created_at`, `decided_at`, `decided_by_sub` nullable.

2. Перестроить `strategy_snapshots`:
   - снять unique «ровно одна строка на room»;  
   - добавить `status`: `active | superseded` (или `is_active` bool);  
   - partial unique index: один `active` на `room_id`;  
   - миграция данных: существующие строки → `active`.

Handoff create: по-прежнему одна `active`.  
Accept: старая `active` → `superseded`, insert новой `active` из proposal payload.  
Снимки **не** редактировать in-place (immutable).

### 6.2. API

```http
POST /internal/v1/strategy-publications
POST /api/v1/rooms/{room_id}/strategy-proposals/{proposal_id}/accept
POST /api/v1/rooms/{room_id}/strategy-proposals/{proposal_id}/reject
```

| Код | Когда |
|-----|--------|
| **200** | publish → `pending` / `already_exists` |
| **200** | accept / reject |
| **404** | нет комнаты / нет proposal |
| **409** | уже есть pending; version == active; decide не-pending; publication на другую room |
| **422** | валидация; нет `X-Actor-Sub` на decide |

`GET /api/v1/rooms/{id}`: active strategy + `pending_strategy` если есть.

Логика в `domain/`; thin routers. Internal publish — open + README; decide — требует `X-Actor-Sub`.

### 6.3. Тесты (pytest + PG)

1. Handoff → publish новой version → GET room: old offer в `strategy`, new в `pending_strategy`.  
2. Accept → GET: новый offer в `strategy`, `pending_strategy: null`; в БД старый snapshot `superseded`.  
3. Reject → GET: old active без изменений; proposal `rejected`.  
4. Второй publish при pending → 409.  
5. Повтор `publication_id` → `already_exists`.  
6. Publish с version == active → 409.  
7. Accept без `X-Actor-Sub` → 422.  
8. Регрессия: C1 handoff idempotency + C3 GET.

### 6.4. Frontend

На `RoomPage`:

1. Если есть `pending_strategy` — блок «Pending strategy vX» с offer/audience/hot_criteria.  
2. Кнопки **Accept** / **Reject** → POST с заголовком `X-Actor-Sub: teamlead-demo-sub` (константа в UI или поле ввода на странице — достаточно константы + комментарий).  
3. После решения — refetch room.  
4. Без pending — блока нет.

### 6.5. Документация

- `backend/README.md` — C5 + curl: handoff → publish → GET → accept → GET.  
- `frontend/README.md` — Accept/Reject stub.

---

## 7. DoD

- [ ] Ветка **`feature/c5-strategy-accept`** от `main` с C2+C3.  
- [ ] Контракты `StrategyPublished` (+ Decide) + example; обновлён `RoomRead.v1`.  
- [ ] Миграции proposals + snapshot history (`active`/`superseded`).  
- [ ] Publish / Accept / Reject + коды ошибок выше.  
- [ ] GET room показывает active + pending.  
- [ ] React: Accept/Reject с `X-Actor-Sub`.  
- [ ] `pytest` зелёный + регрессия C1/C3.  
- [ ] PR с ручным сценарием проверки.

---

## 8. Вне скоупа / параллель

- Staffing slots (C4)  
- Keycloak roles / настоящий teamlead  
- Diff UI «что изменилось»  
- Уведомления наружу / Outbox  

**Параллельно:** [C4 — Staffing slots](261015%20-%20задание%20C4%20Staffing%20slots.md).

---

## 9. Промпт для стажёра + ИИ (копировать целиком)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c5-strategy-accept
База: origin/main ПОСЛЕ merge C2 + C3.
Этот тикет ПАРАЛЛЕЛЕН C4 (feature/c4-staffing-slots): не трогай room_function_slots / materialize.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Читай AGENTS.md, docs/canon/ADR-002-wowlance-2.0-platform-room.md.
Задание: docs/261015 - задание C5 Strategy accept.md

Сделай C5:
1) contracts: StrategyPublished.v1.yaml + example; Decide paths; доп. pending_strategy в RoomRead.v1; contracts/README.md
2) strategy_proposals + strategy_snapshots status active|superseded (migration; существующие → active)
3) POST /internal/v1/strategy-publications — pending proposal; идемпотентность publication_id; 409 если уже pending или version==active
4) POST accept/reject с X-Actor-Sub — Accept меняет active snapshot; Reject нет
5) GET room: strategy=active, pending_strategy если есть
6) pytest на сценарии выше + регрессия handoff/GET
7) React RoomPage: pending блок + Accept/Reject
8) backend/README.md curl

Не делай staffing/slots, Keycloak JWT, редактор стратегии, CRM, уведомления.
Сначала план 5–8 шагов, потом маленькие коммиты.
```

---

## 10. Ревьюеру

- До Accept GET **не** подменяет active strategy.  
- Снимки immutable (supersede + insert), не UPDATE payload.  
- Один pending на комнату; идемпотентность по `publication_id`.  
- Не вызывает materialize слотов и не ломает C4 при merge.  
- Stub `X-Actor-Sub` достаточен; нет фейкового «полного Keycloak».
