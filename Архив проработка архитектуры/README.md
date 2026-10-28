# WowLance 2.0

Пакет документов по входу сервиса в общую инфраструктуру (Keycloak, Gateway, FastAPI, React, PostgreSQL, OpenSpec).

| # | Файл | Содержание |
|---|------|------------|
| — | [ADR-002](../docs/canon/ADR-002-wowlance-2.0-platform-room.md) · [ADR-002.md](ADR-002.md) | **Принятый ADR WowLance 2.0** (канон в `docs/canon/`) |
| 0 | [00-decisions.md](00-decisions.md) | Журнал решений (сведён в ADR-002) |
| 1 | [01-overview.md](01-overview.md) | Технический обзор: переделки, смежники, 3 концепции, рекомендация |
| 1b | [01-overview for PO.md](01-overview%20for%20PO.md) | Для PO: сравнение вариантов простым языком, рекомендация, верхние вопросы |
| 2 | [02-concept-A-snapshot.md](02-concept-A-snapshot.md) | Концепция A — Snapshot Room |
| 3 | [03-concept-B-federated.md](03-concept-B-federated.md) | Концепция B — Federated Live |
| 4 | [04-concept-C-hybrid.md](04-concept-C-hybrid.md) | Концепция C — Hybrid Contract ★ целевая |
| 5 | [05-integration-map.md](05-integration-map.md) | Схема обменов: Keycloak, Стратегия, Таланты, SRM, Платежи, Order, Jira, Jitsi |
| 6 | [06-tz-vs-2.0-architecture.md](06-tz-vs-2.0-architecture.md) | Разбор исходного ТЗ 010101: есть ли схема МС, реконструкция, сравнение с 2.0 |
| 7 | [07-jira-roles-model.md](07-jira-roles-model.md) | Задачи/аналитика по ролям: WL↔Jira, кто master, UX директора/TL/фрилансера |

Для PO: `01-overview for PO`. Для команды: `01` → `04` → `02` → `03`. Обмены: `05`. Jira-роли: `07`.
