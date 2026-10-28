# Agent / developer guide — WowLance 2.0

## Stack (обязательно)

- **FastAPI** — HTTP API сервиса комнаты  
- **React** (Vite + TypeScript) — UI  
- **PostgreSQL** — единственная БД сервиса  
- **OpenSpec** — контракты в `contracts/` (менять до кода)  
- **Superpowers** — спека → план → маленькие PR → тесты  

Платформа: Keycloak JWT, API Gateway (локально можно mock).  
Чужие БД (Strategy / Talent / CRM) **не читать**.

## Продукт

Канон: [`docs/canon/ADR-002-…`](docs/canon/ADR-002-wowlance-2.0-platform-room.md).  
**Передача другой команде:** [`docs/handoff/START.md`](docs/handoff/START.md).

- WowLance = универсальная **комната исполнения** (sale + develop).  
- Целевая модель данных: Hybrid **C**; первый срез = snapshot **A** (`FounderHandoff`).  
- Handoff может создать комнату **до** оплаты; **staffing** — после entitlement.  
- Не входит: Jira, CRM как продукт, редактор стратегии, Talent-онбординг, биллинг лида.

Django [WowLance 1.0](https://github.com/EvgenyEVS/WowLance) — **reference** смыслов (RBAC, Quality Gate, Hot, staffing), не исходник для копирования.

## Структура репо

```text
contracts/           OpenSpec по сервисам (см. REGISTRY.md)
backend/             FastAPI
frontend/            React (Vite + TypeScript)
docs/
  handoff/           ← старт для новой команды
  canon/             ADR-002
  phases/            задания C0–C42 + QA
  status/            отчёты готовности
  guides/            зоны stub, owners, hardening
  diagrams/          схемы платформы
  architecture/      концепты A/B/C, integration map
```

## Workflow

1. Контракт / acceptance в `contracts/`  
2. Реализация + тесты  
3. Stubs адаптеров Strategy/Talent/Billing до live (`agreed`)  

## Задания стажёрам / промпты ИИ

В **каждом** задании явно указывать:

- **название новой ветки** (например `feature/c1-founder-handoff`) от актуального `main`;
- стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers;
- путь к файлу задания в `docs/phases/assignments/`.

Локальные пути:

- Этот репозиторий: `C:\Программирование\Стажировка Wowlance\WowLance-2.0`  
- Демо 1.0 (reference): `...\WowLance`  
