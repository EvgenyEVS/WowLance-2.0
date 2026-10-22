# Stub hardening (C32)

Канон 4xx **не плодим третий shape**. Проект уже на FastAPI:

```json
{ "detail": "forbidden_role" }
```

или, для 422 валидации Pydantic:

```json
{ "detail": [ { "type": "...", "loc": [...], "msg": "..." } ] }
```

`detail` — **строка-код** или человекочитаемое сообщение. Известные коды:

| HTTP | `detail` (примеры) | Когда |
|------|--------------------|--------|
| 403 | `forbidden_role`, `staffing_locked` | RBAC / locked staffing |
| 404 | `room_id does not exist`, `freelancer_not_in_roster`, … | нет сущности |
| 409 | `conflict` messages: illegal transition, handoff payload mismatch, `already_seated` | конфликт состояния |
| 422 | FastAPI list **или** `X-Actor-Sub header is required` | валидация |
| 401 | Bearer / `Internal service token required` | auth |

Не оборачиваем в `{ "detail": { "code", "message" } }` — это был бы третий формат и сломал бы pytest.

## Идемпотентные POST (stub)

| Endpoint | Повтор | Побочка |
|----------|--------|---------|
| `POST /internal/v1/handoffs` тот же `handoff_id` + payload | 200 `already_exists`, тот же `room_id` | snapshot не переписывается |
| тот же `handoff_id`, другой payload | 409 | нет новой комнаты |
| `POST /internal/v1/entitlements` тот же `entitlement_id` | 200 `already_granted` | нет второго unlock/outbox |
| `POST /internal/v1/crm/deal-status` тот же `crm_ref` + поля | 200, те же deal_* | без дубля outbox C9 |
| `POST …/meet/ensure` | тот же URL | `already_exists` |
| `POST …/slots/{id}/assign` тот же freelancer | `already_assigned` | |
| create **task/lead** | каждый POST — новая сущность (нет natural key) | 201, не 500 |

Live broker / Gateway / доставка outbox **не** входят в C32.

## Логи

Internal stub входы пишут одну строку logger `wowlance.stub`:

`event=handoff outcome=created room_id=… handoff_id=…`

Без dump тела запроса (PII).

`X-Request-Id`: если клиент прислал — эхо в ответе; иначе UUID.

`GET /health` без изменений.

`AUTH_DISABLED=true` + `scripts/founder-demo.ps1` остаются рабочими.
