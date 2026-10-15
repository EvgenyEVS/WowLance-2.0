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
| **C0** | Контракты (`FounderHandoff` v1) |
| **C1** | Handoff → комната + immutable snapshot |
| **C2** | Keycloak + React shell + tasks |
| **C3+** | Talent roster, Accept стратегии, adapters |

## Политика оплаты

Комната может создаться по handoff **до** оплаты; **staffing** — только после entitlement (`PaymentSucceeded` / Order).
