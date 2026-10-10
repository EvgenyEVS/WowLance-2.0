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

Канон: [`docs/ADR-002-wowlance-2.0-platform-room.md`](docs/ADR-002-wowlance-2.0-platform-room.md).

- WowLance = универсальная **комната исполнения** (sale + develop).  
- Целевая модель данных: Hybrid **C**; первый срез = snapshot **A** (`FounderHandoff`).  
- Handoff может создать комнату **до** оплаты; **staffing** — после entitlement.  
- Не входит: Jira, CRM как продукт, редактор стратегии, Talent-онбординг, биллинг лида.

Django [WowLance 1.0](https://github.com/EvgenyEVS/WowLance) — **reference** смыслов (RBAC, Quality Gate, Hot, staffing), не исходник для копирования.

## Структура репо

```text
contracts/wowlance/   OpenSpec / схемы + examples
backend/              FastAPI
frontend/             React
docs/                 ADR + architecture
```

## Workflow

1. Контракт / acceptance в `contracts/`  
2. Реализация + тесты  
3. Stubs адаптеров Strategy/Talent/Billing до live  

Локальные пути:

- Этот репозиторий: `C:\Программирование\Стажировка Wowlance\WowLance-2.0`  
- Документы-исходники 2.0 (исторически): `...\WowLance\WowLance 2.0`  
- Демо 1.0: `...\WowLance`  
