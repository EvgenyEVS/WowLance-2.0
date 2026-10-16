# WowLance 2.0

Сервис **универсальной рабочей комнаты** в общей платформе (Keycloak · Gateway · соседние Strategy / Talent / CRM / Order).

| | |
|--|--|
| **Стек** | FastAPI · React · PostgreSQL · OpenSpec · Superpowers |
| **Канон** | [ADR-002](docs/ADR-002-wowlance-2.0-platform-room.md) |
| **Для ИИ / команды** | [AGENTS.md](AGENTS.md) |
| **1.0 (reference)** | [EvgenyEVS/WowLance](https://github.com/EvgenyEVS/WowLance) |

## Структура

```text
contracts/   OpenSpec-контракты (C0) — править раньше кода
backend/     FastAPI + PostgreSQL
frontend/    React (Vite + TypeScript)
docs/        ADR-002 и архитектурные материалы
```

## Быстрый старт (скелет)

```powershell
# PostgreSQL (host port 5433 — см. docker-compose.yml)
docker compose up -d db

# API
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy ..\.env.example .env
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000

# UI (после npm create / install)
cd ..\frontend
npm install
npm run dev
```

C1 handoff: [backend/README.md](backend/README.md) (`POST /internal/v1/handoffs`).  
C3 room UI: [frontend/README.md](frontend/README.md) (`GET /api/v1/rooms/{id}` → `/rooms/:roomId`).  
Health: http://127.0.0.1:8000/health  

## Фазы

| Фаза | Содержание |
|------|------------|
| **C0–C1** | Контракты + FounderHandoff → комната + snapshot |
| **C2** | Entitlement → `staffing_unlocked` |
| **C3** | GET room + React shell |
| **C4** | Staffing slots (gated) |
| **C5** | StrategyPublished → Accept/Reject |
| **C6** | Local roster + assign — [задание](docs/261015%20-%20задание%20C6%20Roster%20assign.md) |
| **C7** | Room tasks — [задание](docs/261015%20-%20задание%20C7%20Room%20tasks.md) |
| **C8** | Keycloak JWT + shadow User — [задание](docs/261016%20-%20задание%20C8%20Keycloak%20JWT.md) ∥ C9 |
| **C9** | Hot lead → CRM stub — [задание](docs/261016%20-%20задание%20C9%20Hot%20lead%20CRM.md) ∥ C8 |
| **C10+** | Quality Gate, live adapters, `wowlance_test` DB |

## Политика оплаты

Комната может создаться по handoff **до** оплаты; **staffing** — только после entitlement (`PaymentSucceeded` / Order).
