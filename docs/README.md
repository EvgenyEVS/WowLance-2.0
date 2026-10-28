# Документация WowLance 2.0

## Передача новой команде

**→ [handoff/START.md](handoff/START.md)** — читать первым.

| Раздел handoff | Содержание |
|----------------|------------|
| [01 продукт](handoff/01-product-boundaries.md) | Границы, соседи |
| [02 архитектура](handoff/02-architecture.md) | Стек, каналы, модули |
| [03 запуск](handoff/03-getting-started.md) | Docker, API, UI, demo |
| [04 карта репо](handoff/04-repository-map.md) | Структура каталогов |
| [05 контракты](handoff/05-contracts-and-neighbors.md) | OpenSpec, `agreed` |
| [06 процесс](handoff/06-development-workflow.md) | Контракт → PR |
| [07 тесты](handoff/07-testing-and-qa.md) | pytest, QA |
| [08 статус](handoff/08-status-and-backlog.md) | C0–C42, бэклог |
| [09 долги](handoff/09-debts-and-risks.md) | P0–P2 |
| [10 глоссарий](handoff/10-glossary.md) | Термины |

---

## Каталог по папкам

| Папка | Содержание |
|-------|------------|
| [handoff/](handoff/) | Пакет передачи команды |
| [canon/](canon/) | [ADR-002](canon/ADR-002-wowlance-2.0-platform-room.md) — канон продукта |
| [architecture/](architecture/) | Overview, Hybrid C, integration map, decisions |
| [diagrams/](diagrams/) | Схемы платформы (MD + PNG) |
| [guides/](guides/) | Owners, зоны до согласования, stub hardening |
| [status/](status/) | Отчёты готовности, аудит, UI parity |
| [phases/assignments/](phases/assignments/) | Задания срезов C1–C42 |
| [phases/qa/](phases/qa/) | QA-отчёты |
| [demo/](demo/) | Founder-demo чеклист |
| [ui-parity/](ui-parity/) | Скриншоты 1.0 vs 2.0 |

**Контракты (код):** [`../contracts/`](../contracts/) · [REGISTRY](../contracts/REGISTRY.md)

> Старые пути (`docs/ADR-002-…`, `docs/contracts-owners.md`, `docs/261022 - зоны…`) оставлены как **редиректы** на новые папки.

---

## Быстрые ссылки

| Тема | Документ |
|------|----------|
| ADR | [canon/ADR-002](canon/ADR-002-wowlance-2.0-platform-room.md) |
| Схема (обзор) | [diagrams PNG](diagrams/261024%20-%20схема%20платформы%20WOWLANCE.png) |
| Схема (tech / БД) | [diagrams tech PNG](diagrams/261024%20-%20схема%20платформы%20WOWLANCE%20tech.png) |
| Owners контрактов | [guides/contracts-owners.md](guides/contracts-owners.md) |
| Зоны до `agreed` | [guides/зоны](guides/261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) |
| Hardening stubs | [guides/hardening-stub.md](guides/hardening-stub.md) |
| Demo | [demo/founder-demo.md](demo/founder-demo.md) |
| Аудит / no-rewrite | [status/аудит](status/261026%20-%20технический%20аудит%20и%20обоснование%20рефакторинга.md) |
| Отчёт стейкхолдерам | [status/261023](status/261023%20-%20отчёт%20стейкхолдерам%20готовность.md) |

---

## Фазы (задания)

Полная таблица — в [корневом README](../README.md).  
Файлы заданий: [phases/assignments/](phases/assignments/).  
QA: [phases/qa/](phases/qa/).
