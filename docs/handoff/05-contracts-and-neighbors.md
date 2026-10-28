# Контракты и взаимодействие со смежниками

| Артефакт | Путь |
|----------|------|
| Реестр | [contracts/REGISTRY.md](../../contracts/REGISTRY.md) |
| Owners / пинг | [guides/contracts-owners.md](../guides/contracts-owners.md) |
| Зоны до `agreed` | [guides/зоны…](../guides/261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) |
| Схема платформы | [diagrams/](../diagrams/) |

---

## Что такое контракт у нас

**Контракт** = правила обмена (поля, путь, идемпотентность, ошибки).  
**API** = рабочее «окошко» (`/internal/...`, `/api/...`), которое эти правила реализует.  
**Событие** = outbox-сообщение («случилось»), не обязательный request/response.

Соседи **не** подписывают `contracts/wowlance/*` (внутренний API комнаты).  
Подписывают свою папку: `strategy/`, `order/`, `talent/`, `crm/`, …

Сервис стратегии в документах: **Стратегия (US Closer)**.

---

## Статусы

| Статус | Смысл |
|--------|--------|
| `draft` | Черновик |
| `aligned` | Совпадает с нашим stub-кодом |
| `proposed` | Отдали соседу на review |
| `agreed` | Сосед принял → можно live-адаптер |

Сейчас: контракты **aligned / готовы к proposed**; **`agreed` нет** (owners часто TBD).

---

## Порядок стыковки (рекомендация)

1. Keycloak / Platform (единый `sub` + service-token)  
2. Стратегия (US Closer) — Handoff + RoomHealth  
3. Order — Entitlement  
4. Talent — RosterUpsert  
5. CRM — Hot + history + deal-status  

Пока нет `agreed` — развиваем stubs, UX, тесты. Live adapters — только после `agreed` по конкретному соседу.

---

## Как выдать пакет соседу

1. Ссылка на папку `contracts/<svc>/` + REGISTRY + схему.  
2. Просьба: `agreed` на v1 as-is **или** ≤5 вопросов.  
3. Прогон example JSON на stub (чеклист в contracts-owners).  
4. Запись статуса в REGISTRY / owners.

Breaking change → новая **v2**, не молчатая правка v1 после `agreed`.
