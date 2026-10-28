# Передача WowLance 2.0 — начните здесь

| Поле | Значение |
|------|----------|
| **Дата пакета** | 2026-10-28 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Для кого** | Команда, принимающая микросервис комнаты |
| **Статус продукта** | Stub-MVP комнаты готов к демо и согласованию контрактов; live с соседями — после `agreed` |

---

## Что вы принимаете

**WowLance 2.0** — микросервис **рабочей комнаты** платформы WOWLANCE:

- команда (слоты, roster, matching lite);
- снимок стратегии из **Стратегия (US Closer)**;
- задачи + Quality Gate;
- прогрев лидов до Hot → CRM;
- сводки health / earnings для витрины фаундера;
- chat / meet stubs, RBAC lite, founder-demo.

Это **не** вся платформа. Соседи: US Closer, Talent, CRM, Keycloak, Order / Payment / Invoicing.

---

## Читать по порядку (1–2 часа)

| # | Документ | Зачем |
|---|----------|--------|
| 1 | [01 — продукт и границы](01-product-boundaries.md) | Что входит / не входит |
| 2 | [02 — архитектура](02-architecture.md) | Стек, БД, каналы, Gateway |
| 3 | [03 — запуск](03-getting-started.md) | Поднять локально за 15 минут |
| 4 | [04 — карта репозитория](04-repository-map.md) | Где какой код |
| 5 | [05 — контракты и соседи](05-contracts-and-neighbors.md) | OpenSpec, REGISTRY, порядок `agreed` |
| 6 | [06 — процесс разработки](06-development-workflow.md) | Контракт → код → тесты → PR |
| 7 | [07 — тесты и QA](07-testing-and-qa.md) | pytest, демо, отчёты |
| 8 | [08 — статус и бэклог](08-status-and-backlog.md) | Что сделано (C0–C42), что дальше |
| 9 | [09 — долги и риски](09-debts-and-risks.md) | Auth defaults, outbox, UI parity |
| 10 | [10 — глоссарий](10-glossary.md) | Термины |

**Канон продукта:** [ADR-002](../canon/ADR-002-wowlance-2.0-platform-room.md)  
**Схемы платформы:** [diagrams/](../diagrams/)  
**Индекс всех docs:** [../README.md](../README.md)

---

## Быстрая проверка «мы на месте»

```powershell
docker compose up -d db
cd backend
# venv + pip + alembic + uvicorn — см. 03-getting-started.md
cd ..\frontend
npm install
npm run dev
# другой терминал:
powershell -File scripts\founder-demo.ps1
cd backend
.\.venv\Scripts\pytest -q
```

Ожидание: demo отрабатывает золотой путь; pytest зелёный (ориентир ~200+).

---

## Чего не делать в первые недели

1. Не читать чужие БД соседей — только контракты.  
2. Не включать signup/пароли в WowLance — Keycloak.  
3. Не тащить полноценную CRM / deals в комнату.  
4. Не стартовать live-адаптеры без `agreed` по контракту соседа.  
5. Не rewrite «с нуля» — см. [аудит](../status/261026%20-%20технический%20аудит%20и%20обоснование%20рефакторинга.md): инкремент, не снос.

---

## Контакты / артефакты для смежников

| Артефакт | Путь |
|----------|------|
| Реестр контрактов | [contracts/REGISTRY.md](../../contracts/REGISTRY.md) |
| Владельцы контрактов | [guides/contracts-owners.md](../guides/contracts-owners.md) |
| Зоны до согласования | [guides/…](../guides/261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) |
| Founder demo | [demo/founder-demo.md](../demo/founder-demo.md) |
| Схема (PNG) | [diagrams/](../diagrams/) |
