# Владельцы контрактов (C33)

Подготовка к `proposed → agreed`. **Это не live adapters.**

Пока нет `agreed` с соседом — **WowLance продолжает stubs** (см. [зоны до согласования](261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md)). Статусы `draft` / `aligned` в [REGISTRY](../../contracts/REGISTRY.md) значат «совпадает с нашим stub-кодом», не «сосед подписал».

Канал пинга ниже — TBD (Slack / GitHub issue). Имена владельцев — TBD, заполняет тимлид при выдаче.

## Сводка

| Сосед | Контракты (файлы) | Владелец | Канал пинга | Статус | Блокер для WL live |
|-------|-------------------|----------|-------------|--------|-------------------|
| Strategy | FounderHandoff, StrategyPublished, RoomCreated, RoomHealth | TBD Strategy / Founder Studio | Slack/issue TBD | aligned (код) / **proposed** к соседу | live handoff + health витрина |
| Order | EntitlementGranted, StaffingUnlocked | TBD Order / Payments | Slack/issue TBD | aligned / **proposed** | live unlock |
| Talent | TalentRosterUpsert, MemberTerminated, TaskAccepted | TBD Talent | Slack/issue TBD | aligned / **proposed** | live roster |
| CRM | HotLeadToCrm, CrmDealStatus | TBD CRM / SRM | Slack/issue TBD | aligned / **proposed** | live hot + deal-status |
| Keycloak | AuthBearer | TBD IAM | Slack/issue TBD | aligned / **proposed** | боевой realm |
| Platform | InternalServiceAuth | TBD Platform / Gateway | Slack/issue TBD | aligned / **proposed** | Gateway + service-token |
| Meet | RoomMeet | TBD Meet / Jitsi | Slack/issue TBD | aligned / **proposed** | live Jitsi |
| WowLance | `contracts/wowlance/*` | команда комнаты | внутренний | draft/aligned, **не** на подпись соседям | — |

## По соседу: YAML и что просим

Просим **`agreed` на v1 stub as-is**, либо ответ по открытым вопросам (не больше пяти).

### Strategy

- Каталог: [`contracts/strategy/`](../../contracts/strategy/)
- YAML: [FounderHandoff](../../contracts/strategy/FounderHandoff.v1.yaml) · [StrategyPublished](../../contracts/strategy/StrategyPublished.v1.yaml) · [RoomCreated](../../contracts/strategy/RoomCreated.v1.yaml) · [RoomHealth](../../contracts/strategy/RoomHealth.v1.yaml)
- Просим: `agreed` на handoff/publish/outbox as-is.
- Вопросы: (1) `handoff_id` идемпотентность ок? (2) RoomHealth `earnings` блок ок? (3) documents только URI+checksum?

### Order

- Каталог: [`contracts/order/`](../../contracts/order/)
- YAML: [EntitlementGranted](../../contracts/order/EntitlementGranted.v1.yaml) · [StaffingUnlocked](../../contracts/order/StaffingUnlocked.v1.yaml)
- Просим: `agreed` вместо отдельного `PaymentSucceeded` на границе WL.
- Вопросы: (1) `entitlement_id` как ключ ок? (2) нужен ли outbound Order-status сверх StaffingUnlocked?

### Talent

- Каталог: [`contracts/talent/`](../../contracts/talent/)
- YAML: [TalentRosterUpsert](../../contracts/talent/TalentRosterUpsert.v1.yaml) · [MemberTerminated](../../contracts/talent/MemberTerminated.v1.yaml) · [TaskAccepted](../../contracts/talent/TaskAccepted.v1.yaml)
- Просим: `agreed` на stub upsert + outbox terminate/accept.
- Вопросы: (1) GET list roster — только WL? (2) ProfileChanged откладываем? (3) amount в TaskAccepted опционален?

### CRM

- Каталог: [`contracts/crm/`](../../contracts/crm/)
- YAML: [HotLeadToCrm](../../contracts/crm/HotLeadToCrm.v1.yaml) · [CrmDealStatus](../../contracts/crm/CrmDealStatus.v1.yaml)
- Просим: `agreed` на stub outbox + inbound deal-status.
- Вопросы: (1) `crm-stub:<lead_id>` как ref ок до live? (2) `deal_amount` string?

### Keycloak / platform

- YAML: [AuthBearer](../../contracts/keycloak/AuthBearer.v1.yaml) · [InternalServiceAuth](../../contracts/platform/InternalServiceAuth.v1.yaml)
- Просим: `agreed` на JWT aud/iss и `X-Service-Token` для `/internal/v1/*`.
- Вопросы: (1) Gateway скрывает `/internal`? (2) realm roles vs local room_members (C27)?

### Meet

- YAML: [RoomMeet](../../contracts/meet/RoomMeet.v1.yaml)
- Просим: `agreed` на stub URL `meeting_url` в RoomRead.
- Вопросы: (1) формат Jitsi URL?

## Шаблон пинга (issue / Slack)

```text
Привет! Нужен review граничных контрактов WowLance 2.0 → статус agreed (v1 stub as-is).

Реестр: https://github.com/EvgenyEVS/WowLance-2.0/blob/main/contracts/REGISTRY.md
Ваш каталог: contracts/<svc>/ (YAML + examples).
Владельцы / блокеры: docs/contracts-owners.md

Пока нет agreed — комната живёт на stubs; live HTTP/bus не подключаем.
Просьба: пройти YAML, прогнать stub-чеклист ниже (по желанию), ответить agreed или ≤5 вопросов.
Срок ответа / канал: TBD.
```

## Чеклист для соседа (против нашего stub)

1. Поднять WL: `docker compose up -d db` + alembic + uvicorn `:8000`, `AUTH_DISABLED=true`.
2. Прогнать свой example JSON на `POST /internal/v1/…` (см. YAML path).
3. Повтор того же id → 200 already_exists / already_granted, не новая сущность.
4. Другой payload на тот же id → 409.
5. Сверить поля ответа с example / REGISTRY.

Не просим live sandbox на этом шаге.

## Не согласовываем сейчас

Jira sync, deep CRM, live matching / ProfileChanged, биллинг лида, полный Gateway map — [зоны §3](261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md).
