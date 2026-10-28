# WowLance 2.0

Сервис **универсальной рабочей комнаты** в платформе WOWLANCE  
(Keycloak · Gateway · **Стратегия (US Closer)** · Talent · CRM · Order).

| | |
|--|--|
| **Стек** | FastAPI · React · PostgreSQL · OpenSpec |
| **Канон** | [ADR-002](docs/canon/ADR-002-wowlance-2.0-platform-room.md) |
| **Передача команде** | **[docs/handoff/START.md](docs/handoff/START.md)** ← начать здесь |
| **Документация** | [docs/README.md](docs/README.md) |
| **Для ИИ / dev** | [AGENTS.md](AGENTS.md) |
| **Контракты** | [REGISTRY](contracts/REGISTRY.md) · [owners](docs/guides/contracts-owners.md) |
| **Схемы** | [diagrams/](docs/diagrams/) |
| **1.0 (reference)** | [EvgenyEVS/WowLance](https://github.com/EvgenyEVS/WowLance) |

## Структура

```text
contracts/   OpenSpec — править раньше кода (папки по соседям)
backend/     FastAPI + PostgreSQL
frontend/    React (Vite + TypeScript)
docs/        handoff · canon · architecture · phases · …
scripts/     founder-demo.ps1
```

## Быстрый старт (Docker — рекомендовано)

```powershell
docker compose up --build -d
```

| Сервис | URL |
|--------|-----|
| UI | http://127.0.0.1:8088 |
| API / Swagger | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/health |
| Postgres | `127.0.0.1:5433` (user/pass/db: `wowlance`) |

Миграции Alembic выполняются при старте контейнера `api`.  
Подробно: [docs/handoff/03-getting-started.md](docs/handoff/03-getting-started.md).

**Demo** (API на :8000): `powershell -File scripts/founder-demo.ps1` — [чеклист](docs/demo/founder-demo.md)

### Локально без Docker (dev)

```powershell
docker compose up -d db

cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy ..\.env.example .env
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000

cd ..\frontend
npm install
npm run dev
```

- C1 handoff: [backend/README.md](backend/README.md)  
- UI: [frontend/README.md](frontend/README.md)  
- **Stub hardening:** [docs/guides/hardening-stub.md](docs/guides/hardening-stub.md)  
- **Auth:** по умолчанию `AUTH_DISABLED=true` (local). Строгий режим — см. backend README (C8).

## Политика оплаты

Комната может создаться по handoff **до** оплаты; **staffing** — только после entitlement (Order / Payment).

## Фазы

Задания: [docs/phases/assignments/](docs/phases/assignments/).  
QA: [docs/phases/qa/](docs/phases/qa/).  
Статус / бэклог: [docs/handoff/08-status-and-backlog.md](docs/handoff/08-status-and-backlog.md).

| Фаза | Содержание |
|------|------------|
| **C0–C1** | Контракты + FounderHandoff → комната + snapshot |
| **C2** | Entitlement → `staffing_unlocked` |
| **C3** | GET room + React shell |
| **C4** | Staffing slots — [задание](docs/phases/assignments/261015%20-%20задание%20C4%20Staffing%20slots.md) |
| **C5** | StrategyPublished Accept/Reject — [задание](docs/phases/assignments/261015%20-%20задание%20C5%20Strategy%20accept.md) |
| **C6** | Roster + assign — [задание](docs/phases/assignments/261015%20-%20задание%20C6%20Roster%20assign.md) |
| **C7** | Room tasks — [задание](docs/phases/assignments/261015%20-%20задание%20C7%20Room%20tasks.md) |
| **C8** | Keycloak JWT — [задание](docs/phases/assignments/261016%20-%20задание%20C8%20Keycloak%20JWT.md) ∥ C9 |
| **C9** | Hot → CRM stub — [задание](docs/phases/assignments/261016%20-%20задание%20C9%20Hot%20lead%20CRM.md) |
| **C10** | Quality Gate — [задание](docs/phases/assignments/261017%20-%20задание%20C10%20Quality%20Gate.md) |
| **C11** | Outbox RoomCreated — [задание](docs/phases/assignments/261017%20-%20задание%20C11%20RoomCreated%20outbox.md) |
| **C12** | Slot unassign — [задание](docs/phases/assignments/261017%20-%20задание%20C12%20Slot%20unassign.md) |
| **C13** | Room health — [задание](docs/phases/assignments/261017%20-%20задание%20C13%20Room%20health.md) |
| **C14** | Meet / Jitsi stub — [задание](docs/phases/assignments/261017%20-%20задание%20C14%20Meet%20Jitsi%20stub.md) |
| **C15** | Task roster assignee — [задание](docs/phases/assignments/261017%20-%20задание%20C15%20Task%20roster%20assignee.md) |
| **C16** | Earnings stub — [задание](docs/phases/assignments/261017%20-%20задание%20C16%20Earnings%20stub.md) |
| **C17** | MemberTerminated — [задание](docs/phases/assignments/261017%20-%20задание%20C17%20Member%20terminated.md) |
| **C18** | StaffingUnlocked outbox — [задание](docs/phases/assignments/261019%20-%20задание%20C18%20StaffingUnlocked%20outbox.md) |
| **C19** | CRM deal-status — [задание](docs/phases/assignments/261019%20-%20задание%20C19%20CRM%20deal%20status.md) |
| **C20** | Room chat — [задание](docs/phases/assignments/261019%20-%20задание%20C20%20Room%20chat.md) |
| **C21** | Internal service-token — [задание](docs/phases/assignments/261019%20-%20задание%20C21%20Internal%20service%20token.md) |
| **C22** | Slot rematerialize — [задание](docs/phases/assignments/261021%20-%20задание%20C22%20Slot%20rematerialize.md) |
| **C23** | Matching lite — [задание](docs/phases/assignments/261021%20-%20задание%20C23%20Matching%20lite.md) |
| **C24** | TaskAccepted outbox — [задание](docs/phases/assignments/261021%20-%20задание%20C24%20TaskAccepted%20outbox.md) |
| **C25** | Health earnings — [задание](docs/phases/assignments/261021%20-%20задание%20C25%20Health%20earnings.md) |
| **C26** | Founder-demo — [задание](docs/phases/assignments/261022%20-%20задание%20C26%20Founder%20demo%20pack.md) |
| **C27** | Room RBAC lite — [задание](docs/phases/assignments/261022%20-%20задание%20C27%20Room%20RBAC.md) |
| **C28** | QA C0–C25 — [задание](docs/phases/assignments/261022%20-%20задание%20C28%20QA%20C0-C25.md) |
| **C29** | Room UX polish — [задание](docs/phases/assignments/261022%20-%20задание%20C29%20Room%20UX%20polish.md) |
| **C30** | Tasks + QG UX — [задание](docs/phases/assignments/261022%20-%20задание%20C30%20Tasks%20QG%20UX.md) |
| **C31** | Slots UX — [задание](docs/phases/assignments/261022%20-%20задание%20C31%20Slots%20staffing%20UX.md) |
| **C32** | Stub hardening — [задание](docs/phases/assignments/261022%20-%20задание%20C32%20Stub%20hardening.md) |
| **C33** | Contract owners — [задание](docs/phases/assignments/261022%20-%20задание%20C33%20Contract%20owners.md) |
| **C34** | Leads UX — [задание](docs/phases/assignments/261023%20-%20задание%20C34%20Leads%20UX.md) |
| **C35** | Chat / Meet UX — [задание](docs/phases/assignments/261023%20-%20задание%20C35%20Chat%20Meet%20UX.md) |
| **C36** | Earnings / Health UX — [задание](docs/phases/assignments/261023%20-%20задание%20C36%20Earnings%20Health%20UX.md) |
| **C37** | QA C0–C33 — [задание](docs/phases/assignments/261023%20-%20задание%20C37%20QA%20C0-C33.md) |
| **C38** | QA C0–C37 — [задание](docs/phases/assignments/261025%20-%20задание%20C38%20QA%20C0-C37.md) |
| **C39** | UI tokens / shell — [задание](docs/phases/assignments/261026%20-%20задание%20C39%20UI%20tokens%20shell.md) |
| **C40** | UI room chrome — [задание](docs/phases/assignments/261026%20-%20задание%20C40%20UI%20room%20chrome.md) |
| **C41** | UI panels — [задание](docs/phases/assignments/261026%20-%20задание%20C41%20UI%20panels.md) |
| **C42** | UI visual QA — [задание](docs/phases/assignments/261026%20-%20задание%20C42%20UI%20visual%20QA.md) |
| **Далее** | Live adapters / Gateway — **только после `agreed`** контрактов с соседями |
