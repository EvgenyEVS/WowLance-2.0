# Запуск локально

Подробности API: [backend/README.md](../../backend/README.md).  
UI: [frontend/README.md](../../frontend/README.md).  
Demo: [demo/founder-demo.md](../demo/founder-demo.md).

---

## Требования

- Docker Desktop (PostgreSQL)  
- Python 3.11+ (проект гонялся и на 3.13)  
- Node.js 20+ (для frontend)  
- Git  

---

## 1. База

```powershell
cd <repo>
docker compose up -d db
# host: 127.0.0.1:5433  user/pass/db: wowlance
# также создаётся БД wowlance_test (для pytest)
```

## 2. Backend

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

## 3. Frontend

```powershell
cd frontend
npm install
npm run dev
# обычно http://127.0.0.1:5173
```

## 4. Founder demo (золотой путь)

При запущенном API:

```powershell
powershell -File scripts\founder-demo.ps1
```

Скрипт: handoff → entitlement → roster/assign → task QG → hot lead → health.  
Чеклист: [demo/founder-demo.md](../demo/founder-demo.md).

## 5. Тесты

```powershell
cd backend
.\.venv\Scripts\pytest -q
```

Нужна БД `wowlance_test` на том же Postgres (создаётся init-скриптом Docker).

---

## Важные env (`.env.example`)

| Переменная | Dev-default | Prod-цель |
|------------|-------------|-----------|
| `AUTH_DISABLED` | `true` | `false` + Keycloak |
| `INTERNAL_AUTH_DISABLED` | `true` | `false` + token |
| `ROOM_RBAC_DISABLED` | `true` | `false` |
| `DATABASE_URL` | `…@127.0.0.1:5433/wowlance` | свой |

Подробнее hardening: [guides/hardening-stub.md](../guides/hardening-stub.md).
