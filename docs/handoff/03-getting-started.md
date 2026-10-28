# Запуск локально

Подробности API: [backend/README.md](../../backend/README.md).  
UI: [frontend/README.md](../../frontend/README.md).  
Demo: [demo/founder-demo.md](../demo/founder-demo.md).

---

## Способ A — весь стек в Docker (рекомендуется принимающей команде)

**Требование:** Docker Desktop.

```powershell
cd <repo>
docker compose up --build -d
```

| Сервис | Порт / URL |
|--------|------------|
| **web** (React + nginx) | http://127.0.0.1:8088 |
| **api** (FastAPI) | http://127.0.0.1:8000 · Swagger `/docs` |
| **db** (PostgreSQL 16) | `127.0.0.1:5433` · user/pass/db `wowlance` |

Nginx на `web` проксирует `/api`, `/internal`, `/health`, `/auth`, `/docs` на `api`.  
При старте `api` сам делает `alembic upgrade head`.

Проверка:

```powershell
curl http://127.0.0.1:8000/health
# открыть http://127.0.0.1:8088
```

Остановка:

```powershell
docker compose down
# с данными БД: docker compose down -v
```

Логи:

```powershell
docker compose logs -f api
docker compose logs -f web
```

---

## Способ B — гибрид (только БД в Docker)

**Требования:** Docker Desktop · Python 3.11+ · Node.js 20+ · Git

### 1. База

```powershell
cd <repo>
docker compose up -d db
# host: 127.0.0.1:5433  user/pass/db: wowlance
# также создаётся БД wowlance_test (для pytest)
```

### 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy ..\.env.example .env
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Проверка: http://127.0.0.1:8000/health → `{"status":"ok",...}`  
Swagger: http://127.0.0.1:8000/docs

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
# обычно http://127.0.0.1:5173
```

---

## Founder demo (золотой путь)

При запущенном API на :8000:

```powershell
powershell -File scripts\founder-demo.ps1
```

Скрипт: handoff → entitlement → roster/assign → task QG → hot lead → health.  
Чеклист: [demo/founder-demo.md](../demo/founder-demo.md).

---

## Тесты

```powershell
cd backend
.\.venv\Scripts\pytest -q
```

Нужна БД `wowlance_test` на том же Postgres (создаётся init-скриптом Docker).  
При полном Docker-стеке БД уже на `:5433` — pytest с хоста использует `.env` / `.env.example`.

---

## Важные env (`.env.example` / compose)

| Переменная | Dev-default | Prod-цель |
|------------|-------------|-----------|
| `AUTH_DISABLED` | `true` | `false` + Keycloak |
| `INTERNAL_AUTH_DISABLED` | `true` | `false` + token |
| `ROOM_RBAC_DISABLED` | `true` | `false` |
| `DATABASE_URL` | host `127.0.0.1:5433` / в compose — `db:5432` | свой |

В `docker-compose.yml` для `api` уже заданы безопасные для локального демо значения.  
Подробнее hardening: [guides/hardening-stub.md](../guides/hardening-stub.md).
