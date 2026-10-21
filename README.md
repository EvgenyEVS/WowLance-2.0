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

**Auth (C8):** по умолчанию `AUTH_DISABLED=true` — `/api/v1/*` открыт (локальный demo).  
Строгий режим: `AUTH_DISABLED=false` → 401 без Bearer JWT; токен за 2 минуты — `POST /auth/stub-token` (`AUTH_STUB_JWKS=true`) или свой Keycloak/JWKS. Подробнее: [backend/README.md](backend/README.md) (C8), UI-логин: [frontend/README.md](frontend/README.md).

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
| **C10** | Quality Gate lite — [задание](docs/261017%20-%20задание%20C10%20Quality%20Gate.md) ∥ C11 |
| **C11** | Outbox `RoomCreated` — [задание](docs/261017%20-%20задание%20C11%20RoomCreated%20outbox.md) ∥ C10 |
| **C12** | Slot unassign / reassign — [задание](docs/261017%20-%20задание%20C12%20Slot%20unassign.md) ∥ C11 · C13 |
| **C13** | Room health stub → Strategy — [задание](docs/261017%20-%20задание%20C13%20Room%20health.md) ∥ C11 · C12 |
| **C14** | Meet / Jitsi stub — [задание](docs/261017%20-%20задание%20C14%20Meet%20Jitsi%20stub.md) ∥ C11–C13 · C15–C17 |
| **C15** | Task assignee из roster — [задание](docs/261017%20-%20задание%20C15%20Task%20roster%20assignee.md) ∥ C11–C14 · C16–C17 |
| **C16** | «Я заработал» stub — [задание](docs/261017%20-%20задание%20C16%20Earnings%20stub.md) ∥ C11–C15 · C17–C21 |
| **C17** | MemberTerminated lite — [задание](docs/261017%20-%20задание%20C17%20Member%20terminated.md) ∥ C11 · C13–C16 · C18–C21 (осторожно с C12) |
| **C18** | Outbox `StaffingUnlocked` — [задание](docs/261019%20-%20задание%20C18%20StaffingUnlocked%20outbox.md) ∥ C16–C17 · C19–C21 |
| **C19** | CRM deal-status inbound — [задание](docs/261019%20-%20задание%20C19%20CRM%20deal%20status.md) ∥ C16–C18 · C20–C21 |
| **C20** | Room chat stub — [задание](docs/261019%20-%20задание%20C20%20Room%20chat.md) ∥ C16–C19 · C21 |
| **C21** | Internal service-token stub — [задание](docs/261019%20-%20задание%20C21%20Internal%20service%20token.md) ∥ C16–C20 |
| **C22** | Slot rematerialize — [задание](docs/261021%20-%20задание%20C22%20Slot%20rematerialize.md) ∥ C19 · C23–C25 |
| **C23** | Matching lite — [задание](docs/261021%20-%20задание%20C23%20Matching%20lite.md) ∥ C19 · C22 · C24–C25 |
| **C24** | Outbox `TaskAccepted` — [задание](docs/261021%20-%20задание%20C24%20TaskAccepted%20outbox.md) ∥ C19 · C22–C23 · C25 |
| **C25** | Earned в Room health — [задание](docs/261021%20-%20задание%20C25%20Health%20earnings.md) ∥ C19 · C22–C24 |
| **C26+** | Полный RBAC, live adapters, Gateway |

## Политика оплаты

Комната может создаться по handoff **до** оплаты; **staffing** — только после entitlement (`PaymentSucceeded` / Order).
