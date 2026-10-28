# Карта репозитория

```text
WowLance-2.0/
├── README.md                 ← обзор + быстрый старт + таблица фаз
├── AGENTS.md                 ← правила для ИИ и разработчиков
├── docker-compose.yml        ← PostgreSQL :5433
├── .env.example
├── contracts/                ← OpenSpec (править РАНЬШЕ кода)
│   ├── REGISTRY.md
│   ├── strategy/             ← Стратегия (US Closer)
│   ├── order/ talent/ crm/ keycloak/ platform/ meet/
│   └── wowlance/             ← внутренний API комнаты
├── backend/                  ← FastAPI
│   ├── app/api/ domain/ auth/ adapters/ db/
│   ├── alembic/
│   ├── tests/
│   └── README.md
├── frontend/                 ← React (Vite)
│   ├── src/
│   └── README.md
├── scripts/                  ← founder-demo.ps1, render_*.py
└── docs/                     ← документация (этот пакет)
    ├── handoff/              ← ПЕРЕДАЧА КОМАНДЕ ← вы здесь
    ├── canon/                ← ADR-002
    ├── architecture/
    ├── diagrams/
    ├── guides/
    ├── status/
    ├── phases/assignments|qa/
    ├── demo/
    └── ui-parity/
```

---

## Где менять что

| Задача | Куда идти |
|--------|-----------|
| Новый граничный контракт | `contracts/<сосед>/` + REGISTRY + example |
| Домен / API | `backend/app/domain`, `backend/app/api` |
| Миграция БД | `backend/alembic/versions` |
| Stub соседа | `backend/app/adapters/` |
| UI комнаты | `frontend/src/` |
| Demo-скрипт | `scripts/founder-demo.ps1` |
| Задание среза | `docs/phases/assignments/` |

---

## Связь с Django 1.0

| Репозиторий | Роль |
|-------------|------|
| [WowLance](https://github.com/EvgenyEVS/WowLance) | Reference смыслов (RBAC, QG, Hot) — **не** копировать стек |
| `WowLance-2.0` | Рабочий код комнаты FastAPI/React |

Локально 1.0 часто лежит рядом: `...\WowLance` — не путать с `WowLance-2.0`.
