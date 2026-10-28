# Архитектура (кратко для команды)

Подробнее: [architecture/](../architecture/) · [ADR-002](../canon/ADR-002-wowlance-2.0-platform-room.md).

---

## Стек

| Слой | Технология |
|------|------------|
| API | FastAPI (`backend/`) |
| UI | React + Vite + TypeScript (`frontend/`) |
| БД | PostgreSQL 16 (Docker, host port **5433**) |
| Миграции | Alembic |
| Контракты | OpenSpec YAML в `contracts/` |
| Auth (цель) | Keycloak JWT + shadow User |
| Internal | `X-Service-Token` на `/internal/v1/*` |
| События | Таблица `outbox_messages` (stub `sent`; live broker later) |

---

## Контуры HTTP

| Префикс | Кто вызывает | Auth (prod-цель) |
|---------|--------------|------------------|
| `/api/v1/*` | UI / клиенты | Bearer JWT (Keycloak) |
| `/internal/v1/*` | Соседние сервисы | Service-token (C21) |
| `/health` | Пробы | Открыт |
| `/auth/stub-token` | Только local stub | Dev |

Снаружи в платформе — **API Gateway** (один HTTPS). Внутри — свой порт сервиса (локально `:8000`).

---

## Три канала обмена

| Канал | Пример |
|-------|--------|
| **A. Sync API** | `POST /internal/v1/handoffs`, `POST /internal/v1/entitlements` |
| **B. События (outbox)** | `RoomCreated`, `HotLeadToCrm`, `TaskAccepted`, `RoomHealthSnapshot` |
| **C. Ссылки** | Meet URL, deeplink в CRM, URI документов |

---

## Ключевые доменные модули (`backend/app/`)

| Путь | Зона |
|------|------|
| `domain/handoff.py` | FounderHandoff + RoomCreated |
| `domain/entitlement.py` | Unlock + StaffingUnlocked |
| `domain/staffing.py` | Слоты, rematerialize |
| `domain/matching.py` | Matching lite |
| `domain/tasks.py` | Задачи, QG, TaskAccepted |
| `domain/leads.py` | Лиды, Hot, deal-status |
| `domain/room_health.py` | Health + earnings блок |
| `domain/schemas.py` | Pydantic = зеркало контрактов |
| `adapters/` | crm_stub, meet_stub |
| `auth/` | JWT, shadow user, deps |
| `api/` | Роутеры FastAPI |

Frontend: `frontend/src/` — room page + панели (slots, tasks, leads, chat, health…).

---

## Модель данных (Hybrid C)

- Первый handoff = snapshot **A** (полная копия стратегии в БД WL).  
- Позже StrategyPublished → pending → Accept/Reject тимлида.  
- Live-only без снимка (**B**) — не default.

См. [04-concept-C-hybrid](../architecture/04-concept-C-hybrid.md).
